# backend/services/scraper/temu_scraper.py
# Purpose: Scrape product data from Temu via Scrape.do (render=true)
# NOT for: HTML parsing (temu_html_parser.py)

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import quote

import httpx
import structlog

from services.scraper import get_scrape_do_token
from services.scraper.temu_html_parser import parse_temu_html

logger = structlog.get_logger()


@dataclass
class TemuProduct:
    """Scraped product data from a single Temu listing."""

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


def extract_temu_id(url: str) -> str:
    """Extract product ID from Temu URL.

    Patterns:
      /goods-detail-g-601099527865713.html → 601099527865713
      ?goods_id=601099546539029 → 601099546539029
    """
    # WHY: Slug-based URL is most common
    match = re.search(r'/goods-detail-g-(\d+)\.html', url)
    if match:
        return match.group(1)
    # WHY: Query param format used in some regions/redirects
    match = re.search(r'goods_id=(\d+)', url)
    return match.group(1) if match else ""


async def _scrape_via_scrape_do(url: str, token: str, product_id: str) -> TemuProduct:
    """Scrape Temu page via Scrape.do with render=true.

    WHY render=true: Temu uses proprietary anti-bot — needs JS execution.
    WHY beta: Temu's anti-bot is aggressive, success rate may be lower than AliExpress.
    """
    product = TemuProduct(source_url=url, source_id=product_id)
    encoded_url = quote(url, safe="")
    api_url = (
        f"https://api.scrape.do/"
        f"?token={token}"
        f"&url={encoded_url}"
        f"&render=true"
    )

    logger.info("temu_scrape_do_request", url=url, product_id=product_id)

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
                logger.error("temu_scrape_do_failed", status=resp.status_code, product_id=product_id)
                return product
            parse_temu_html(resp.text, product)
    except httpx.TimeoutException:
        product.error = "Scrape.do timeout (90s) — Temu may be slow"
        logger.error("temu_scrape_do_timeout", url=url, product_id=product_id)
    except Exception as e:
        # SECURITY: httpx exceptions may contain api_url with Scrape.do token — sanitize
        error_msg = str(e).replace(token, "***") if token in str(e) else str(e)
        product.error = f"Scrape.do request failed: {error_msg}"
        logger.error("temu_scrape_do_error", url=url, product_id=product_id, error=error_msg)

    return product


async def scrape_temu_product(url: str) -> TemuProduct:
    """Scrape product data from a Temu URL.

    Single tier: Scrape.do with render=true (no open API available).
    WHY beta: Temu's anti-bot is more aggressive than AliExpress — some fields may be missing.
    """
    # SECURITY: Validate URL domain
    from utils.url_validator import validate_marketplace_url
    try:
        validate_marketplace_url(url, "temu")
    except ValueError as e:
        return TemuProduct(source_url=url, error=f"Invalid URL: {e}")

    product_id = extract_temu_id(url)
    if not product_id:
        return TemuProduct(
            source_url=url,
            error="Nie udalo sie wyciagnac ID produktu z URL. Sprawdz link."
        )

    token = get_scrape_do_token()
    if not token:
        return TemuProduct(
            source_url=url,
            source_id=product_id,
            error="Brak tokenu Scrape.do — skonfiguruj SCRAPE_DO_TOKEN"
        )

    product = await _scrape_via_scrape_do(url, token, product_id)

    # WHY: Scrape.do may return 200 with CAPTCHA page or empty HTML — detect and report
    if not product.error and not product.title:
        product.error = "Nie udalo sie wyciagnac danych z Temu — strona mogla zwrocic CAPTCHA (beta)"
        logger.warning("temu_scrape_empty", product_id=product_id)
    elif not product.error:
        logger.info("temu_scrape_success", product_id=product_id,
                    title=product.title[:60], price=product.price or "(none)")
    return product
