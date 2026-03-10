# backend/services/scraper/bol_scraper.py
# Purpose: Scrape product data from BOL.com product pages via Scrape.do
# NOT for: BOL Retailer API (bol_api.py) or data conversion (converter/)

import json
import os
import random
import re
from typing import Dict, List, Optional
from urllib.parse import quote

import httpx
import structlog
from bs4 import BeautifulSoup

from services.scraper.allegro_scraper import AllegroProduct

logger = structlog.get_logger()

# WHY reuse AllegroProduct: Same dataclass shape works for all marketplaces.
# The converter pipeline expects AllegroProduct as input — no point duplicating.
BolProduct = AllegroProduct

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
]


def extract_bol_product_id(url: str) -> str:
    """Extract product ID from BOL.com URL.

    BOL URLs: https://www.bol.com/nl/nl/p/product-name/9300000123456789/
    """
    clean = url.split("?")[0].split("#")[0].rstrip("/")
    match = re.search(r'/(\d{10,16})/?$', clean)
    return match.group(1) if match else ""


def _get_scrape_do_token() -> str:
    """Get Scrape.do API token."""
    token = os.environ.get("SCRAPE_DO_TOKEN", "")
    if not token:
        try:
            from config import settings
            token = settings.scrape_do_token
        except Exception:
            pass
    return token


def _parse_json_ld(soup: BeautifulSoup) -> Optional[Dict]:
    """Extract Product schema from JSON-LD in <script> tags.

    WHY: BOL.com embeds structured data — most reliable source for
    title, price, EAN, images, brand, description.
    """
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                return data
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _parse_bol_html(html: str, url: str) -> BolProduct:
    """Parse BOL.com product page HTML into BolProduct.

    WHY JSON-LD first: Structured, reliable, no CSS selector breakage.
    Falls back to HTML parsing for fields not in JSON-LD.
    """
    soup = BeautifulSoup(html, "html.parser")
    product = BolProduct(source_url=url, currency="EUR")

    # Extract product ID from URL
    product.source_id = extract_bol_product_id(url)

    # Try JSON-LD first (most reliable)
    ld = _parse_json_ld(soup)
    if ld:
        product.title = ld.get("name", "")
        product.description = ld.get("description", "")

        # Images
        img = ld.get("image", [])
        if isinstance(img, str):
            product.images = [img]
        elif isinstance(img, list):
            product.images = [i if isinstance(i, str) else i.get("url", "") for i in img]

        # Brand
        brand = ld.get("brand", {})
        if isinstance(brand, dict):
            product.brand = brand.get("name", "")
        elif isinstance(brand, str):
            product.brand = brand

        # EAN / GTIN
        product.ean = ld.get("gtin13", "") or ld.get("gtin", "") or ld.get("sku", "")

        # Price
        offers = ld.get("offers", {})
        if isinstance(offers, dict):
            product.price = str(offers.get("price", ""))
        elif isinstance(offers, list) and offers:
            product.price = str(offers[0].get("price", ""))

    # Fallback: HTML title
    if not product.title:
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            product.title = title_tag.get_text(strip=True)

    # Specs/parameters from product specs section
    for spec_row in soup.select("[data-test='specifications'] tr, .specs__row, .product-specs tr"):
        cells = spec_row.find_all(["th", "td", "dt", "dd"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True)
            val = cells[1].get_text(strip=True)
            if key and val:
                product.parameters[key] = val

    # Extract category from breadcrumbs
    breadcrumbs = soup.select(".breadcrumbs a, nav[aria-label='breadcrumb'] a")
    if breadcrumbs:
        product.category = breadcrumbs[-1].get_text(strip=True)

    # Manufacturer from parameters
    for mfg_key in ("Fabrikant", "Manufacturer", "Merk", "Brand"):
        if mfg_key in product.parameters:
            product.manufacturer = product.parameters[mfg_key]
            break

    if not product.title:
        product.error = "Nie udało się sparsować strony BOL.com"

    return product


async def scrape_bol_product(url: str) -> BolProduct:
    """Scrape a single BOL.com product page via Scrape.do.

    WHY Scrape.do: BOL.com blocks direct requests. Scrape.do handles
    anti-bot, cookies, JS rendering. Same service as Allegro scraper.
    """
    token = _get_scrape_do_token()
    if not token:
        return BolProduct(source_url=url, error="SCRAPE_DO_TOKEN not configured")

    encoded_url = quote(url, safe="")
    scrape_url = f"https://api.scrape.do?token={token}&url={encoded_url}&render=false"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                scrape_url,
                headers={"User-Agent": random.choice(_USER_AGENTS)},
            )

        if resp.status_code != 200:
            logger.warning("bol_scrape_failed", url=url[:80], status=resp.status_code)
            return BolProduct(source_url=url, error=f"Scrape.do HTTP {resp.status_code}")

        product = _parse_bol_html(resp.text, url)
        if not product.error:
            logger.info("bol_scrape_ok", url=url[:60], title=(product.title or "")[:50])
        return product

    except httpx.TimeoutException:
        return BolProduct(source_url=url, error="Timeout — BOL.com nie odpowiedział")
    except Exception as e:
        logger.error("bol_scrape_error", url=url[:80], error=str(e))
        return BolProduct(source_url=url, error=f"Scrape error: {str(e)}")


async def scrape_bol_batch(urls: List[str], delay: float = 3.0) -> List[BolProduct]:
    """Scrape multiple BOL.com products with delay between requests.

    WHY sequential: Scrape.do has concurrency limits per token.
    Delay prevents rate limiting and token exhaustion.
    """
    results: List[BolProduct] = []
    for i, url in enumerate(urls):
        product = await scrape_bol_product(url)
        results.append(product)
        if i < len(urls) - 1:
            import asyncio
            await asyncio.sleep(random.uniform(delay * 0.8, delay * 1.2))
    return results
