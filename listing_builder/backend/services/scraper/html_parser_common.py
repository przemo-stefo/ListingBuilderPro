# backend/services/scraper/html_parser_common.py
# Purpose: Shared HTML parsing utilities for JSON-LD, og: tags across all marketplace scrapers
# NOT for: Marketplace-specific parsing (runParams, embedded JSON, title suffix removal)

import json
import re
from typing import Protocol, List, Dict


class ScrapedProduct(Protocol):
    """WHY Protocol: All marketplace product dataclasses share these fields.
    Duck typing lets us reuse JSON-LD/og parsers without coupling to specific types.
    """
    title: str
    description: str
    price: str
    currency: str
    images: List[str]
    brand: str
    category: str


def parse_json_ld_blocks(html: str, product: ScrapedProduct) -> None:
    """Find and parse all JSON-LD blocks in HTML.

    WHY shared: JSON-LD Product/BreadcrumbList schemas are identical across
    AliExpress, Temu, Rozetka — no reason to duplicate the parsing logic.
    """
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
                parse_product_ld(ld, product)
            elif ld.get("@type") == "BreadcrumbList":
                parse_breadcrumb_ld(ld, product)
        except (json.JSONDecodeError, TypeError):
            continue


def parse_product_ld(ld: dict, product: ScrapedProduct) -> None:
    """Extract product fields from a JSON-LD Product object.

    WHY defensive (not product.X): JSON-LD is a fallback source — don't overwrite
    richer data already extracted from primary sources (runParams, og: tags).
    """
    if not product.title and ld.get("name"):
        product.title = ld["name"]

    if not product.description and ld.get("description"):
        product.description = ld["description"]

    if not product.brand and ld.get("brand"):
        brand = ld["brand"]
        if isinstance(brand, dict):
            product.brand = brand.get("name", "")
        elif isinstance(brand, str):
            product.brand = brand

    if not product.images and ld.get("image"):
        imgs = ld["image"]
        if isinstance(imgs, list) and imgs:
            product.images = imgs
        elif isinstance(imgs, str):
            product.images = [imgs]

    if not product.price:
        offers = ld.get("offers")
        if isinstance(offers, dict):
            apply_offer_price(offers, product)
        elif isinstance(offers, list) and offers:
            apply_offer_price(offers[0], product)


def apply_offer_price(offer: dict, product: ScrapedProduct) -> None:
    """Set price and currency from a JSON-LD Offer object."""
    if offer.get("price") and not product.price:
        product.price = str(offer["price"])
    if offer.get("priceCurrency"):
        product.currency = offer["priceCurrency"]


def parse_breadcrumb_ld(ld: dict, product: ScrapedProduct) -> None:
    """Extract category path from a JSON-LD BreadcrumbList."""
    if product.category:
        return
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
