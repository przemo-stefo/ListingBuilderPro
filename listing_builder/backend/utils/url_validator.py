# backend/utils/url_validator.py
# Purpose: Validate user-supplied URLs to prevent SSRF attacks
# NOT for: Business logic, scraping, or URL building

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional, Set


# WHY: Marketplaces we actually support — everything else is rejected
ALLOWED_MARKETPLACE_DOMAINS: dict[str, Set[str]] = {
    # WHY business.allegro.pl: sellers copy URLs from business panel
    "allegro": {"allegro.pl", "www.allegro.pl", "business.allegro.pl"},
    "amazon": {
        "amazon.de", "www.amazon.de",
        "amazon.fr", "www.amazon.fr",
        "amazon.it", "www.amazon.it",
        "amazon.es", "www.amazon.es",
        "amazon.pl", "www.amazon.pl",
        "amazon.co.uk", "www.amazon.co.uk",
        "amazon.com", "www.amazon.com",
        "amazon.nl", "www.amazon.nl",
        "amazon.se", "www.amazon.se",
    },
    "ebay": {
        "ebay.com", "www.ebay.com",
        "ebay.de", "www.ebay.de",
        "ebay.co.uk", "www.ebay.co.uk",
        "ebay.fr", "www.ebay.fr",
        "ebay.it", "www.ebay.it",
        "ebay.es", "www.ebay.es",
        "ebay.pl", "www.ebay.pl",
    },
    "kaufland": {"www.kaufland.de", "kaufland.de"},
}

# WHY: Flat set of all allowed domains for quick lookup when marketplace is unknown
ALL_ALLOWED_DOMAINS: Set[str] = set()
for domains in ALLOWED_MARKETPLACE_DOMAINS.values():
    ALL_ALLOWED_DOMAINS.update(domains)


def validate_marketplace_url(url: str, marketplace: Optional[str] = None) -> str:
    """
    Validate that a URL points to a real marketplace domain.
    SECURITY: Prevents SSRF by rejecting internal/private URLs.

    Returns the validated URL or raises ValueError.
    """
    if not url:
        raise ValueError("URL is required")

    parsed = urlparse(url)

    # WHY: Only HTTPS in production — HTTP is a downgrade attack vector
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    # SECURITY: Check against private/internal IP ranges
    _reject_private_host(hostname)

    # WHY: If marketplace specified, check against that marketplace's domains
    if marketplace and marketplace in ALLOWED_MARKETPLACE_DOMAINS:
        allowed = ALLOWED_MARKETPLACE_DOMAINS[marketplace]
        if hostname not in allowed:
            raise ValueError(
                f"URL domain '{hostname}' is not a valid {marketplace} domain"
            )
    else:
        # WHY: No marketplace → check against ALL known marketplace domains
        if hostname not in ALL_ALLOWED_DOMAINS:
            raise ValueError(
                f"URL domain '{hostname}' is not a recognized marketplace domain"
            )

    return url


def validate_webhook_url(url: str) -> str:
    """
    Validate webhook URL: must be HTTPS, no private IPs.
    SECURITY: Prevents SSRF via webhook delivery.
    """
    if not url:
        raise ValueError("Webhook URL is required")

    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError("Webhook URL must use HTTPS")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Webhook URL has no hostname")

    _reject_private_host(hostname)

    return url


def _reject_private_host(hostname: str) -> None:
    """
    Reject hostnames that resolve to private/internal IPs.
    SECURITY: Core SSRF protection — prevents fetching localhost, metadata APIs, etc.
    """
    # WHY: Reject obvious private hostnames before DNS resolution
    private_hostnames = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
    if hostname.lower() in private_hostnames:
        raise ValueError("Internal/private URLs are not allowed")

    # WHY: Try to resolve and check if IP is private
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise ValueError(f"URL resolves to private/internal IP ({ip_str})")
    except socket.gaierror:
        # WHY: DNS resolution failed — could be a crafted hostname, reject it
        raise ValueError(f"Cannot resolve hostname: {hostname}")
