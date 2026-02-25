# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/middleware/auth.py
# Purpose: API key authentication middleware
# NOT for: User authentication (JWT) or database operations

from fastapi import Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import hmac
import structlog

from config import settings

logger = structlog.get_logger()

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Dependency to verify API key in requests.

    Usage:
        @app.get("/protected")
        async def protected_route(api_key: str = Depends(verify_api_key)):
            return {"message": "Access granted"}

    Raises:
        HTTPException: 401 if API key is invalid or missing
    """
    # Allow health check without auth
    # (Checked in middleware, but added here for direct dependency usage)

    if not x_api_key:
        logger.warning("api_key_missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not hmac.compare_digest(x_api_key, settings.api_secret_key):
        # WHY: Hash prefix instead of raw chars — avoids leaking key material in logs
        import hashlib
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()[:8] if x_api_key else None
        logger.warning("api_key_invalid", key_hash=key_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("api_key_validated")
    return x_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API key on all requests.

    Exceptions:
    - /health - Health check endpoint (for load balancers)
    - / - Root endpoint (API info)
    - /docs, /redoc, /openapi.json - API documentation (if enabled)

    Why middleware:
    - Centralized authentication check
    - No need to add Depends(verify_api_key) to every route
    - Consistent error responses
    """

    # Public endpoints that don't require auth
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/stripe/webhook",  # WHY: Stripe sends webhooks without our API key — auth via signature
        "/api/oauth/amazon/callback",  # WHY: Amazon redirects user here without our API key
        "/api/oauth/allegro/callback",  # WHY: Allegro redirects user here without our API key
        "/api/oauth/ebay/callback",  # WHY: eBay redirects user here without our API key
        "/api/import/webhook",  # WHY: n8n calls with X-Webhook-Secret, not X-API-Key
        "/api/auth/me",  # WHY: Uses JWT directly, no API key needed
    }

    async def dispatch(self, request: Request, call_next):
        """
        Process each request and validate API key.

        Flow:
        1. Check if path is public → allow
        2. Check if API key present → validate → allow
        3. Else → reject with 401
        """
        path = request.url.path

        # Allow public paths
        if path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Allow docs in development only
        if settings.app_debug and (path.startswith("/docs") or path.startswith("/redoc")):
            return await call_next(request)

        # WHY: Try JWT first (Supabase Auth), then fall back to API key (proxy)
        from middleware.supabase_auth import get_user_id_from_jwt
        user_id = get_user_id_from_jwt(request)
        if user_id:
            # WHY: Store user_id on request state so dependencies can access it
            request.state.user_id = user_id
            logger.debug("jwt_auth_ok", path=path, user_id=user_id[:8])
            response = await call_next(request)
            return response

        # Verify API key (fallback for proxy requests)
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("auth_missing", path=path, ip=request.client.host)
            return self._unauthorized_response("Missing authentication. Include Authorization or X-API-Key header.")

        if not hmac.compare_digest(api_key, settings.api_secret_key):
            # WHY: Hash prefix instead of raw chars — avoids leaking key material in logs
            import hashlib
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8] if api_key else None
            logger.warning(
                "api_key_invalid",
                path=path,
                ip=request.client.host,
                key_hash=key_hash,
            )
            return self._unauthorized_response("Invalid API key")

        # Valid API key - proceed (user_id = "default" for backward compat)
        request.state.user_id = "default"
        logger.debug("api_key_validated", path=path)
        response = await call_next(request)
        return response

    def _unauthorized_response(self, detail: str):
        """Return 401 Unauthorized response"""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
            headers={"WWW-Authenticate": "ApiKey"},
        )
