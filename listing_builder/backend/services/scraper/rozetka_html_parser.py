# backend/services/scraper/rozetka_html_parser.py
# Purpose: Parse product data from rendered Rozetka HTML (og: tags, JSON-LD, <title>)
# NOT for: HTTP requests, API calls, or Scrape.do integration

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.scraper.rozetka_scraper import RozetkaProduct


def parse_rozetka_html(html: str, product: "RozetkaProduct") -> None:
    """Extract title, price, images, brand, category from rendered Rozetka HTML.

    WHY multiple strategies: Rozetka uses Nuxt SSR — data lives in og: tags,
    JSON-LD, and <title>. We try all sources and merge best data.
    """
    _parse_og_and_title(html, product)
    _parse_json_ld(html, product)


def _parse_og_and_title(html: str, product: "RozetkaProduct") -> None:
    """Extract title and images from OpenGraph meta tags and <title>."""
    # og:title — most reliable for product name
    og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if og_title:
        product.title = og_title.group(1).strip()

    # <title> tag fallback — format: "Назва - купити | Rozetka"
    if not product.title:
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            raw = title_match.group(1).strip()
            # WHY split: Remove " - купити..." or " – купити..." suffix
            for sep in [" - купити", " – купити", " | ROZETKA", " | Rozetka"]:
                if sep in raw:
                    raw = raw.split(sep)[0].strip()
                    break
            product.title = raw

    # og:image — main product image
    og_images = re.findall(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
    if og_images:
        product.images = og_images


def _parse_json_ld(html: str, product: "RozetkaProduct") -> None:
    """Extract price, brand, images, category from JSON-LD structured data."""
    ld_blocks = re.findall(
        r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    for block in ld_blocks:
        try:
            ld = json.loads(block)
            if not isinstance(ld, dict):
                continue
            if ld.get("@type") == "Product":
                _parse_product_ld(ld, product)
            elif ld.get("@type") == "BreadcrumbList":
                _parse_breadcrumb_ld(ld, product)
        except (json.JSONDecodeError, TypeError):
            continue


def _parse_product_ld(ld: dict, product: "RozetkaProduct") -> None:
    """Extract product fields from a JSON-LD Product object."""
    if not product.title and ld.get("name"):
        product.title = ld["name"]

    # Brand — can be string or {"name": "..."}
    if ld.get("brand"):
        brand = ld["brand"]
        if isinstance(brand, dict):
            product.brand = brand.get("name", "")
        elif isinstance(brand, str):
            product.brand = brand

    # Images — can be string or list
    if ld.get("image"):
        imgs = ld["image"]
        if isinstance(imgs, list) and imgs:
            product.images = imgs
        elif isinstance(imgs, str):
            product.images = [imgs]

    # Price from offers — can be dict or list
    offers = ld.get("offers")
    if isinstance(offers, dict):
        _apply_offer_price(offers, product)
    elif isinstance(offers, list) and offers:
        _apply_offer_price(offers[0], product)


def _apply_offer_price(offer: dict, product: "RozetkaProduct") -> None:
    """Set price and currency from a JSON-LD Offer object."""
    if offer.get("price"):
        product.price = str(offer["price"])
    if offer.get("priceCurrency"):
        product.currency = offer["priceCurrency"]


def _parse_breadcrumb_ld(ld: dict, product: "RozetkaProduct") -> None:
    """Extract category path from a JSON-LD BreadcrumbList."""
    items = ld.get("itemListElement", [])
    if not items:
        return
    names = [
        item.get("item", {}).get("name", "")
        if isinstance(item.get("item"), dict)
        else item.get("name", "")
        for item in items
    ]
    product.category = " > ".join(n for n in names if n)


def extract_title_from_description(description_html: str) -> str:
    """Tier 2 fallback: extract a rough title from API description HTML."""
    if not description_html:
        return ""
    # WHY: First <strong> or <b> in description is often the product name
    for pattern in [r'<strong>([^<]{5,80})</strong>', r'<b>([^<]{5,80})</b>']:
        match = re.search(pattern, description_html)
        if match:
            return match.group(1).strip()
    # WHY: First <p> with substantial text
    p_match = re.search(r'<p>([^<]{10,100})', description_html)
    if p_match:
        return p_match.group(1).strip()[:80]
    return ""
