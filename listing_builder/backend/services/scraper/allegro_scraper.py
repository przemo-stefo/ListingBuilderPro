# backend/services/scraper/allegro_scraper.py
# Purpose: Scrape product data from Allegro.pl product pages
# NOT for: Data conversion, template generation, or AI translation

import asyncio
import json
import os
import random
import re
from html.parser import HTMLParser
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import quote

import httpx
import structlog

logger = structlog.get_logger()

# WHY pool: Same UA across all requests is a fingerprinting signal.
_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
]

# Stealth init script for Playwright fallback path
_STEALTH_INIT_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {
        get: () => ['pl-PL', 'pl', 'en-US', 'en']
    });
    delete window.__playwright;
    delete window.__pw_manual;
"""


@dataclass
class AllegroProduct:
    """Scraped product data from a single Allegro listing."""

    source_url: str = ""
    source_id: str = ""  # Allegro offer ID extracted from URL
    title: str = ""
    description: str = ""  # HTML description
    price: str = ""
    currency: str = "PLN"
    ean: str = ""
    images: List[str] = field(default_factory=list)
    category: str = ""
    quantity: str = ""
    condition: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    brand: str = ""
    manufacturer: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_offer_id(url: str) -> str:
    """Extract numeric offer ID from Allegro URL."""
    clean_url = url.split("?")[0].split("#")[0].rstrip("/")
    match = re.search(r'-(\d{8,12})$', clean_url)
    if match:
        return match.group(1)
    match = re.search(r'/(\d{8,12})$', clean_url)
    if match:
        return match.group(1)
    return ""


def _get_scrape_do_token() -> str:
    """Get Scrape.do API token from env or config."""
    token = os.environ.get("SCRAPE_DO_TOKEN", "")
    if not token:
        try:
            from backend.config import settings
            token = settings.scrape_do_token
        except Exception:
            pass
    return token


def _get_scraperapi_key() -> str:
    """Get ScraperAPI key from env or config."""
    key = os.environ.get("SCRAPERAPI_KEY", "")
    if not key:
        try:
            from config import settings
            key = getattr(settings, "scraperapi_key", "")
        except Exception:
            pass
    return key


def _get_proxy_config() -> Optional[dict]:
    """Build Playwright proxy config from SCRAPER_PROXY_URL env var.

    Only used for the Playwright fallback path (when no Scrape.do token).
    """
    proxy_url = os.environ.get("SCRAPER_PROXY_URL", "")
    if not proxy_url:
        try:
            from backend.config import settings
            proxy_url = settings.scraper_proxy_url
        except Exception:
            pass
    if proxy_url:
        return {"server": proxy_url}
    return None


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY 1: Scrape.do API mode (recommended)
# Scrape.do handles DataDome bypass, Polish residential IPs, everything.
# We just parse the returned HTML. No browser needed.
# ═══════════════════════════════════════════════════════════════════════

def _parse_html_product(html: str, product: AllegroProduct) -> None:
    """Parse product data from Allegro static HTML (no browser needed).

    WHY not BeautifulSoup: avoid adding a dependency just for parsing.
    Allegro's static HTML (render=false) embeds product data in:
    - <h1> for title
    - <title> tag for EAN (in parentheses)
    - <table> inside Parameters section for specs
    - <script> tags with JSON for price (meta tags are JS-rendered)
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

    # ── Title from <h1> ──
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1_match:
        product.title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()

    # ── EAN from <title> tag ──
    # WHY: Allegro puts EAN in parentheses in <title>, e.g.:
    # "Product Name (5905525375211) • Cena, Opinie • Kawa ziarnista"
    title_tag = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
    if title_tag:
        ean_in_title = re.search(r'\((\d{8,14})\)', title_tag.group(1))
        if ean_in_title:
            product.ean = ean_in_title.group(1)

    # ── Price from embedded script JSON ──
    # WHY not meta tags: price meta tags are JS-rendered (not in static HTML).
    # But Allegro embeds price in analytics/config scripts as JSON.
    # Try three patterns, most specific first:
    #   1. "offerId":"...","price":"67.90","currency":"PLN" (product data)
    #   2. "price":67.9,"currency":"PLN" (analytics tracking)
    #   3. "formattedPrice":"67,90 zł" (UI component)
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

    # ── JSON-LD structured data (present in rendered HTML, rare in static) ──
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

    # ── Images ──
    # WHY filter for /original/: Allegro serves thumbnails at /s128/, /s400/ etc.
    # We want the highest resolution version.
    # WHY skip "action-": Allegro UI icons (action-common-information, etc.)
    # are hosted on allegroimg too but aren't product photos.
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
        # Fallback: collect any allegro product images and upscale to /original/
        for match in re.finditer(r'<img[^>]+src="([^"]*allegroimg[^"]*)"', html):
            src = match.group(1)
            filename = src.rsplit("/", 1)[-1] if "/" in src else src
            if not any(filename.startswith(p) for p in _ICON_PATTERNS):
                full_size = re.sub(r'/s\d+/', '/original/', src)
                img_urls.add(full_size)
    product.images = list(img_urls)

    # ── Parameters from <table> ──
    # WHY table not li: Allegro's static HTML uses <table> with <tr> rows,
    # first <td> = key, second <td> = value.
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
                # WHY remove tooltip: Allegro nests a role="tooltip" div
                # inside the value <td> with explanatory text like
                # "Nowy oznacza..." which pollutes the extracted value.
                val_html = re.sub(
                    r'<div[^>]*role="tooltip"[^>]*>.*?</div>',
                    '', tds[1], flags=re.DOTALL
                )
                val = re.sub(r'<[^>]+>', '', val_html).strip()
                key = re.sub(r'\s+', ' ', key).strip()
                val = re.sub(r'\s+', ' ', val).strip()
                if key and val:
                    product.parameters[key] = val

    # ── EAN from parameters (if not found in title tag) ──
    if not product.ean:
        for key, val in product.parameters.items():
            if key.upper() in ("EAN", "GTIN", "EAN (GTIN)", "KOD EAN"):
                product.ean = val.strip()
                break

    # ── Brand / Manufacturer shortcuts ──
    for param_key, param_val in product.parameters.items():
        if "marka" in param_key.lower() and not product.brand:
            product.brand = param_val
        if "producent" in param_key.lower() and not product.manufacturer:
            product.manufacturer = param_val

    # ── Description HTML ──
    desc_match = re.search(
        r'data-box-name="Description"[^>]*>(.*?)(?:data-box-name=|$)',
        html, re.DOTALL
    )
    if desc_match:
        product.description = desc_match.group(1).strip()[:5000]

    # ── Condition (from "Stan" parameter) ──
    for key, val in product.parameters.items():
        if "Stan" in key:
            product.condition = val
            break


