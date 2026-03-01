# backend/services/scraper/temu_html_parser.py
# Purpose: Parse product data from rendered Temu HTML (og: tags, JSON-LD, embedded JSON)
# NOT for: HTTP requests, API calls, or Scrape.do integration

import json
import re
from typing import TYPE_CHECKING

from services.scraper.html_parser_common import parse_json_ld_blocks

if TYPE_CHECKING:
    from services.scraper.temu_scraper import TemuProduct


def parse_temu_html(html: str, product: "TemuProduct") -> None:
    """Extract product data from rendered Temu HTML.

    WHY multiple strategies: Temu obfuscates CSS classes (change every deploy),
    so we rely on og: tags, JSON-LD, and any embedded JSON we can find.
    """
    _parse_og_and_title(html, product)
    parse_json_ld_blocks(html, product)
    _parse_temu_json(html, product)


def _parse_og_and_title(html: str, product: "TemuProduct") -> None:
    """Extract title, image, description from OpenGraph meta tags."""
    if not product.title:
        og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        if og_title:
            raw = og_title.group(1).strip()
            # WHY: Remove "| Temu" suffix from og:title
            raw = re.sub(r'\s*[|]\s*Temu\s*$', '', raw).strip()
            product.title = raw

    if not product.title:
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            raw = title_match.group(1).strip()
            for sep in [" | Temu", " - Temu"]:
                if sep in raw:
                    raw = raw.split(sep)[0].strip()
                    break
            product.title = raw

    if not product.description:
        og_desc = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)
        if og_desc:
            product.description = og_desc.group(1).strip()

    if not product.images:
        og_images = re.findall(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if og_images:
            product.images = og_images


def _parse_temu_json(html: str, product: "TemuProduct") -> None:
    """Try to extract data from Temu's embedded JSON state.

    WHY: Temu sometimes embeds __INITIAL_STATE__ or rawData JSON in <script> tags.
    This is unreliable (changes between deploys) but worth trying as last resort.
    """
    for pattern in [
        r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});\s*\n',
        r'window\.__rawData\s*=\s*(\{.+?\});\s*\n',
    ]:
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            continue
        try:
            data = json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            continue

        # WHY: Structure varies — try common paths defensively
        goods = data.get("goods", data.get("store", {}).get("goods", {}))
        if isinstance(goods, dict):
            if not product.title and goods.get("goodsName"):
                product.title = goods["goodsName"]
            if not product.price and goods.get("minPrice"):
                product.price = str(goods["minPrice"])
            if not product.images and goods.get("hdThumbUrl"):
                product.images = [goods["hdThumbUrl"]]
