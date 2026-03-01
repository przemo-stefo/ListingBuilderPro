# backend/services/scraper/rozetka_scraper.py
# Purpose: Scrape product data from Rozetka.com.ua via Scrape.do + open API
# NOT for: HTML parsing (rozetka_html_parser.py), API calls (rozetka_api.py)

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import quote

import httpx
import structlog

from services.scraper import get_scrape_do_token
from services.scraper.rozetka_api import fetch_rozetka_api
from services.scraper.rozetka_html_parser import parse_rozetka_html, extract_title_from_description

logger = structlog.get_logger()

# WHY: Ukrainian brand parameter names — used in Tier 1 and Tier 2 brand extraction
_BRAND_KEYS = ("Бренд", "Виробник", "Торгова марка")


@dataclass
class RozetkaProduct:
    """Scraped product data from a single Rozetka listing."""

    source_url: str = ""
    source_id: str = ""
    title: str = ""
    description: str = ""     # HTML from product-api
    price: str = ""
    currency: str = "UAH"
    images: List[str] = field(default_factory=list)
    category: str = ""
    brand: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_rozetka_id(url: str) -> str:
    """Extract numeric product ID from Rozetka URL.

    Patterns: /p453106049/ → 453106049, /p12345678 → 12345678
    """
    match = re.search(r'/p(\d+)', url)
    return match.group(1) if match else ""


def _extract_brand(parameters: Dict[str, str]) -> str:
    """Extract brand from Rozetka specs using known Ukrainian key names."""
    for key in _BRAND_KEYS:
        if key in parameters:
            return parameters[key]
    return ""


async def _scrape_via_scrape_do(url: str, token: str, product_id: str) -> RozetkaProduct:
    """Scrape Rozetka page via Scrape.do with render=true (bypasses Cloudflare).

    WHY render=true: Rozetka main site returns 403 without JS execution.
    WHY geoCode=ua: Rozetka geo-restricts some content to Ukraine.
    """
    product = RozetkaProduct(source_url=url, source_id=product_id)
    encoded_url = quote(url, safe="")
    api_url = (
        f"https://api.scrape.do/"
        f"?token={token}"
        f"&url={encoded_url}"
        f"&render=true"
        f"&geoCode=ua"
    )

    logger.info("rozetka_scrape_do_request", url=url, product_id=product_id)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.get(api_url)
            if resp.status_code != 200:
                try:
                    err_data = resp.json()
                    msg = err_data.get("Message", str(resp.status_code))
                    product.error = f"Scrape.do error: {msg if isinstance(msg, str) else '; '.join(msg)}"
                except Exception:
                    product.error = f"Scrape.do returned HTTP {resp.status_code}"
                logger.error("rozetka_scrape_do_failed", status=resp.status_code, product_id=product_id)
                return product
            parse_rozetka_html(resp.text, product)
    except httpx.TimeoutException:
        product.error = "Scrape.do timeout (90s) — Rozetka may be slow"
        logger.error("rozetka_scrape_do_timeout", url=url, product_id=product_id)
    except Exception as e:
        # SECURITY: httpx exceptions may contain api_url with Scrape.do token — sanitize
        error_msg = str(e).replace(token, "***") if token in str(e) else str(e)
        product.error = f"Scrape.do request failed: {error_msg}"
        logger.error("rozetka_scrape_do_error", url=url, product_id=product_id, error=error_msg)

    return product


def _merge_api_data(product: RozetkaProduct, api_data: dict) -> None:
    """Merge open API data (description + specs) into a Scrape.do-scraped product."""
    if api_data["description"]:
        product.description = api_data["description"]
    if api_data["parameters"]:
        product.parameters = api_data["parameters"]
    if not product.brand:
        product.brand = _extract_brand(product.parameters)


def _build_tier2_product(url: str, product_id: str, api_data: dict) -> RozetkaProduct:
    """Build a RozetkaProduct from API-only data (no Scrape.do)."""
    product = RozetkaProduct(
        source_url=url,
        source_id=product_id,
        description=api_data["description"],
        parameters=api_data["parameters"],
        brand=_extract_brand(api_data["parameters"]),
    )
    product.title = extract_title_from_description(api_data["description"])
    if not product.title:
        product.title = f"Produkt Rozetka {product_id}"
    if not api_data["description"] and not api_data["parameters"]:
        product.error = "Rozetka API nie zwrocilo danych dla tego produktu"
    return product


async def scrape_rozetka_product(url: str) -> RozetkaProduct:
    """Scrape product data from a Rozetka URL.

    2-tier: Scrape.do + API (full data) → API only (fallback, limited metadata).
    """
    # SECURITY: Validate URL domain
    from utils.url_validator import validate_marketplace_url
    try:
        validate_marketplace_url(url, "rozetka")
    except ValueError as e:
        return RozetkaProduct(source_url=url, error=f"Invalid URL: {e}")

    product_id = extract_rozetka_id(url)
    if not product_id:
        return RozetkaProduct(
            source_url=url,
            error="Nie udalo sie wyciagnac ID produktu z URL. Sprawdz link."
        )

    api_data = await fetch_rozetka_api(product_id)

    # Tier 1: Scrape.do (rendered HTML) → title, price, images, brand
    token = get_scrape_do_token()
    if token:
        product = await _scrape_via_scrape_do(url, token, product_id)
        if not product.error and product.title:
            _merge_api_data(product, api_data)
            logger.info("rozetka_tier1_success", product_id=product_id,
                        title=product.title[:60], price=product.price or "(none)")
            return product
        logger.warning("rozetka_tier1_failed", product_id=product_id,
                       error=product.error or "no title extracted")

    # Tier 2: Open API only — description + specs, limited metadata
    product = _build_tier2_product(url, product_id, api_data)
    if not product.error:
        logger.info("rozetka_tier2_success", product_id=product_id,
                    title=product.title[:60], params_count=len(product.parameters))
    return product