async def _scrape_via_scrape_do(url: str, token: str) -> AllegroProduct:
    """Scrape Allegro via Scrape.do API mode (static HTML, no render).

    WHY API mode not proxy mode: DataDome blocks proxy-mode connections
    because the browser fingerprint still comes from our local Playwright.
    API mode means Scrape.do's servers handle the full request from their
    residential Polish IPs.

    WHY no render: Scrape.do render=true returns 502 for Allegro (DataDome
    blocks their headless browser too). Static HTML (no render) works and
    contains all product data: title in <h1>, price in embedded script JSON,
    parameters in <table>, EAN in <title> tag, images in <img> tags.
    """
    product = AllegroProduct(source_url=url, source_id=extract_offer_id(url))

    # Build Scrape.do API URL — static HTML, Polish residential IP
    encoded_url = quote(url, safe="")
    api_url = (
        f"https://api.scrape.do/"
        f"?token={token}"
        f"&url={encoded_url}"
        f"&super=true"
        f"&geoCode=pl"
    )

    logger.info("scrape_do_request", url=url, offer_id=product.source_id)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.get(api_url)

            if resp.status_code != 200:
                # Check if Scrape.do returned a JSON error
                try:
                    err_data = resp.json()
                    msg = err_data.get("Message", [str(resp.status_code)])
                    product.error = f"Scrape.do error: {'; '.join(msg) if isinstance(msg, list) else msg}"
                except Exception:
                    product.error = f"Scrape.do returned HTTP {resp.status_code}"
                logger.error("scrape_do_failed", status=resp.status_code, url=url)
                return product

            html = resp.text

            # Parse product data from HTML
            _parse_html_product(html, product)

            logger.info(
                "scrape_do_complete",
                offer_id=product.source_id,
                title=product.title[:60] if product.title else "(empty)",
                price=product.price or "(none)",
                params_count=len(product.parameters),
                images_count=len(product.images),
                has_ean=bool(product.ean),
            )

    except httpx.TimeoutException:
        product.error = "Scrape.do request timed out (90s). Allegro may be slow or blocking."
        logger.error("scrape_do_timeout", url=url)
    except Exception as e:
        product.error = f"Scrape.do request failed: {str(e)}"
        logger.error("scrape_do_error", url=url, error=str(e))

    return product


