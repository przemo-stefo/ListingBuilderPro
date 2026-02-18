# backend/services/oauth_service.py
# Purpose: OAuth2 authorize URL generation + callback token exchange for Amazon & Allegro
# NOT for: Token refresh caching (that's sp_api_auth.py) or UI logic

import hashlib
import hmac
import json
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from config import settings
from models.oauth_connection import OAuthConnection

logger = structlog.get_logger()

STATE_TTL = 600  # 10 minutes


# ── Stateless CSRF state (survives Render free tier restarts) ────────────────

def _sign_state(marketplace: str, user_id: str = "default") -> str:
    """Generate signed OAuth state token.

    WHY stateless: Render free tier sleeps after 15 min — in-memory dict would
    lose state between authorize and callback. HMAC-signed token encodes
    marketplace + timestamp + user_id, verified on callback without any storage.

    WHY user_id in state: OAuth callbacks are PUBLIC_PATHS (no JWT) because
    the browser redirects from Allegro/Amazon. We encode user_id here so the
    callback can associate the connection with the correct user.
    """
    payload = json.dumps({"m": marketplace, "t": int(time.time()), "u": user_id})
    encoded = urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(
        settings.webhook_secret.encode(), encoded.encode(), hashlib.sha256
    ).hexdigest()[:24]
    return f"{encoded}.{sig}"


def _verify_state(state: str) -> Optional[Dict]:
    """Verify signed OAuth state, return payload or None."""
    parts = state.split(".", 1)
    if len(parts) != 2:
        return None

    encoded, sig = parts
    expected = hmac.new(
        settings.webhook_secret.encode(), encoded.encode(), hashlib.sha256
    ).hexdigest()[:24]

    if not hmac.compare_digest(sig, expected):
        return None

    # WHY padding: urlsafe_b64decode needs correct padding
    padded = encoded + "=" * (-len(encoded) % 4)
    try:
        payload = json.loads(urlsafe_b64decode(padded))
    except Exception:
        return None

    if time.time() - payload.get("t", 0) > STATE_TTL:
        return None

    return payload


# ── URL helpers ───────────────────────────────────────────────────────────────

def _frontend_url() -> str:
    if settings.app_env == "production":
        return "https://panel.octohelper.com"
    return "http://localhost:3000"


def _backend_url() -> str:
    """WHY direct backend URL: OAuth callbacks must bypass the proxy because
    the proxy's fetch() follows redirects, breaking the browser redirect flow.
    The backend callback is in PUBLIC_PATHS (no API key needed)."""
    if settings.app_env == "production":
        return "https://api-listing.feedmasters.org"
    return "http://localhost:8000"


# ── Amazon SP-API OAuth ──────────────────────────────────────────────────────

AMAZON_AUTH_URL = "https://sellercentral.amazon.de/apps/authorize/consent"
AMAZON_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


def get_amazon_authorize_url(user_id: str = "default") -> Dict:
    """Generate Amazon Seller Central OAuth URL with CSRF state."""
    if not settings.amazon_client_id:
        return {"error": "Amazon client_id not configured"}

    state = _sign_state("amazon", user_id)
    redirect_uri = f"{_backend_url()}/api/oauth/amazon/callback"

    params = {
        "application_id": settings.amazon_client_id,
        "state": state,
        "redirect_uri": redirect_uri,
    }

    url = f"{AMAZON_AUTH_URL}?{urlencode(params)}"
    return {"authorize_url": url, "state": state}


