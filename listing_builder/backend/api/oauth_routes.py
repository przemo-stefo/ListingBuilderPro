# backend/api/oauth_routes.py
# Purpose: OAuth authorize/callback endpoints for marketplace connections
# NOT for: Token refresh or business logic with marketplace APIs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from config import settings
from database import get_db
from api.dependencies import get_user_id
from services.oauth_service import (
    get_amazon_authorize_url,
    handle_amazon_callback,
    get_allegro_authorize_url,
    handle_allegro_callback,
    get_connections,
    disconnect,
)

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/oauth", tags=["OAuth"])


# ── Connection status ─────────────────────────────────────────────────────────

@router.get("/connections")
async def list_connections(request: Request, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    """List all OAuth connections with status."""
    conns = get_connections(db, user_id)
    return {
        "connections": [
            {
                "id": str(c.id),
                "marketplace": c.marketplace,
                "status": c.status,
                "seller_id": c.seller_id,
                "seller_name": c.seller_name,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in conns
        ]
    }


# ── Amazon OAuth ──────────────────────────────────────────────────────────────

@router.get("/amazon/authorize")
@limiter.limit("10/minute")
async def amazon_authorize(request: Request, user_id: str = Depends(get_user_id)):
    """Generate Amazon Seller Central OAuth URL."""
    result = get_amazon_authorize_url(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/amazon/callback")
async def amazon_callback(
    spapi_oauth_code: str = "",
    state: str = "",
    selling_partner_id: str = "",
    db: Session = Depends(get_db),
):
    """
    Amazon OAuth callback — exchanges authorization code for tokens.
    WHY query params: Amazon redirects with spapi_oauth_code, state, selling_partner_id
    """
    if not spapi_oauth_code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    result = await handle_amazon_callback(spapi_oauth_code, state, selling_partner_id, db)

    if "error" in result:
        logger.error("amazon_oauth_callback_error", error=result["error"])
        # WHY redirect: user is on the callback URL, redirect to frontend with error
        frontend = "https://panel.octohelper.com" if settings.app_env == "production" else "http://localhost:3000"
        return RedirectResponse(f"{frontend}/compliance?tab=integrations&oauth=error&msg={result['error']}")

    frontend = "https://panel.octohelper.com" if settings.app_env == "production" else "http://localhost:3000"
    return RedirectResponse(f"{frontend}/compliance?tab=integrations&oauth=success&marketplace=amazon")


# ── Allegro OAuth ─────────────────────────────────────────────────────────────

@router.get("/allegro/authorize")
@limiter.limit("10/minute")
async def allegro_authorize(request: Request, user_id: str = Depends(get_user_id)):
    """Generate Allegro OAuth URL."""
    result = get_allegro_authorize_url(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/allegro/callback")
async def allegro_callback(
    code: str = "",
    state: str = "",
    db: Session = Depends(get_db),
):
    """Allegro OAuth callback — exchanges authorization code for tokens."""
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    result = await handle_allegro_callback(code, state, db)

    if "error" in result:
        logger.error("allegro_oauth_callback_error", error=result["error"])
        frontend = "https://panel.octohelper.com" if settings.app_env == "production" else "http://localhost:3000"
        return RedirectResponse(f"{frontend}/converter?allegro=error&msg={result['error']}")

    frontend = "https://panel.octohelper.com" if settings.app_env == "production" else "http://localhost:3000"
    return RedirectResponse(f"{frontend}/converter?allegro=connected")


# ── Connection status (all marketplaces) ──────────────────────────────────

@router.get("/status")
async def connection_status(request: Request, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    """Return status of all OAuth connections — frontend uses for reconnect banners."""
    from datetime import datetime as dt, timezone as tz, timedelta as td
    conns = get_connections(db, user_id)
    return {
        "connections": {
            c.marketplace: {
                "status": c.status,
                "expires_soon": (
                    c.token_expires_at is not None
                    and c.token_expires_at.tzinfo is not None
                    and c.token_expires_at < dt.now(tz.utc) + td(hours=1)
                ) if c.status == "active" else False,
            }
            for c in conns
        }
    }


# ── Disconnect ────────────────────────────────────────────────────────────────

@router.delete("/{marketplace}")
async def disconnect_marketplace(request: Request, marketplace: str, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    """Remove an OAuth connection."""
    if not disconnect(db, marketplace, user_id):
        raise HTTPException(status_code=404, detail=f"No connection for {marketplace}")
    return {"status": "disconnected", "marketplace": marketplace}