async def _scrape_via_scraperapi(url: str, api_key: str) -> AllegroProduct:
    """Scrape Allegro via ScraperAPI (same approach as Scrape.do — HTTP API returns HTML)."""
    product = AllegroProduct(source_url=url, source_id=extract_offer_id(url))
    encoded_url = quote(url, safe="")
    api_url = f"https://api.scraperapi.com?api_key={api_key}&url={encoded_url}&country_code=pl"

    logger.info("scraperapi_request", url=url, offer_id=product.source_id)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.get(api_url)
            if resp.status_code != 200:
                product.error = f"ScraperAPI returned HTTP {resp.status_code}"
                logger.error("scraperapi_failed", status=resp.status_code, url=url)
                return product

            _parse_html_product(resp.text, product)
            logger.info(
                "scraperapi_complete",
                offer_id=product.source_id,
                title=product.title[:60] if product.title else "(empty)",
                price=product.price or "(none)",
            )
    except httpx.TimeoutException:
        product.error = "ScraperAPI request timed out (90s)"
        logger.error("scraperapi_timeout", url=url)
    except Exception as e:
        product.error = f"ScraperAPI request failed: {str(e)}"
        logger.error("scraperapi_error", url=url, error=str(e))

    return product


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY 3: Playwright fallback (direct or with raw proxy)
# Used when no Scrape.do token is configured.
# ═══════════════════════════════════════════════════════════════════════

async def _handle_cookie_consent(page) -> None:
    """Click Allegro's GDPR consent button if it appears."""
    try:
        consent_btn = await page.query_selector('[data-role="accept-consent"]')
        if consent_btn:
            await consent_btn.click()
            logger.info("cookie_consent_handled")
            await asyncio.sleep(0.5)
            return

        buttons = await page.query_selector_all("button")
        for btn in buttons:
            text = await btn.inner_text()
            if "akceptuj" in text.lower():
                await btn.click()
                logger.info("cookie_consent_handled", method="text_match")
                await asyncio.sleep(0.5)
                return

        logger.debug("no_cookie_consent_banner")
    except Exception:
        logger.debug("cookie_consent_skipped")


async def _detect_block(page) -> Optional[str]:
    """Check if Allegro blocked us. Returns error message or None."""
    try:
        title = await page.title()
        body_text = await page.evaluate(
            "() => document.body?.innerText?.substring(0, 500) || ''"
        )
        combined = (title + " " + body_text).lower()

        if "zablokowany" in combined or "blocked" in combined:
            return (
                "Allegro blocked this IP. Set SCRAPE_DO_TOKEN in .env "
                "(free at scrape.do) or use SCRAPER_PROXY_URL."
            )
        if "captcha" in combined or "datadome" in combined:
            return "Allegro CAPTCHA/DataDome challenge. Use SCRAPE_DO_TOKEN."
        if "enable js" in combined and len(body_text.strip()) < 100:
            return (
                "Allegro DataDome JS challenge failed. "
                "Set SCRAPE_DO_TOKEN in .env (free at scrape.do)."
            )
    except Exception:
        pass
    return None


