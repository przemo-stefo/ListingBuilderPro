# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/ebay_service.py
# Purpose: Fetch public eBay product data via Scrape.do (no eBay dev account needed)
# NOT for: eBay seller APIs, order management, or listing creation

import os
import re
import json
from typing import Optional
from urllib.parse import quote
import httpx
import structlog

logger = structlog.get_logger()


async def fetch_ebay_product(item_id: str) -> Optional[dict]:
    """Fetch eBay product data by item ID.

    WHY direct httpx first: eBay doesn't use DataDome — simple GET with
    stealth UA works fine from any IP. Falls back to ScraperAPI/Scrape.do
    if direct request fails.
    """
    url = f"https://www.ebay.com/itm/{item_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)

            if resp.status_code == 200 and len(resp.text) > 5000:
                return _parse_ebay_html(resp.text, item_id)

            # Fallback: ScraperAPI
            scraperapi_key = os.environ.get("SCRAPERAPI_KEY", "")
            if scraperapi_key:
                encoded_url = quote(url, safe="")
                api_url = f"https://api.scraperapi.com?api_key={scraperapi_key}&url={encoded_url}"
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    return _parse_ebay_html(resp.text, item_id)

            # Fallback: Scrape.do
            token = os.environ.get("SCRAPE_DO_TOKEN", "")
            if token:
                encoded_url = quote(url, safe="")
                api_url = f"https://api.scrape.do/?token={token}&url={encoded_url}"
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    return _parse_ebay_html(resp.text, item_id)

            return {"error": f"All fetch strategies failed (HTTP {resp.status_code})"}

    except httpx.TimeoutException:
        return {"error": "eBay scrape timed out"}
    except Exception as e:
        return {"error": str(e)}


def _parse_ebay_html(html: str, item_id: str) -> dict:
    """Extract product data from eBay HTML."""
    data = {
        "item_id": item_id,
        "title": None,
        "price": None,
        "currency": None,
        "listing_active": True,
        "stock": None,
        "condition": None,
        "seller": None,
    }

    # Title
    m = re.search(r'<h1[^>]*class="[^"]*x-item-title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        data["title"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    if not data["title"]:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
        if m:
            title_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            # WHY split: eBay <title> includes " | eBay" suffix
            data["title"] = title_text.split(" | eBay")[0].strip()

    # Price from JSON-LD
    json_ld_blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    for block in json_ld_blocks:
        try:
            ld = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(ld, dict) and ld.get("@type") == "Product":
            offers = ld.get("offers", {})
            if isinstance(offers, dict):
                data["price"] = float(offers["price"]) if offers.get("price") else None
                data["currency"] = offers.get("priceCurrency")
            if isinstance(offers, list) and offers:
                data["price"] = float(offers[0]["price"]) if offers[0].get("price") else None
                data["currency"] = offers[0].get("priceCurrency")

    # Fallback price from meta tag
    if not data["price"]:
        m = re.search(r'"prcIsum[^"]*"[^>]*>([^<]+)', html)
        if m:
            price_text = re.sub(r'[^\d.,]', '', m.group(1))
            try:
                data["price"] = float(price_text.replace(",", ""))
            except ValueError:
                pass

    # Listing status — ended listings show "This listing has ended"
    if "This listing has ended" in html or "this listing was ended" in html.lower():
        data["listing_active"] = False

    # Condition
    m = re.search(r'"conditionText"[^>]*>([^<]+)', html)
    if m:
        data["condition"] = m.group(1).strip()

    # Seller
    m = re.search(r'"seller-link"[^>]*>(.*?)</a>', html, re.DOTALL)
    if m:
        data["seller"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    # Quantity available
    m = re.search(r'(\d+)\s*available', html, re.IGNORECASE)
    if m:
        data["stock"] = int(m.group(1))

    logger.info(
        "ebay_parsed",
        item_id=item_id,
        title=(data["title"] or "")[:60],
        price=data["price"],
        active=data["listing_active"],
    )
    return data
