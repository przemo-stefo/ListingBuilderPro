# backend/services/sp_api_auth.py
# Purpose: Amazon SP-API LWA (Login with Amazon) token exchange with caching
# NOT for: Report fetching or business logic

import httpx
import time
import structlog
from config import settings

logger = structlog.get_logger()

# WHY module-level cache: token valid 1h, we cache 55min to avoid edge-case expiry
_token_cache: dict = {"access_token": None, "expires_at": 0}

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


async def get_access_token() -> str:
    """
    Exchange refresh_token for a short-lived access_token via LWA.
    Caches result for 55 minutes (token valid 3600s).
    Raises ValueError if credentials not configured.
    """
    if not settings.amazon_refresh_token:
        raise ValueError("Amazon refresh token not configured")
    if not settings.amazon_client_id or not settings.amazon_client_secret:
        raise ValueError("Amazon client_id/client_secret not configured")

    # Return cached token if still valid
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": settings.amazon_refresh_token,
        "client_id": settings.amazon_client_id,
        "client_secret": settings.amazon_client_secret,
    }

    # WHY retry: LWA occasionally returns 429 under load
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(LWA_TOKEN_URL, data=payload)

        if resp.status_code == 200:
            data = resp.json()
            _token_cache["access_token"] = data["access_token"]
            # WHY 55min: 5min safety margin before actual 60min expiry
            _token_cache["expires_at"] = time.time() + 3300
            logger.info("sp_api_token_refreshed")
            return data["access_token"]

        if resp.status_code == 429:
            wait = 2 ** attempt
            logger.warning("sp_api_token_rate_limited", attempt=attempt, wait=wait)
            import asyncio
            await asyncio.sleep(wait)
            continue

        logger.error("sp_api_token_failed", status=resp.status_code, body=resp.text[:200])
        raise RuntimeError(f"LWA token exchange failed: {resp.status_code} — {resp.text[:200]}")

    raise RuntimeError("LWA token exchange failed after 3 retries (rate limited)")


def credentials_configured() -> bool:
    """Check if SP-API credentials are set (not empty strings)."""
    return bool(settings.amazon_client_id and settings.amazon_client_secret)


def has_refresh_token() -> bool:
    """Check if refresh token is available."""
    return bool(settings.amazon_refresh_token)