async def _extract_product_data(page, product: AllegroProduct) -> None:
    """Extract all product fields from a loaded Allegro page (Playwright)."""
    title_el = await page.query_selector("h1")
    if title_el:
        product.title = (await title_el.inner_text()).strip()

    price_el = await page.query_selector('meta[itemprop="price"]')
    if price_el:
        product.price = await price_el.get_attribute("content") or ""

    currency_el = await page.query_selector('meta[itemprop="priceCurrency"]')
    if currency_el:
        product.currency = await currency_el.get_attribute("content") or "PLN"

    json_ld_data = await page.evaluate("""
        () => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            return [...scripts].map(s => {
                try { return JSON.parse(s.textContent); }
                catch { return null; }
            }).filter(Boolean);
        }
    """)
    for ld in (json_ld_data or []):
        if isinstance(ld, dict):
            for key in ("gtin13", "gtin", "gtin8", "gtin12", "gtin14"):
                if ld.get(key):
                    product.ean = str(ld[key])
                    break
            if ld.get("@type") == "BreadcrumbList" and ld.get("itemListElement"):
                items = ld["itemListElement"]
                if items:
                    product.category = " > ".join(
                        item.get("item", {}).get("name", "")
                        for item in items
                        if item.get("item", {}).get("name")
                    )

    images = await page.evaluate("""
        () => {
            const urls = new Set();
            document.querySelectorAll('img[src*="allegro"]').forEach(img => {
                const src = img.src || img.dataset?.src || '';
                if (src.includes('allegro.pl') || src.includes('a.allegroimg')) {
                    const fullSize = src.replace(/\\/s\\d+\\//, '/original/');
                    urls.add(fullSize);
                }
            });
            return [...urls];
        }
    """)
    product.images = images or []

    parameters = await page.evaluate("""
        () => {
            const params = {};
            const selectors = [
                'div[data-box-name="Parameters"] li',
                '[data-testid="product-parameter"]',
                'div[class*="parameter"] li',
            ];
            for (const sel of selectors) {
                const items = document.querySelectorAll(sel);
                if (items.length > 0) {
                    items.forEach(item => {
                        const parts = item.textContent.trim().split(':');
                        if (parts.length >= 2) {
                            const key = parts[0].trim();
                            const val = parts.slice(1).join(':').trim();
                            if (key && val) params[key] = val;
                        }
                    });
                    break;
                }
            }
            return params;
        }
    """)
    product.parameters = parameters or {}

    if not product.ean:
        for key, val in product.parameters.items():
            if key.upper() in ("EAN", "GTIN", "EAN (GTIN)", "KOD EAN"):
                product.ean = val.strip()
                break

    for param_key, param_val in product.parameters.items():
        if "marka" in param_key.lower() and not product.brand:
            product.brand = param_val
        if "producent" in param_key.lower() and not product.manufacturer:
            product.manufacturer = param_val

    description = await page.evaluate("""
        () => {
            const descSection = document.querySelector(
                '[data-box-name="Description"] div[class*="description"]'
            ) || document.querySelector('[data-testid="description"]');
            return descSection ? descSection.innerHTML : '';
        }
    """)
    product.description = description or ""

    for key, val in product.parameters.items():
        if "Stan" in key:
            product.condition = val
            break


