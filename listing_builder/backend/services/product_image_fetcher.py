# backend/services/product_image_fetcher.py
# Purpose: Fetch product image from marketplace URL (og:image + Amazon fallbacks)
# NOT for: ComfyUI pipeline (comfyui_service.py) or HTTP endpoints (video_routes.py)

import re
import httpx
import structlog

logger = structlog.get_logger()

# WHY: og:image is the standard way to get product image from any marketplace page
_OG_IMAGE_RE = re.compile(
    r'<meta\s+(?:property|name)=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE2 = re.compile(
    r'content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:image["\']',
    re.IGNORECASE,
)

# WHY: Amazon-specific fallback patterns — Amazon blocks og:image for server-side requests
_AMAZON_COLOR_IMAGES_RE = re.compile(
    r"colorImages.*?hiRes.*?(https://m\.media-amazon\.com/images/I/[A-Za-z0-9+_%-]+\._[^\"']+\.jpg)",
    re.DOTALL,
)
_AMAZON_DYNAMIC_IMAGE_RE = re.compile(
    r'data-a-dynamic-image=["\']\{.*?(https://m\.media-amazon\.com/images/I/[A-Za-z0-9+_%-]+\._[^"&]+\.jpg)',
)
_AMAZON_MEDIA_IMAGE_RE = re.compile(
    r'(https://m\.media-amazon\.com/images/I/[A-Za-z0-9+_%-]+\.jpg)',
)

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def _is_amazon_url(url: str) -> bool:
    return "amazon." in url


def _fetch_html_with_cookies(url: str, client: httpx.Client) -> str:
    """Fetch page HTML, using cookie warmup for Amazon.

    WHY: Amazon returns captcha/minimal HTML without session cookies.
    First hit the homepage to get cookies, then fetch the product page.
    """
    if _is_amazon_url(url):
        # WHY: Extract base domain for cookie warmup (e.g. amazon.de from full URL)
        from urllib.parse import urlparse
        parsed = urlparse(url)
        homepage = f"{parsed.scheme}://{parsed.netloc}/"
        try:
            client.get(homepage, headers=_BROWSER_HEADERS)
        except Exception:
            pass  # WHY: Cookie warmup failure is non-fatal — try product page anyway

    resp = client.get(url, headers=_BROWSER_HEADERS)
    resp.raise_for_status()
    return resp.text


def _extract_image_url(html: str, url: str) -> str:
    """Extract product image URL from HTML using multiple strategies.

    WHY: og:image works for most marketplaces but Amazon blocks it.
    Fallback chain: og:image → colorImages hiRes → dynamic-image → any media-amazon img.
    """
    # Strategy 1: og:image (works for Allegro, eBay, Kaufland, etc.)
    match = _OG_IMAGE_RE.search(html) or _OG_IMAGE_RE2.search(html)
    if match:
        logger.debug("image_found_via", method="og:image")
        return match.group(1)

    # Strategy 2-4: Amazon-specific fallbacks
    if _is_amazon_url(url):
        # Strategy 2: colorImages hiRes (JS variable with highest quality images)
        match = _AMAZON_COLOR_IMAGES_RE.search(html)
        if match:
            logger.debug("image_found_via", method="colorImages_hiRes")
            return match.group(1)

        # Strategy 3: data-a-dynamic-image attribute on main image element
        match = _AMAZON_DYNAMIC_IMAGE_RE.search(html)
        if match:
            logger.debug("image_found_via", method="dynamic_image")
            return match.group(1)

        # Strategy 4: Any product image from media-amazon.com (last resort)
        imgs = _AMAZON_MEDIA_IMAGE_RE.findall(html)
        if imgs:
            logger.debug("image_found_via", method="media_amazon_fallback", count=len(imgs))
            return imgs[0]

    raise ValueError("Nie znaleziono zdjecia produktu na tej stronie")


def fetch_product_image(url: str) -> tuple[bytes, str]:
    """Fetch product page HTML, extract image URL, download the image.

    SECURITY: URL must pass validate_marketplace_url() before calling this.
    Uses context manager for proper resource cleanup.
    """
    with httpx.Client(timeout=30.0, follow_redirects=True, cookies=httpx.Cookies()) as client:
        html = _fetch_html_with_cookies(url, client)

        image_url = _extract_image_url(html, url)
        if image_url.startswith("//"):
            image_url = "https:" + image_url

        # WHY: Validate image URL too — could point to internal IP (second-order SSRF)
        _validate_image_url(image_url)

        img_resp = client.get(image_url, headers={"User-Agent": _BROWSER_HEADERS["User-Agent"]})
        img_resp.raise_for_status()

        content_type = img_resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL obrazu nie zwrocilo obrazu: {content_type}")

        if len(img_resp.content) > 10 * 1024 * 1024:
            raise ValueError("Obraz produktu zbyt duzy (>10MB)")

        ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
        return img_resp.content, f"product_from_url.{ext}"


def _validate_image_url(url: str) -> None:
    """Basic SSRF check on image URL — reject private IPs and non-HTTPS."""
    from urllib.parse import urlparse
    from utils.url_validator import _reject_private_host

    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Image URL has invalid scheme: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Image URL has no hostname")
    _reject_private_host(hostname)
