# backend/services/validator_data_sources.py
# Purpose: Parallel data fetching from Google Trends, Allegro, Amazon for product validation
# NOT for: LLM analysis (that's validator_service.py) or model definitions

from __future__ import annotations

import asyncio
import re
from typing import Dict

import httpx
import structlog

from config import settings

logger = structlog.get_logger()

# WHY: Reuse httpx client across calls — avoids TLS handshake per request
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
    return _client


async def fetch_google_trends(product_name: str, geo: str = "PL") -> Dict:
    """Fetch Google Trends interest data via pytrends (sync, wrapped in to_thread).

    WHY: pytrends is synchronous — to_thread avoids blocking the event loop.
    Retry 2x with 3s backoff because Google rate-limits aggressively.
    """
    def _sync_fetch() -> Dict:
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="pl-PL", tz=60)
            pytrends.build_payload([product_name[:100]], cat=0, timeframe="today 3-m", geo=geo)

            interest = pytrends.interest_over_time()
            if interest.empty:
                return {"available": True, "trend": "brak danych", "avg_interest": 0}

            col = product_name[:100]
            avg = int(interest[col].mean()) if col in interest.columns else 0
            recent = int(interest[col].iloc[-1]) if col in interest.columns else 0

            trend = "rosnący" if recent > avg else "malejący" if recent < avg * 0.7 else "stabilny"
            return {"available": True, "trend": trend, "avg_interest": avg, "recent_interest": recent}
        except Exception as e:
            logger.warning("google_trends_failed", error=str(e))
            return {"available": False, "error": str(e)}

    # WHY: 2 retries with 3s backoff — Google blocks aggressive requests
    for attempt in range(2):
        result = await asyncio.to_thread(_sync_fetch)
        if result.get("available"):
            return result
        if attempt < 1:
            await asyncio.sleep(3)

    return result


async def fetch_allegro_competition(product_name: str) -> Dict:
    """Scrape Allegro search results for competition data.

    WHY: Uses Scrape.do proxy to bypass anti-bot — same pattern as scraper/__init__.py
    """
    scrape_do_token = getattr(settings, "scrape_do_token", "") or ""
    if not scrape_do_token:
        return {"available": False, "error": "Scrape.do token not configured"}

    try:
        client = _get_client()
        query = product_name[:80].replace(" ", "+")
        target_url = f"https://allegro.pl/listing?string={query}"
        url = f"https://api.scrape.do?token={scrape_do_token}&url={target_url}"

        resp = await client.get(url)
        if resp.status_code != 200:
            return {"available": False, "error": f"HTTP {resp.status_code}"}

        html = resp.text

        # WHY: Regex parsing — lightweight, no lxml dependency
        total_match = re.search(r'(\d[\d\s]*)\s*(?:ofert|wynik)', html)
        total_results = int(total_match.group(1).replace(" ", "")) if total_match else 0

        prices = [float(p.replace(",", ".").replace(" ", ""))
                  for p in re.findall(r'(\d+[,\.]\d{2})\s*zł', html)]

        return {
            "available": True,
            "marketplace": "allegro",
            "total_results": total_results,
            "avg_price_pln": round(sum(prices) / len(prices), 2) if prices else 0,
            "price_range": {"min": min(prices), "max": max(prices)} if prices else None,
            "sample_count": len(prices),
        }
    except Exception as e:
        logger.warning("allegro_scrape_failed", error=str(e))
        return {"available": False, "error": str(e)}


async def fetch_amazon_competition(product_name: str, marketplace: str = "DE") -> Dict:
    """Scrape Amazon search results for competition data.

    WHY: Uses Scrape.do proxy — same pattern as Allegro above.
    """
    scrape_do_token = getattr(settings, "scrape_do_token", "") or ""
    if not scrape_do_token:
        return {"available": False, "error": "Scrape.do token not configured"}

    tld_map = {"DE": "de", "US": "com", "UK": "co.uk", "FR": "fr", "IT": "it", "ES": "es", "PL": "pl"}
    tld = tld_map.get(marketplace.upper(), "de")

    try:
        client = _get_client()
        query = product_name[:80].replace(" ", "+")
        target_url = f"https://www.amazon.{tld}/s?k={query}"
        url = f"https://api.scrape.do?token={scrape_do_token}&url={target_url}"

        resp = await client.get(url)
        if resp.status_code != 200:
            return {"available": False, "error": f"HTTP {resp.status_code}"}

        html = resp.text

        result_match = re.search(r'(\d[\d\s,\.]*)\s*(?:results?|Ergebnisse|wynik)', html)
        total_results = int(re.sub(r'[^\d]', '', result_match.group(1))) if result_match else 0

        prices = [float(p.replace(",", "."))
                  for p in re.findall(r'(\d+[,\.]\d{2})\s*€', html)]

        reviews = [int(r.replace(".", "").replace(",", ""))
                   for r in re.findall(r'([\d.,]+)\s*(?:Bewertung|rating|review|ocen)', html)]

        return {
            "available": True,
            "marketplace": f"amazon_{marketplace.lower()}",
            "total_results": total_results,
            "avg_price_eur": round(sum(prices) / len(prices), 2) if prices else 0,
            "price_range": {"min": min(prices), "max": max(prices)} if prices else None,
            "avg_reviews": round(sum(reviews) / len(reviews)) if reviews else 0,
            "sample_count": len(prices),
        }
    except Exception as e:
        logger.warning("amazon_scrape_failed", error=str(e))
        return {"available": False, "error": str(e)}