async def _scrape_via_playwright(url: str, _browser=None) -> AllegroProduct:
    """Fallback: scrape with Playwright + stealth when no Scrape.do token."""
    product = AllegroProduct(source_url=url, source_id=extract_offer_id(url))
    owns_browser = _browser is None

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        product.error = (
            "playwright not installed. Run: pip install playwright && "
            "playwright install chromium"
        )
        return product

    pw_instance = None

    try:
        proxy = _get_proxy_config()
        using_proxy = proxy is not None

        if owns_browser:
            pw_instance = await async_playwright().start()
            _browser = await pw_instance.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                proxy=proxy,
            )

        context = await _browser.new_context(
            user_agent=random.choice(_USER_AGENTS),
            locale="pl-PL",
            timezone_id="Europe/Warsaw",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=using_proxy,
        )
        await context.add_init_script(_STEALTH_INIT_SCRIPT)

        try:
            from playwright_stealth import stealth_async
            page = await context.new_page()
            await stealth_async(page)
            logger.info("stealth_applied", method="playwright_stealth")
        except ImportError:
            page = await context.new_page()
            logger.info("stealth_applied", method="init_script_only")

        logger.info("scraping_allegro_playwright", url=url)

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await _handle_cookie_consent(page)
        await asyncio.sleep(random.uniform(2.0, 5.0))

        block_msg = await _detect_block(page)
        if block_msg:
            product.error = block_msg
            logger.warning("allegro_blocked", url=url, message=block_msg)
            await context.close()
            return product

        await _extract_product_data(page, product)
        await context.close()

        logger.info(
            "scrape_complete",
            offer_id=product.source_id,
            title=product.title[:60],
            params_count=len(product.parameters),
            images_count=len(product.images),
        )

    except Exception as e:
        product.error = f"Scraping failed: {str(e)}"
        logger.error("scrape_failed", url=url, error=str(e))

    finally:
        if owns_browser:
            if _browser:
                await _browser.close()
            if pw_instance:
                await pw_instance.stop()

    return product


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API (unchanged interface)
# ═══════════════════════════════════════════════════════════════════════

async def scrape_allegro_product(url: str, _browser=None) -> AllegroProduct:
    """Scrape full product data from a single Allegro product URL.

    Strategy:
    1. Scrape.do API mode (if SCRAPE_DO_TOKEN is set) — handles DataDome
    2. Playwright with stealth (fallback) — may be blocked without proxy

    Args:
        url: Full Allegro product URL
        _browser: Optional shared Playwright browser (for batch fallback)

    Returns:
        AllegroProduct with all extracted fields
    """
    # Strategy 1: Scrape.do API (recommended, handles DataDome)
    token = _get_scrape_do_token()
    if token:
        return await _scrape_via_scrape_do(url, token)

    # Strategy 2: ScraperAPI (same HTTP approach, different provider)
    scraperapi_key = _get_scraperapi_key()
    if scraperapi_key:
        return await _scrape_via_scraperapi(url, scraperapi_key)

    # Strategy 3: Playwright fallback
    return await _scrape_via_playwright(url, _browser)


async def scrape_allegro_batch(
    urls: List[str], delay: float = 3.0
) -> List[AllegroProduct]:
    """Scrape multiple Allegro products sequentially.

    Uses Scrape.do API if token is set (no browser needed),
    otherwise falls back to shared Playwright browser.

    Args:
        urls: List of Allegro product URLs
        delay: Base seconds between requests (randomized ±30%)

    Returns:
        List of AllegroProduct results (some may have errors)
    """
    results = []
    total = len(urls)
    token = _get_scrape_do_token()

    if token:
        # Scrape.do path — simple HTTP calls, no browser
        for i, url in enumerate(urls):
            logger.info("batch_scraping", progress=f"{i+1}/{total}", url=url[:80])
            product = await _scrape_via_scrape_do(url, token)
            results.append(product)

            if i < total - 1:
                jittered = random.uniform(delay * 0.7, delay * 1.3)
                await asyncio.sleep(jittered)
    else:
        # Playwright fallback — shared browser instance
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            error_msg = (
                "playwright not installed. Run: pip install playwright && "
                "playwright install chromium"
            )
            return [AllegroProduct(source_url=u, error=error_msg) for u in urls]

        pw_instance = await async_playwright().start()
        try:
            proxy = _get_proxy_config()
            browser = await pw_instance.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                proxy=proxy,
            )

            for i, url in enumerate(urls):
                logger.info("batch_scraping", progress=f"{i+1}/{total}", url=url[:80])
                product = await _scrape_via_playwright(url, _browser=browser)
                results.append(product)

                if i < total - 1:
                    jittered = random.uniform(delay * 0.7, delay * 1.3)
                    await asyncio.sleep(jittered)

            await browser.close()
        finally:
            await pw_instance.stop()

    succeeded = sum(1 for r in results if not r.error)
    logger.info(
        "batch_complete", total=total, succeeded=succeeded,
        failed=total - succeeded,
    )
    return results
