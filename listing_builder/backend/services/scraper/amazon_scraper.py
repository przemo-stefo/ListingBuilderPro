# backend/services/scraper/amazon_scraper.py
# Purpose: Parse Amazon URL/ASIN, detect marketplace, scrape product listing data
# NOT for: Full product catalog, pricing, or inventory — just title/bullets/description for scoring

import os
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse, quote

import httpx
import structlog

logger = structlog.get_logger()

# WHY: Map Amazon TLD → marketplace label for UI display
AMAZON_DOMAIN_MAP = {
    "amazon.com": "US",
    "amazon.co.uk": "UK",
    "amazon.de": "DE",
    "amazon.fr": "FR",
    "amazon.it": "IT",
    "amazon.es": "ES",
    "amazon.pl": "PL",
    "amazon.nl": "NL",
    "amazon.se": "SE",
    "amazon.ca": "CA",
    "amazon.com.mx": "MX",
    "amazon.co.jp": "JP",
    "amazon.com.au": "AU",
    "amazon.in": "IN",
    "amazon.com.br": "BR",
    "amazon.sa": "SA",
    "amazon.ae": "AE",
    "amazon.sg": "SG",
    "amazon.com.tr": "TR",
    "amazon.com.be": "BE",
    "amazon.eg": "EG",
}


@dataclass
class AmazonListing:
    """Parsed Amazon product listing data."""
    asin: str = ""
    marketplace: str = ""  # e.g. "DE", "US", "PL"
    domain: str = ""  # e.g. "amazon.de"
    title: str = ""
    bullets: list[str] = field(default_factory=list)
    description: str = ""
    url: str = ""
    error: Optional[str] = None


def parse_input(raw: str) -> AmazonListing:
    """Detect if input is an Amazon URL or standalone ASIN. Extract metadata.

    Handles:
    - Full URLs: https://www.amazon.de/dp/B0XXXXXX/ref=...
    - Short URLs: https://amzn.to/XXXX (returns ASIN empty, needs redirect)
    - Bare ASIN: B0XXXXXX (10 chars, starts with B0 or numeric)
    - ASIN with marketplace hint: B0XXXXXX amazon.de
    """
    raw = raw.strip()
    result = AmazonListing()

    # WHY: Try URL parse first — if it has a scheme, it's likely a URL
    if raw.startswith("http://") or raw.startswith("https://"):
        return _parse_url(raw, result)

    # WHY: Check for bare ASIN (10 alphanumeric chars)
    asin_match = re.match(r'^([A-Z0-9]{10})$', raw.upper())
    if asin_match:
        result.asin = asin_match.group(1)
        return result

    # WHY: ASIN + marketplace hint like "B0XXXXXX amazon.de" or "B0XXXXXX DE"
    parts = raw.split()
    if len(parts) >= 2:
        potential_asin = parts[0].upper()
        if re.match(r'^[A-Z0-9]{10}$', potential_asin):
            result.asin = potential_asin
            hint = parts[1].lower().replace("www.", "")
            # Check if hint is a domain
            if hint in AMAZON_DOMAIN_MAP:
                result.marketplace = AMAZON_DOMAIN_MAP[hint]
                result.domain = hint
            # Check if hint is a marketplace code
            elif hint.upper() in AMAZON_DOMAIN_MAP.values():
                result.marketplace = hint.upper()
                # Reverse lookup domain
                for d, m in AMAZON_DOMAIN_MAP.items():
                    if m == result.marketplace:
                        result.domain = d
                        break
            return result

    result.error = "Nie rozpoznano — wklej link Amazon lub ASIN (np. B0DXXXXXX)"
    return result


