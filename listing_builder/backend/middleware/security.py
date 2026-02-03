# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/middleware/security.py
# Purpose: Security headers and HTTPS enforcement
# NOT for: Authentication or authorization

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import structlog

from config import settings

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.

    Headers added:
    - Strict-Transport-Security (HSTS) - Force HTTPS
    - X-Content-Type-Options - Prevent MIME sniffing
    - X-Frame-Options - Prevent clickjacking
    - X-XSS-Protection - Enable XSS filter
    - Content-Security-Policy - Restrict resource loading
    - Referrer-Policy - Control referrer information

    Why these headers:
    - HSTS: Ensures browser always uses HTTPS (prevents downgrade attacks)
    - nosniff: Prevents browser from interpreting files as different type
    - DENY: Prevents site from being embedded in iframe (clickjacking protection)
    - XSS Protection: Enables browser's built-in XSS filter
    - CSP: Restricts what resources can load (XSS protection)
    - Referrer: Controls what referrer info is sent
    """

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)

        # Add security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add CORS headers if not already set by CORS middleware
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = settings.cors_origins_list[0]

        return response


async def https_redirect_middleware(request: Request, call_next):
    """
    Redirect HTTP to HTTPS in production.

    Why:
    - Protects API keys in transit
    - Prevents man-in-the-middle attacks
    - Required for many services (Stripe, payment processors)

    How it works:
    - Checks X-Forwarded-Proto header (set by reverse proxy)
    - If HTTP in production → redirect to HTTPS
    - Otherwise → proceed normally

    Note: Railway/Vercel automatically handle HTTPS, but this is defense-in-depth
    """
    # Only enforce in production
    if not settings.is_production:
        return await call_next(request)

    # Check if request is HTTP (via proxy header)
    forwarded_proto = request.headers.get("X-Forwarded-Proto")

    if forwarded_proto == "http":
        # Build HTTPS URL
        url = str(request.url).replace("http://", "https://", 1)

        logger.info("https_redirect", original=str(request.url), redirect=url)

        # Redirect to HTTPS
        return RedirectResponse(url=url, status_code=307)  # 307 = Temporary Redirect

    # Already HTTPS or local development
    return await call_next(request)