async def handle_amazon_callback(
    code: str,
    state: str,
    selling_partner_id: Optional[str],
    db: Session,
) -> Dict:
    """Exchange Amazon authorization code for refresh token."""
    payload = _verify_state(state)
    if not payload or payload.get("m") != "amazon":
        return {"error": "Invalid or expired state parameter"}

    # WHY: user_id encoded in state during authorize step (callbacks have no JWT)
    user_id = payload.get("u", "default")

    if not settings.amazon_client_id or not settings.amazon_client_secret:
        return {"error": "Amazon credentials not configured"}

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.amazon_client_id,
        "client_secret": settings.amazon_client_secret,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(AMAZON_TOKEN_URL, data=data)

    if resp.status_code != 200:
        logger.error("amazon_oauth_token_failed", status=resp.status_code, body=resp.text[:200])
        return {"error": f"Token exchange failed: {resp.status_code}"}

    data = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == "amazon",
    ).first()

    if not conn:
        conn = OAuthConnection(user_id=user_id, marketplace="amazon")
        db.add(conn)

    conn.status = "active"
    conn.access_token = data.get("access_token")
    conn.refresh_token = data.get("refresh_token")
    conn.token_expires_at = expires_at
    conn.seller_id = selling_partner_id
    conn.raw_data = {"token_type": data.get("token_type"), "scope": data.get("scope")}
    conn.updated_at = datetime.now(timezone.utc)

    db.commit()
    logger.info("amazon_oauth_connected", seller_id=selling_partner_id)

    return {"status": "connected", "marketplace": "amazon", "seller_id": selling_partner_id}


# ── Allegro OAuth ────────────────────────────────────────────────────────────

ALLEGRO_AUTH_URL = "https://allegro.pl/auth/oauth/authorize"
ALLEGRO_TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_allegro_authorize_url(user_id: str = "default") -> Dict:
    """Generate Allegro OAuth URL with CSRF state."""
    if not settings.allegro_client_id:
        return {"error": "Allegro client_id not configured"}

    state = _sign_state("allegro", user_id)
    redirect_uri = f"{_backend_url()}/api/oauth/allegro/callback"

    params = {
        "response_type": "code",
        "client_id": settings.allegro_client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    url = f"{ALLEGRO_AUTH_URL}?{urlencode(params)}"
    return {"authorize_url": url, "state": state}


async def handle_allegro_callback(
    code: str,
    state: str,
    db: Session,
) -> Dict:
    """Exchange Allegro authorization code for tokens."""
    payload = _verify_state(state)
    if not payload or payload.get("m") != "allegro":
        return {"error": "Invalid or expired state parameter"}

    # WHY: user_id encoded in state during authorize step (callbacks have no JWT)
    user_id = payload.get("u", "default")

    if not settings.allegro_client_id or not settings.allegro_client_secret:
        return {"error": "Allegro credentials not configured"}

    redirect_uri = f"{_backend_url()}/api/oauth/allegro/callback"

    # WHY: Allegro uses HTTP Basic auth for token exchange
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            ALLEGRO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(settings.allegro_client_id, settings.allegro_client_secret),
        )

    if resp.status_code != 200:
        logger.error("allegro_oauth_token_failed", status=resp.status_code, body=resp.text[:200])
        return {"error": f"Token exchange failed: {resp.status_code}"}

    data = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 43200))

    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == "allegro",
    ).first()

    if not conn:
        conn = OAuthConnection(user_id=user_id, marketplace="allegro")
        db.add(conn)

    conn.status = "active"
    conn.access_token = data.get("access_token")
    conn.refresh_token = data.get("refresh_token")
    conn.token_expires_at = expires_at
    conn.scopes = data.get("scope")
    conn.raw_data = {"token_type": data.get("token_type"), "allegro_api": data.get("allegro_api")}
    conn.updated_at = datetime.now(timezone.utc)

    db.commit()
    logger.info("allegro_oauth_connected")

    return {"status": "connected", "marketplace": "allegro"}


# ── Connection status ────────────────────────────────────────────────────────

def get_connections(db: Session, user_id: str = "default") -> list:
    """List all OAuth connections for a user."""
    return db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
    ).order_by(OAuthConnection.marketplace).all()


def get_connection(db: Session, marketplace: str, user_id: str = "default") -> Optional[OAuthConnection]:
    """Get OAuth connection for a specific marketplace + user."""
    return db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == marketplace,
    ).first()


def disconnect(db: Session, marketplace: str, user_id: str = "default") -> bool:
    """Revoke/delete an OAuth connection."""
    conn = get_connection(db, marketplace, user_id)
    if not conn:
        return False
    db.delete(conn)
    db.commit()
    logger.info("oauth_disconnected", marketplace=marketplace, user_id=user_id)
    return True
