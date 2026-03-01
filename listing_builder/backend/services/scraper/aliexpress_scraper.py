# backend/services/scraper/aliexpress_scraper.py
# Purpose: Scrape product data from AliExpress via Scrape.do (render=true)
# NOT for: HTML parsing (aliexpress_html_parser.py)

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import quote

import httpx
import structlog

from services.scraper import get_scrape_do_token
from services.scraper.aliexpress_html_parser import parse_aliexpress_html

logger = structlog.get_logger()


@dataclass
class AliExpressProduct:
    """Scraped product data from a single AliExpress listing."""

    source_url: str = ""
    source_id: str = ""
    title: str = ""
    description: str = ""
    price: str = ""
    currency: str = "USD"
    images: List[str] = field(default_factory=list)
    category: str = ""
    brand: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_aliexpress_id(url: str) -> str:
    """Extract numeric product ID from AliExpress URL.

    Patterns: /item/1005005184831712.html → 1005005184831712
    """
    match = re.search(r'/item/(\d+)\.html', url)
    return match.group(1) if match else ""


async def _scrape_via_scrape_do(url: str, token: str, product_id: str) -> AliExpressProduct:
    """Scrape AliExpress page via Scrape.do with render=true.

    WHY render=true: AliExpress uses Akamai Bot Manager — needs JS execution.
    WHY 25 credits/req: render=true costs 25x vs 1x for non-rendered.
    """
    product = AliExpressProduct(source_url=url, source_id=product_id)
    encoded_url = quote(url, safe="")
    api_url = (
        f"https://api.scrape.do/"
        f"?token={token}"
        f"&url={encoded_url}"
        f"&render=true"
    )

    logger.info("aliexpress_scrape_do_request", url=url, product_id=product_id)

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
                logger.error("aliexpress_scrape_do_failed", status=resp.status_code, product_id=product_id)
                return product
            parse_aliexpress_html(resp.text, product)
    except httpx.TimeoutException:
        product.error = "Scrape.do timeout (90s) — AliExpress may be slow"
        logger.error("aliexpress_scrape_do_timeout", url=url, product_id=product_id)
    except Exception as e:
        # SECURITY: httpx exceptions may contain api_url with Scrape.do token — sanitize
        error_msg = str(e).replace(token, "***") if token in str(e) else str(e)
        product.error = f"Scrape.do request failed: {error_msg}"
        logger.error("aliexpress_scrape_do_error", url=url, product_id=product_id, error=error_msg)

    return product


async def scrape_aliexpress_product(url: str) -> AliExpressProduct:
    """Scrape product data from an AliExpress URL.

    Single tier: Scrape.do with render=true (no open API available).
    """
    # SECURITY: Validate URL domain
    from utils.url_validator import validate_marketplace_url
    try:
        validate_marketplace_url(url, "aliexpress")
    except ValueError as e:
        return AliExpressProduct(source_url=url, error=f"Invalid URL: {e}")

    product_id = extract_aliexpress_id(url)
    if not product_id:
        return AliExpressProduct(
            source_url=url,
            error="Nie udalo sie wyciagnac ID produktu z URL. Sprawdz link."
        )

    token = get_scrape_do_token()
    if not token:
        return AliExpressProduct(
            source_url=url,
            source_id=product_id,
            error="Brak tokenu Scrape.do — skonfiguruj SCRAPE_DO_TOKEN"
        )

    product = await _scrape_via_scrape_do(url, token, product_id)

    # WHY: Scrape.do may return 200 with CAPTCHA page or empty HTML — detect and report
    if not product.error and not product.title:
        product.error = "Nie udalo sie wyciagnac danych z AliExpress — strona mogla zwrocic CAPTCHA"
        logger.warning("aliexpress_scrape_empty", product_id=product_id)
    elif not product.error:
        logger.info("aliexpress_scrape_success", product_id=product_id,
                    title=product.title[:60], price=product.price or "(none)")
    return product
