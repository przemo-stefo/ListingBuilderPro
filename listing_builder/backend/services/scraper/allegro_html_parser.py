# backend/services/scraper/allegro_html_parser.py
# Purpose: Parse product data from Allegro static HTML (no browser needed)
# NOT for: HTTP requests, browser automation, or API calls (that's allegro_scraper.py)

import json
import re
from typing import Dict, List

import structlog

logger = structlog.get_logger()


def parse_html_product(html: str, product) -> None:
    """Parse product data from Allegro static HTML.

    WHY not BeautifulSoup: avoid adding a dependency just for parsing.
    Allegro's static HTML embeds product data in:
    - <h1> for title
    - <title> tag for EAN (in parentheses)
    - <table> inside Parameters section for specs
    - <script> tags with JSON for price
    - <img> tags for product images
    """
    # ── Block detection ──
    html_lower = html.lower()
    if "zablokowany" in html_lower or ("enable js" in html_lower and len(html) < 2000):
        product.error = (
            "Allegro blocked this request even through Scrape.do. "
            "Try again later or contact support@scrape.do."
        )
        return

    _extract_title(html, product)
    _extract_ean_from_title(html, product)
    _extract_price(html, product)
    _extract_json_ld(html, product)
    _extract_images(html, product)
    _extract_parameters(html, product)
    _extract_ean_from_params(product)
    _extract_brand_manufacturer(product)
    _extract_description(html, product)
    _extract_condition(product)


def _extract_title(html: str, product) -> None:
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1_match:
        product.title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()


def _extract_ean_from_title(html: str, product) -> None:
    """WHY: Allegro puts EAN in parentheses in <title>, e.g. 'Product (5905525375211)'."""
    title_tag = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
    if title_tag:
        ean_in_title = re.search(r'\((\d{8,14})\)', title_tag.group(1))
        if ean_in_title:
            product.ean = ean_in_title.group(1)


def _extract_price(html: str, product) -> None:
    """WHY not meta tags: price meta tags are JS-rendered. We use embedded script JSON."""
    if not product.price:
        m = re.search(r'"price":"(\d+[\.,]\d+)","currency":"(\w+)"', html)
        if m:
            product.price = m.group(1)
            product.currency = m.group(2)

    if not product.price:
        m = re.search(r'"price":(\d+\.?\d*),"currency":"(\w+)"', html)
        if m:
            product.price = m.group(1)
            product.currency = m.group(2)

    if not product.price:
        m = re.search(r'"formattedPrice":"([\d,]+(?:\.\d+)?)\s*(?:zł|PLN)"', html)
        if m:
            product.price = m.group(1).replace(",", ".")


def _extract_json_ld(html: str, product) -> None:
    """Extract EAN and category from JSON-LD structured data."""
    json_ld_blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    for block in json_ld_blocks:
        try:
            ld = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(ld, dict):
            continue

        for key in ("gtin13", "gtin", "gtin8", "gtin12", "gtin14"):
            if ld.get(key) and not product.ean:
                product.ean = str(ld[key])

        if ld.get("@type") == "BreadcrumbList" and ld.get("itemListElement"):
            items = ld["itemListElement"]
            product.category = " > ".join(
                item.get("item", {}).get("name", "")
                for item in items
                if item.get("item", {}).get("name")
            )


def _extract_images(html: str, product) -> None:
    """WHY filter /original/: We want highest resolution. Skip UI icons."""
    _ICON_PATTERNS = ("action-", "icon-", "logo-", "badge-", "flag-")
    img_urls = set()
    for match in re.finditer(
        r'"(https?://a\.allegroimg\.com/original/[^"]+)"', html
    ):
        src = match.group(1)
        filename = src.rsplit("/", 1)[-1] if "/" in src else src
        if not any(filename.startswith(p) for p in _ICON_PATTERNS):
            img_urls.add(src)

    if not img_urls:
        for match in re.finditer(r'<img[^>]+src="([^"]*allegroimg[^"]*)"', html):
            src = match.group(1)
            filename = src.rsplit("/", 1)[-1] if "/" in src else src
            if not any(filename.startswith(p) for p in _ICON_PATTERNS):
                full_size = re.sub(r'/s\d+/', '/original/', src)
                img_urls.add(full_size)
    product.images = list(img_urls)


def _extract_parameters(html: str, product) -> None:
    """WHY table not li: Allegro static HTML uses <table> with <tr> rows."""
    params_section = re.search(
        r'data-box-name="Parameters"(.*?)(?:data-box-name=|</section)',
        html, re.DOTALL
    )
    if params_section:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', params_section.group(1), re.DOTALL)
        for row in rows:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(tds) >= 2:
                key = re.sub(r'<[^>]+>', '', tds[0]).strip()
                # WHY: Remove tooltip divs that pollute extracted values
                val_html = re.sub(
                    r'<div[^>]*role="tooltip"[^>]*>.*?</div>',
                    '', tds[1], flags=re.DOTALL
                )
                val = re.sub(r'<[^>]+>', '', val_html).strip()
                key = re.sub(r'\s+', ' ', key).strip()
                val = re.sub(r'\s+', ' ', val).strip()
                if key and val:
                    product.parameters[key] = val


def _extract_ean_from_params(product) -> None:
    if not product.ean:
        for key, val in product.parameters.items():
            if key.upper() in ("EAN", "GTIN", "EAN (GTIN)", "KOD EAN"):
                product.ean = val.strip()
                break


def _extract_brand_manufacturer(product) -> None:
    for param_key, param_val in product.parameters.items():
        if "marka" in param_key.lower() and not product.brand:
            product.brand = param_val
        if "producent" in param_key.lower() and not product.manufacturer:
            product.manufacturer = param_val


def _extract_description(html: str, product) -> None:
    """WHY multiple patterns: Allegro uses different HTML structures for descriptions."""
    # Pattern 1: data-box-name="Description" (most common in static HTML)
    desc_match = re.search(
        r'data-box-name="Description"[^>]*>(.*?)(?:data-box-name=|$)',
        html, re.DOTALL
    )
    if desc_match:
        raw = desc_match.group(1).strip()
        text_content = re.sub(r'<[^>]+>', '', raw).strip()
        if text_content:
            product.description = raw[:5000]

    # Pattern 2: __NEXT_DATA__ JSON (Allegro is Next.js)
    if not product.description:
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                props = next_data.get("props", {}).get("pageProps", {})
                offer = props.get("offer", {}) or props.get("offerDetails", {})
                desc_sections = offer.get("description", {}).get("sections", [])
                desc_parts = []
                for section in desc_sections:
                    for item in section.get("items", []):
                        if item.get("type") == "TEXT":
                            desc_parts.append(item.get("content", ""))
                        elif item.get("type") == "COLUMN":
                            for sub in item.get("items", []):
                                if sub.get("type") == "TEXT":
                                    desc_parts.append(sub.get("content", ""))
                if desc_parts:
                    product.description = "\n".join(desc_parts)[:5000]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass


def _extract_condition(product) -> None:
    for key, val in product.parameters.items():
        if "Stan" in key:
            product.condition = val
            break
