# backend/services/gws_auth.py
# Purpose: Google Workspace OAuth token management for PYROX internal account
# NOT for: Client OAuth (gws_client_service.py) or gws CLI wrapper (removed)

from __future__ import annotations

import time
from typing import Optional

import httpx
import structlog

from config import settings

logger = structlog.get_logger()

# WHY: Module-level cache — avoid refreshing token on every API call
_token_cache: dict = {"access_token": "", "expires_at": 0}


def get_internal_token() -> Optional[str]:
    """Get a valid access token for the PYROX internal Google account.

    WHY: Uses refresh_token from env vars (GOOGLE_INTERNAL_REFRESH_TOKEN).
    Caches token in memory, refreshes 5 min before expiry.
    """
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 300:
        return _token_cache["access_token"]

    if not settings.google_internal_refresh_token:
        logger.error("gws_auth_no_refresh_token", hint="Set GOOGLE_INTERNAL_REFRESH_TOKEN env var")
        return None

    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                # WHY: Internal ops use old Desktop client credentials (separate from Web App client)
                "client_id": settings.google_internal_client_id or settings.google_oauth_client_id,
                "client_secret": settings.google_internal_client_secret or settings.google_oauth_client_secret,
                "refresh_token": settings.google_internal_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("gws_auth_refresh_failed", status=resp.status_code, body=resp.text[:200])
            return None

        data = resp.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 3600)
        return data["access_token"]
    except httpx.HTTPError as e:
        logger.error("gws_auth_refresh_error", error=str(e))
        return None


def google_api(method: str, url: str, json_data: dict = None, params: dict = None) -> dict:
    """Make authenticated Google API request using PYROX internal account.

    WHY: Direct REST API — no gws CLI dependency. Works in Docker.
    """
    token = get_internal_token()
    if not token:
        return {"error": "Google auth failed — check GOOGLE_INTERNAL_REFRESH_TOKEN"}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = httpx.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = httpx.post(url, headers=headers, json=json_data, timeout=30)
        elif method == "PUT":
            resp = httpx.put(url, headers=headers, json=json_data, params=params, timeout=30)
        elif method == "DELETE":
            resp = httpx.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if resp.status_code >= 400:
            logger.warning("google_api_error", method=method, url=url[:80], status=resp.status_code)
            return {"error": resp.text[:500], "status": resp.status_code}
        return resp.json() if resp.text.strip() else {}
    except httpx.HTTPError as e:
        logger.error("google_api_request_failed", error=str(e))
        return {"error": str(e)}
