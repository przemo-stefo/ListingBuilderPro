# backend/api/news_routes.py
# Purpose: News aggregation endpoint — fetches RSS, translates to Polish via Groq, caches
# NOT for: Compliance alerts or monitoring (those are separate systems)

import asyncio
import json
import re
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Query
import httpx
import structlog

from config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/api/news", tags=["news"])

# WHY: In-memory cache — single Render worker means dict is fine
_cache: Dict = {"articles": [], "timestamp": 0}
CACHE_TTL = 7200  # 2 hours

# WHY: Same feeds as frontend had — moved here for server-side fetch + translation
RSS_FEEDS = [
    {"url": "https://channelx.world/category/amazon/feed/", "source": "ChannelX Amazon", "category": "amazon"},
    {"url": "https://www.junglescout.com/blog/feed/", "source": "Jungle Scout", "category": "amazon"},
    {"url": "https://blog.allegro.tech/feed.xml", "source": "Allegro Tech Blog", "category": "allegro"},
    {"url": "https://news.google.com/rss/search?q=Allegro+marketplace+sprzedawcy&hl=pl&gl=PL&ceid=PL:pl", "source": "Allegro News", "category": "allegro"},
    {"url": "https://www.ebayinc.com/stories/news/rss/", "source": "eBay Inc.", "category": "ebay"},
    {"url": "https://channelx.world/category/ebay/feed/", "source": "ChannelX eBay", "category": "ebay"},
    {"url": "https://news.google.com/rss/search?q=Kaufland+Global+Marketplace+ecommerce&hl=en&gl=DE&ceid=DE:en", "source": "Kaufland News", "category": "kaufland"},
    {"url": "https://ecommercenews.eu/feed/", "source": "Ecommerce News EU", "category": "ecommerce"},
    {"url": "https://tamebay.com/feed", "source": "Tamebay", "category": "ecommerce"},
    {"url": "https://www.practicalecommerce.com/feed", "source": "Practical Ecommerce", "category": "ecommerce"},
    {"url": "https://sellerengine.com/feed/", "source": "SellerEngine", "category": "ecommerce"},
    {"url": "https://news.google.com/rss/search?q=Temu+marketplace+sellers+ecommerce&hl=en&gl=US&ceid=US:en", "source": "Temu News", "category": "temu"},
    {"url": "https://channelx.world/category/temu/feed/", "source": "ChannelX Temu", "category": "temu"},
    {"url": "https://news.google.com/rss/search?q=EU+GPSR+EPR+product+safety+ecommerce+compliance&hl=en&gl=DE&ceid=DE:en", "source": "EU Compliance", "category": "compliance"},
    {"url": "https://news.google.com/rss/search?q=Amazon+eBay+marketplace+compliance+regulation&hl=en&gl=US&ceid=US:en", "source": "Marketplace Compliance", "category": "compliance"},
]

RSS_API = "https://api.rss2json.com/v1/api.json?rss_url="
TRANSLATE_BATCH_SIZE = 15
MAX_TRANSLATE_RETRIES = 2


async def _fetch_feed(client: httpx.AsyncClient, feed: dict) -> List[dict]:
    """Fetch single RSS feed via rss2json.com API."""
    try:
        resp = await client.get(f"{RSS_API}{feed['url']}", timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if data.get("status") != "ok":
            return []

        items = []
        for item in data.get("items", [])[:6]:
            desc = item.get("description", "")
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
            thumb = (
                item.get("thumbnail")
                or (item.get("enclosure") or {}).get("link")
                or (img_match.group(1) if img_match else "")
            )
            items.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "source": feed["source"],
                "pubDate": item.get("pubDate", ""),
                "description": re.sub(r"<[^>]*>", "", desc)[:200],
                "category": feed["category"],
                "thumbnail": thumb,
            })
        return items
    except Exception:
        return []


async def _fetch_all_feeds() -> List[dict]:
    """Fetch all RSS feeds in parallel batches (3 at a time)."""
    articles: List[dict] = []
    async with httpx.AsyncClient() as client:
        for i in range(0, len(RSS_FEEDS), 3):
            batch = RSS_FEEDS[i : i + 3]
            results = await asyncio.gather(*[_fetch_feed(client, f) for f in batch])
            for r in results:
                articles.extend(r)
            if i + 3 < len(RSS_FEEDS):
                await asyncio.sleep(0.3)

    articles.sort(key=lambda a: a.get("pubDate", ""), reverse=True)
    return articles


