# backend/services/scraper/allegro_scraper.py
# Purpose: Scrape product data from Allegro.pl product pages using Playwright
# NOT for: Data conversion, template generation, or AI translation

import asyncio
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

import structlog

logger = structlog.get_logger()


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


async def scrape_allegro_product(url: str) -> AllegroProduct:
    """Scrape full product data from a single Allegro product URL.

    Uses Playwright (headless Chromium) because Allegro renders
    critical product data via JavaScript.

    Args:
        url: Full Allegro product URL

    Returns:
        AllegroProduct with all extracted fields
    """
    product = AllegroProduct(source_url=url, source_id=extract_offer_id(url))

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        product.error = "playwright not installed. Run: pip install playwright && playwright install chromium"
        logger.error("playwright_not_installed")
        return product

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                locale="pl-PL",
                timezone_id="Europe/Warsaw",
                viewport={"width": 1920, "height": 1080},
            )

            page = await context.new_page()

            # Block unnecessary resources to speed up loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
            await page.route("**/analytics/**", lambda route: route.abort())
            await page.route("**/tracking/**", lambda route: route.abort())

            logger.info("scraping_allegro", url=url, offer_id=product.source_id)

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for JS to render product data
            await asyncio.sleep(3)

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

            await browser.close()

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

    return product


async def scrape_allegro_batch(urls: List[str], delay: float = 3.0) -> List[AllegroProduct]:
    """Scrape multiple Allegro products sequentially with delay.

    Sequential (not parallel) to avoid triggering Allegro's anti-bot.
    Delay between requests reduces detection risk.

    Args:
        urls: List of Allegro product URLs
        delay: Seconds to wait between requests

    Returns:
        List of AllegroProduct results (some may have errors)
    """
    results = []
    total = len(urls)

    for i, url in enumerate(urls):
        logger.info("batch_scraping", progress=f"{i+1}/{total}", url=url[:80])
        product = await scrape_allegro_product(url)
        results.append(product)

        # Delay between requests (skip after last one)
        if i < total - 1:
            await asyncio.sleep(delay)

    succeeded = sum(1 for r in results if not r.error)
    logger.info("batch_complete", total=total, succeeded=succeeded, failed=total - succeeded)

    return results
