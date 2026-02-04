# backend/services/scraper/allegro_scraper.py
# Purpose: Scrape product data from Allegro.pl product pages using Playwright
# NOT for: Data conversion, template generation, or AI translation

import asyncio
import json
import os
import random
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

import structlog

logger = structlog.get_logger()

# WHY pool: Same UA across all requests is a fingerprinting signal.
# Allegro's DataDome checks this. Rotate per session.
_USER_AGENTS = [
    # Chrome 131 on Windows 11
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    # Chrome 131 on macOS Sonoma
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    # Chrome 130 on Windows 11
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    # Edge 131 on Windows 11
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    ),
    # Chrome 131 on macOS Ventura
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
]

# WHY init_script: Allegro uses DataDome which checks navigator.webdriver,
# window.chrome, plugins, and languages to detect headless browsers.
# These overrides make the browser look like a real user session.
_STEALTH_INIT_SCRIPT = """
    // Hide webdriver flag (primary detection vector)
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

    // Spoof chrome runtime (headless Chrome lacks this)
    window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};

    // Spoof plugins (headless has empty array)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });

    // Spoof languages (must match locale)
    Object.defineProperty(navigator, 'languages', {
        get: () => ['pl-PL', 'pl', 'en-US', 'en']
    });

    // Remove automation indicators
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
    # Convenience accessors for common parameters
    brand: str = ""
    manufacturer: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_offer_id(url: str) -> str:
    """Extract numeric offer ID from Allegro URL.

    Allegro URLs end with the offer ID after the last dash:
    https://allegro.pl/oferta/some-product-name-12345678 → 12345678
    Also handles query params: ...12345678?utm=abc → 12345678
    """
    # Strip query string and fragment first
    clean_url = url.split("?")[0].split("#")[0].rstrip("/")
    match = re.search(r'-(\d{8,12})$', clean_url)
    if match:
        return match.group(1)
    # Fallback: try to find any large number at end of path
    match = re.search(r'/(\d{8,12})$', clean_url)
    if match:
        return match.group(1)
    return ""


def _get_proxy_config() -> Optional[dict]:
    """Read proxy URL from env. Returns Playwright proxy dict or None."""
    proxy_url = os.environ.get("SCRAPER_PROXY_URL", "")
    if not proxy_url:
        # Also try config if imported
        try:
            from backend.config import settings
            proxy_url = settings.scraper_proxy_url
        except Exception:
            pass
    if proxy_url:
        return {"server": proxy_url}
    return None


async def _handle_cookie_consent(page) -> None:
    """Click Allegro's GDPR consent button if it appears.

    WHY: Without accepting cookies, Allegro may not fully render product data.
    Non-blocking — if the banner doesn't show up, we just continue.
    """
    try:
        # Allegro uses data-role="accept-consent" on their cookie banner
        consent_btn = await page.query_selector('[data-role="accept-consent"]')
        if consent_btn:
            await consent_btn.click()
            logger.info("cookie_consent_handled")
            await asyncio.sleep(0.5)
            return

        # Fallback: look for button with Polish text "Akceptuję"
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
        # Non-blocking — cookie consent is best-effort
        logger.debug("cookie_consent_skipped")


async def _detect_block(page) -> Optional[str]:
    """Check if Allegro blocked us. Returns error message or None.

    WHY: Without this, the scraper silently returns empty data when blocked.
    Now it reports WHY scraping failed so the user can take action (use proxy, etc).
    """
    try:
        title = await page.title()
        body_text = await page.evaluate("() => document.body?.innerText?.substring(0, 500) || ''")
        combined = (title + " " + body_text).lower()

        if "zablokowany" in combined or "blocked" in combined:
            return (
                "Allegro blocked this IP (anti-bot protection). "
                "Set SCRAPER_PROXY_URL in .env to use a residential proxy, "
                "or wait and retry later."
            )
        if "captcha" in combined or "datadome" in combined:
            return (
                "Allegro triggered CAPTCHA/DataDome challenge. "
                "Use a residential proxy (SCRAPER_PROXY_URL) to bypass."
            )
        # WHY: DataDome serves a 403 page with just "Please enable JS and
        # disable any ad blocker" — it means the JS challenge failed to
        # resolve, which happens when DataDome fingerprints the browser.
        if "enable js" in combined and len(body_text.strip()) < 100:
            return (
                "Allegro DataDome anti-bot blocked this request (JS challenge failed). "
                "A residential proxy is required. Set SCRAPER_PROXY_URL in .env "
                "(e.g. http://user:pass@proxy:port)."
            )
    except Exception:
        pass
    return None


async def _extract_product_data(page, product: AllegroProduct) -> None:
    """Extract all product fields from a loaded Allegro page.

    Separated from browser management so both single and batch
    scraping can share this logic.
    """
    # ── Title ──
    title_el = await page.query_selector("h1")
    if title_el:
        product.title = (await title_el.inner_text()).strip()

    # ── Price from meta tag (most reliable) ──
    price_el = await page.query_selector('meta[itemprop="price"]')
    if price_el:
        product.price = await price_el.get_attribute("content") or ""

    currency_el = await page.query_selector('meta[itemprop="priceCurrency"]')
    if currency_el:
        product.currency = await currency_el.get_attribute("content") or "PLN"

    # ── JSON-LD structured data ──
    json_ld_data = await page.evaluate("""
        () => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            return [...scripts].map(s => {
                try { return JSON.parse(s.textContent); }
                catch { return null; }
            }).filter(Boolean);
        }
    """)

    # Extract EAN from JSON-LD
    for ld in (json_ld_data or []):
        if isinstance(ld, dict):
            for key in ("gtin13", "gtin", "gtin8", "gtin12", "gtin14"):
                if ld.get(key):
                    product.ean = str(ld[key])
                    break
            # Also grab category from breadcrumb
            if ld.get("@type") == "BreadcrumbList" and ld.get("itemListElement"):
                items = ld["itemListElement"]
                if items:
                    product.category = " > ".join(
                        item.get("item", {}).get("name", "")
                        for item in items
                        if item.get("item", {}).get("name")
                    )

    # ── Images ──
    images = await page.evaluate("""
        () => {
            const urls = new Set();
            // Gallery thumbnails
            document.querySelectorAll('img[src*="allegro"]').forEach(img => {
                const src = img.src || img.dataset?.src || '';
                if (src.includes('allegro.pl') || src.includes('a.allegroimg')) {
                    // Get full-size version by replacing size suffix
                    const fullSize = src.replace(/\\/s\\d+\\//, '/original/');
                    urls.add(fullSize);
                }
            });
            return [...urls];
        }
    """)
    product.images = images or []

    # ── Parameters table ──
    parameters = await page.evaluate("""
        () => {
            const params = {};
            // Multiple selector strategies because Allegro changes class names
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
                    break;  // Use first selector that works
                }
            }
            return params;
        }
    """)
    product.parameters = parameters or {}

    # Extract EAN from parameters if not found in JSON-LD
    if not product.ean:
        for key, val in product.parameters.items():
            if key.upper() in ("EAN", "GTIN", "EAN (GTIN)", "KOD EAN"):
                product.ean = val.strip()
                break

    # Extract common parameter shortcuts
    param_map = {
        "Marka": "brand",
        "Producent": "manufacturer",
    }
    for pl_key, attr_name in param_map.items():
        for param_key, param_val in product.parameters.items():
            if pl_key.lower() in param_key.lower():
                setattr(product, attr_name, param_val)
                break

    # ── Description HTML ──
    description = await page.evaluate("""
        () => {
            // Allegro loads description in a separate section
            const descSection = document.querySelector(
                '[data-box-name="Description"] div[class*="description"]'
            ) || document.querySelector('[data-testid="description"]');
            return descSection ? descSection.innerHTML : '';
        }
    """)
    product.description = description or ""

    # ── Condition ──
    for key, val in product.parameters.items():
        if "Stan" in key:
            product.condition = val
            break


async def scrape_allegro_product(url: str, _browser=None) -> AllegroProduct:
    """Scrape full product data from a single Allegro product URL.

    Uses Playwright (headless Chromium) with stealth anti-detection
    because Allegro uses DataDome-level bot protection.

    Args:
        url: Full Allegro product URL
        _browser: Optional shared browser instance (used by batch scraping).
                  If None, creates and closes its own browser.

    Returns:
        AllegroProduct with all extracted fields
    """
    product = AllegroProduct(source_url=url, source_id=extract_offer_id(url))
    owns_browser = _browser is None

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        product.error = "playwright not installed. Run: pip install playwright && playwright install chromium"
        logger.error("playwright_not_installed")
        return product

    pw_instance = None

    try:
        # WHY reuse: batch scraping passes a shared browser so we don't
        # launch/close a new browser for every product (suspicious + slow)
        if owns_browser:
            pw_instance = await async_playwright().start()

            proxy = _get_proxy_config()
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
            _browser = await pw_instance.chromium.launch(
                headless=True,
                args=launch_args,
                proxy=proxy,
            )

        context = await _browser.new_context(
            user_agent=random.choice(_USER_AGENTS),
            locale="pl-PL",
            timezone_id="Europe/Warsaw",
            viewport={"width": 1920, "height": 1080},
        )

        # WHY stealth: navigator.webdriver=true is the #1 detection signal
        await context.add_init_script(_STEALTH_INIT_SCRIPT)

        # Also try playwright-stealth for deeper patches (CDP-level)
        try:
            from playwright_stealth import stealth_async
            page = await context.new_page()
            await stealth_async(page)
            logger.info("stealth_applied", method="playwright_stealth")
        except ImportError:
            page = await context.new_page()
            logger.info("stealth_applied", method="init_script_only")

        # WHY no resource blocking: the old code blocked images/fonts/analytics.
        # Blocking resources is a major bot detection signal — real browsers load
        # everything. Removed to reduce fingerprint.

        logger.info("scraping_allegro", url=url, offer_id=product.source_id)

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Handle GDPR cookie consent (may block page rendering)
        await _handle_cookie_consent(page)

        # WHY random: fixed sleep(3) is a bot pattern. Randomize render wait.
        await asyncio.sleep(random.uniform(2.0, 5.0))

        # Check if Allegro blocked us BEFORE trying to extract data
        block_msg = await _detect_block(page)
        if block_msg:
            product.error = block_msg
            logger.warning("allegro_blocked", url=url, message=block_msg)
            await context.close()
            return product

        # Extract all product data from the loaded page
        await _extract_product_data(page, product)

        await context.close()

        logger.info(
            "scrape_complete",
            offer_id=product.source_id,
            title=product.title[:60],
            params_count=len(product.parameters),
            images_count=len(product.images),
            has_ean=bool(product.ean),
        )

    except Exception as e:
        product.error = f"Scraping failed: {str(e)}"
        logger.error("scrape_failed", url=url, error=str(e))

    finally:
        # Only close browser if we created it (not shared from batch)
        if owns_browser:
            if _browser:
                await _browser.close()
            if pw_instance:
                await pw_instance.stop()

    return product


async def scrape_allegro_batch(urls: List[str], delay: float = 3.0) -> List[AllegroProduct]:
    """Scrape multiple Allegro products with a shared browser.

    WHY shared browser: real users don't open/close the browser for every page.
    One browser instance, new tab (page) per URL. Sequential to avoid
    triggering Allegro's anti-bot rate limits.

    Args:
        urls: List of Allegro product URLs
        delay: Base seconds between requests (randomized ±30%)

    Returns:
        List of AllegroProduct results (some may have errors)
    """
    results = []
    total = len(urls)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        error_msg = "playwright not installed. Run: pip install playwright && playwright install chromium"
        return [AllegroProduct(source_url=u, error=error_msg) for u in urls]

    pw_instance = await async_playwright().start()

    try:
        proxy = _get_proxy_config()
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]
        browser = await pw_instance.chromium.launch(
            headless=True,
            args=launch_args,
            proxy=proxy,
        )

        for i, url in enumerate(urls):
            logger.info("batch_scraping", progress=f"{i+1}/{total}", url=url[:80])
            product = await scrape_allegro_product(url, _browser=browser)
            results.append(product)

            # WHY randomize: fixed delays are a bot pattern.
            # ±30% variance makes timing look human.
            if i < total - 1:
                jittered_delay = random.uniform(delay * 0.7, delay * 1.3)
                await asyncio.sleep(jittered_delay)

        await browser.close()

    finally:
        await pw_instance.stop()

    succeeded = sum(1 for r in results if not r.error)
    logger.info("batch_complete", total=total, succeeded=succeeded, failed=total - succeeded)

    return results
