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
        logger.warning("api_key_invalid", key_prefix=x_api_key[:8] if x_api_key else None)
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

        # Verify API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("api_key_missing", path=path, ip=request.client.host)
            return self._unauthorized_response("Missing API key. Include X-API-Key header.")

        if not hmac.compare_digest(api_key, settings.api_secret_key):
            logger.warning(
                "api_key_invalid",
                path=path,
                ip=request.client.host,
                key_prefix=api_key[:8] if api_key else None,
            )
            return self._unauthorized_response("Invalid API key")

        # Valid API key - proceed
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
