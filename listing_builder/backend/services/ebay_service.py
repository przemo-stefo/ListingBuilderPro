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
    """Fetch eBay product data by item ID using Scrape.do.

    WHY Scrape.do not eBay API: eBay Browse API requires a developer account
    and OAuth setup. Scrape.do is already configured for Allegro and works
    for any site. Public product pages have all the data we need.
    """
    token = os.environ.get("SCRAPE_DO_TOKEN", "")
    if not token:
        try:
            from config import settings
            token = settings.scrape_do_token
        except Exception:
            pass

    if not token:
        return {"error": "SCRAPE_DO_TOKEN not configured"}

    url = f"https://www.ebay.com/itm/{item_id}"
    encoded_url = quote(url, safe="")
    api_url = f"https://api.scrape.do/?token={token}&url={encoded_url}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(api_url)

            if resp.status_code != 200:
                return {"error": f"Scrape.do returned HTTP {resp.status_code}"}

            html = resp.text
            return _parse_ebay_html(html, item_id)

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