async def _fetch_og_image(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch og:image from article URL — reads only first 50KB of HTML."""
    try:
        resp = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)", "Accept": "text/html"},
            follow_redirects=True,
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        # WHY: og:image is always in <head> — no need to read full page
        html = resp.text[:50_000]
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I
        )
        return match.group(1) if match else None
    except Exception:
        return None


async def _resolve_thumbnails(articles: List[dict]) -> None:
    """Fetch og:image for articles missing thumbnails — 5 at a time."""
    missing = [a for a in articles if not a.get("thumbnail")]
    if not missing:
        return

    async with httpx.AsyncClient() as client:
        for i in range(0, len(missing), 5):
            batch = missing[i : i + 5]
            results = await asyncio.gather(*[_fetch_og_image(client, a["link"]) for a in batch])
            for art, img in zip(batch, results):
                if img:
                    art["thumbnail"] = img
            if i + 5 < len(missing):
                await asyncio.sleep(0.2)

    resolved = sum(1 for a in missing if a.get("thumbnail"))
    logger.info("news_thumbnails_resolved", missing=len(missing), resolved=resolved)


async def _translate_batch(articles: List[dict], keys: List[str], batch_idx: int) -> List[dict]:
    """Translate a batch of articles to Polish via Groq — retries with different key on failure."""
    if not articles:
        return articles

    lines = []
    for i, art in enumerate(articles):
        lines.append(f'{i+1}. T: "{art["title"]}"')
        if art.get("description"):
            lines.append(f'   D: "{art["description"]}"')

    prompt = (
        "Przetłumacz tytuły (T) i opisy (D) artykułów e-commerce na język polski.\n"
        "Zachowaj nazwy własne (Amazon, Allegro, eBay, Kaufland, Temu, GPSR, EPR) bez zmian.\n"
        "Jeśli tekst jest już po polsku, zostaw go bez zmian.\n"
        "WAŻNE: Przetłumacz KAŻDY artykuł — nie pomijaj żadnego.\n"
        'Odpowiedz TYLKO jako JSON: {"items": [{"t": "tytuł PL", "d": "opis PL"}, ...]}\n\n'
        + "\n".join(lines)
    )

    # WHY: Retry with different Groq keys — 429 on one key doesn't mean all are exhausted
    for attempt in range(min(MAX_TRANSLATE_RETRIES, len(keys))):
        key = keys[(batch_idx + attempt) % len(keys)]
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )
                if resp.status_code == 429:
                    logger.warning("news_translate_429", batch=batch_idx, attempt=attempt)
                    await asyncio.sleep(2.0)
                    continue
                if resp.status_code != 200:
                    logger.warning("news_translate_failed", batch=batch_idx, status=resp.status_code)
                    continue

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                translated = json.loads(content)
                items = translated.get("items", [])

                translated_count = 0
                for i, art in enumerate(articles):
                    if i < len(items):
                        if items[i].get("t"):
                            art["title"] = items[i]["t"]
                            translated_count += 1
                        if items[i].get("d"):
                            art["description"] = items[i]["d"]

                logger.info("news_batch_translated", batch=batch_idx, count=translated_count)
                return articles

        except Exception as e:
            logger.error("news_translate_error", batch=batch_idx, attempt=attempt, error=str(e))
            if attempt < MAX_TRANSLATE_RETRIES - 1:
                await asyncio.sleep(1.0)

    logger.error("news_translate_all_retries_failed", batch=batch_idx)
    return articles


async def _translate_all(articles: List[dict]) -> List[dict]:
    """Translate articles sequentially, rotating Groq API keys per batch."""
    keys = settings.groq_api_keys
    if not keys:
        return articles

    batches = [
        articles[i : i + TRANSLATE_BATCH_SIZE]
        for i in range(0, len(articles), TRANSLATE_BATCH_SIZE)
    ]

    # WHY: Sequential + key rotation to avoid 429 rate limits on single key
    translated: List[dict] = []
    for idx, batch in enumerate(batches):
        result = await _translate_batch(batch, keys, idx)
        translated.extend(result)
        if idx < len(batches) - 1:
            await asyncio.sleep(1.0)

    logger.info("news_translated", total=len(translated), batches=len(batches))
    return translated


@router.get("/feed")
async def get_news_feed(force: bool = Query(False)):
    """Aggregated marketplace news feed — translated to Polish, cached 2h.

    WHY force param: allows cache bypass when translations failed or new deploy.
    """
    now = time.time()
    if not force and _cache["articles"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return {"articles": _cache["articles"], "cached": True}

    articles = await _fetch_all_feeds()
    await _resolve_thumbnails(articles)
    articles = await _translate_all(articles)

    _cache["articles"] = articles
    _cache["timestamp"] = now

    logger.info("news_feed_refreshed", total=len(articles))
    return {"articles": articles, "cached": False}