def _parse_url(url: str, result: AmazonListing) -> AmazonListing:
    """Extract ASIN and marketplace from an Amazon product URL."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().replace("www.", "")

    # WHY: Detect marketplace from domain
    if hostname in AMAZON_DOMAIN_MAP:
        result.marketplace = AMAZON_DOMAIN_MAP[hostname]
        result.domain = hostname
    elif hostname in ("amzn.to", "a.co"):
        # Short URL — we know it's Amazon but need to follow redirect for ASIN
        result.url = url
        result.marketplace = "US"  # default, may change after redirect
        return result
    else:
        result.error = f"Nieznana domena: {hostname}"
        return result

    # WHY: Extract ASIN from URL path — multiple Amazon URL patterns
    path = parsed.path
    # Pattern 1: /dp/ASIN or /dp/ASIN/...
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', path, re.IGNORECASE)
    if not asin_match:
        # Pattern 2: /gp/product/ASIN
        asin_match = re.search(r'/gp/product/([A-Z0-9]{10})', path, re.IGNORECASE)
    if not asin_match:
        # Pattern 3: /ASIN/ (some old URLs)
        asin_match = re.search(r'/([A-Z0-9]{10})(?:/|$)', path, re.IGNORECASE)

    if asin_match:
        result.asin = asin_match.group(1).upper()
    else:
        result.error = "Nie znaleziono ASIN w linku — sprawdź URL"
        return result

    result.url = f"https://www.{result.domain}/dp/{result.asin}"
    return result


# ── HTML SCRAPING ──────────────────────────────────────────────────

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


class _AmazonHTMLParser(HTMLParser):
    """Extract title, bullets, and description from Amazon product page HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.bullets: list[str] = []
        self.description = ""

        # Internal state tracking
        self._in_title = False
        self._in_feature_bullets = False
        self._in_bullet_span = False
        self._in_description = False
        self._current_bullet = ""
        self._desc_parts: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        tag_id = attr_dict.get("id", "")

        if tag == "span" and tag_id == "productTitle":
            self._in_title = True
        elif tag_id == "feature-bullets":
            self._in_feature_bullets = True
        elif self._in_feature_bullets and tag == "span" and "a-list-item" in attr_dict.get("class", ""):
            self._in_bullet_span = True
            self._current_bullet = ""
        elif tag_id == "productDescription":
            self._in_description = True
            self._depth = 0
        elif self._in_description:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._in_title and tag == "span":
            self._in_title = False
        if self._in_bullet_span and tag == "span":
            text = self._current_bullet.strip()
            if text and text not in ("›", "‹"):
                self.bullets.append(text)
            self._in_bullet_span = False
        if self._in_feature_bullets and tag == "div":
            self._in_feature_bullets = False
        if self._in_description:
            if tag == "div":
                if self._depth <= 0:
                    self.description = " ".join(self._desc_parts).strip()
                    self._in_description = False
                else:
                    self._depth -= 1

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text
        elif self._in_bullet_span:
            self._current_bullet += " " + text
        elif self._in_description:
            self._desc_parts.append(text)


async def fetch_listing(listing: AmazonListing) -> AmazonListing:
    """Fetch product page and parse title/bullets/description.

    Uses Scrape.do if token available, falls back to direct httpx.
    """
    if not listing.asin or listing.error:
        return listing

    url = listing.url or f"https://www.{listing.domain or 'amazon.com'}/dp/{listing.asin}"
    listing.url = url

    scrape_do_token = os.environ.get("SCRAPE_DO_TOKEN", "")

    try:
        html = ""
        # WHY: Try scrape.do first (handles anti-bot), fall back to direct on failure
        if scrape_do_token:
            try:
                html = await _fetch_via_scrape_do(url, scrape_do_token)
            except Exception as e:
                logger.warning("scrape_do_failed_fallback_direct", error=str(e)[:80])
        if not html:
            html = await _fetch_direct(url)

        if not html:
            listing.error = "Nie udało się pobrać strony — spróbuj ponownie"
            return listing

        parser = _AmazonHTMLParser()
        parser.feed(html)

        listing.title = parser.title.strip()
        listing.bullets = parser.bullets
        listing.description = parser.description

        if not listing.title:
            listing.error = "Nie znaleziono tytułu — Amazon mógł zablokować zapytanie"

        logger.info(
            "amazon_fetch_ok",
            asin=listing.asin,
            marketplace=listing.marketplace,
            title_len=len(listing.title),
            bullets=len(listing.bullets),
        )

    except Exception as e:
        logger.error("amazon_fetch_error", asin=listing.asin, error=str(e))
        listing.error = f"Błąd pobierania: {str(e)[:100]}"

    return listing


async def _fetch_via_scrape_do(url: str, token: str) -> str:
    """Fetch page via Scrape.do proxy — handles anti-bot."""
    api_url = f"https://api.scrape.do?token={token}&url={quote(url, safe='')}&render=false"
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()
        return resp.text


async def _fetch_direct(url: str) -> str:
    """Direct fetch with browser-like headers. Works for some marketplaces."""
    import random
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,pl;q=0.8,de;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text
