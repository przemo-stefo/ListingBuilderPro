# backend/services/scraper/aliexpress_html_parser.py
# Purpose: Parse product data from rendered AliExpress HTML (runParams, og: tags, JSON-LD)
# NOT for: HTTP requests, API calls, or Scrape.do integration

import json
import re
from typing import TYPE_CHECKING

from services.scraper.html_parser_common import parse_json_ld_blocks

if TYPE_CHECKING:
    from services.scraper.aliexpress_scraper import AliExpressProduct


def parse_aliexpress_html(html: str, product: "AliExpressProduct") -> None:
    """Extract product data from rendered AliExpress HTML.

    WHY 3 strategies: runParams is the richest source (structured JSON embedded
    in page), og: tags are reliable fallback, JSON-LD is last resort.
    """
    _parse_run_params(html, product)
    _parse_og_and_title(html, product)
    parse_json_ld_blocks(html, product)


def _parse_run_params(html: str, product: "AliExpressProduct") -> None:
    """PRIMARY parser — extract window.runParams JSON embedded in <script> tag.

    WHY: AliExpress embeds full product data as `window.runParams = {...}` in
    the initial HTML. This is the most complete and structured data source.
    """
    match = re.search(r'window\.runParams\s*=\s*(\{.+?\});\s*\n', html, re.DOTALL)
    if not match:
        return

    try:
        run_params = json.loads(match.group(1))
    except (json.JSONDecodeError, TypeError):
        return

    data = run_params.get("data", run_params)

    # Title
    title_module = data.get("titleModule", {})
    if title_module.get("subject") and not product.title:
        product.title = title_module["subject"]

    # Price
    price_module = data.get("priceModule", {})
    if not product.price:
        for key in ("minPrice", "formatedPrice", "minActivityAmount"):
            val = price_module.get(key)
            if val:
                product.price = str(val).replace("US $", "").replace("$", "").strip()
                break
    if price_module.get("currencyCode"):
        product.currency = price_module["currencyCode"]

    # Images
    image_module = data.get("imageModule", {})
    if not product.images:
        img_list = image_module.get("imagePathList", [])
        if img_list:
            product.images = img_list

    # Specifications → parameters
    specs_module = data.get("specsModule", {})
    if not product.parameters:
        props = specs_module.get("props", [])
        for prop in props:
            name = prop.get("attrName", "")
            value = prop.get("attrValue", "")
            if name and value:
                product.parameters[name] = value

    # Brand / Seller
    store_module = data.get("storeModule", {})
    if not product.brand and store_module.get("storeName"):
        product.brand = store_module["storeName"]

    # Category from breadcrumbs
    cross_link = data.get("crossLinkModule", {})
    if not product.category:
        breadcrumbs = cross_link.get("breadCrumbPathList", [])
        names = [b.get("name", "") for b in breadcrumbs if b.get("name")]
        if names:
            product.category = " > ".join(names)


def _parse_og_and_title(html: str, product: "AliExpressProduct") -> None:
    """Fallback: extract title and image from OpenGraph meta tags."""
    if not product.title:
        og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        if og_title:
            raw = og_title.group(1).strip()
            # WHY: Remove price suffix like "- US $12.34" from og:title
            raw = re.sub(r'\s*[-|]\s*US?\s*\$[\d.,]+.*$', '', raw).strip()
            product.title = raw

    if not product.title:
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            raw = title_match.group(1).strip()
            for sep in [" - AliExpress", " | AliExpress", " -  "]:
                if sep in raw:
                    raw = raw.split(sep)[0].strip()
                    break
            product.title = raw

    if not product.images:
        og_images = re.findall(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if og_images:
            product.images = og_images
