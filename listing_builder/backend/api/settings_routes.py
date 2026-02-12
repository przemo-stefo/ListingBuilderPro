# backend/api/settings_routes.py
# Purpose: Settings endpoint — persisted to Supabase user_settings table
# NOT for: App config or env vars (those stay in config.py)

import json
from typing import List, Optional
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    SettingsResponse,
    GeneralSettings,
    MarketplaceConnection,
    NotificationSettings,
    DataExportSettings,
)
import structlog

logger = structlog.get_logger()

USER_ID = "default"  # WHY: Single-user for now; swap to auth user_id later


class SettingsUpdateRequest(BaseModel):
    """Typed update payload — only known sections accepted.

    WHY: Using dict allowed arbitrary keys (injection risk).
    Pydantic ignores unknown fields and validates types.
    """
    general: Optional[GeneralSettings] = None
    marketplace_connections: Optional[List[MarketplaceConnection]] = None
    notifications: Optional[NotificationSettings] = None
    data_export: Optional[DataExportSettings] = None


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/settings", tags=["Settings"])

# WHY: Default settings used when no DB row exists yet
_DEFAULT_SETTINGS = {
    "general": {
        "store_name": "My Marketplace Store",
        "default_marketplace": "amazon",
        "timezone": "America/New_York",
    },
    "marketplace_connections": [
        {"id": "amazon", "name": "Amazon", "connected": False, "api_key": "", "last_synced": None},
        {"id": "ebay", "name": "eBay", "connected": False, "api_key": "", "last_synced": None},
        {"id": "kaufland", "name": "Kaufland", "connected": False, "api_key": "", "last_synced": None},
        {"id": "allegro", "name": "Allegro", "connected": False, "api_key": "", "last_synced": None},
    ],
    "notifications": {
        "email_alerts": True,
        "low_stock_alerts": True,
        "competitor_price_changes": False,
        "compliance_warnings": True,
    },
    "data_export": {
        "default_export_format": "csv",
        "auto_sync_frequency": "24h",
    },
}


def _load_settings(db: Session) -> dict:
    """Load settings from DB, falling back to defaults."""
    row = db.execute(
        text("SELECT settings FROM user_settings WHERE user_id = :uid"),
        {"uid": USER_ID},
    ).fetchone()
    if row and row[0]:
        return row[0]
    return dict(_DEFAULT_SETTINGS)


def _save_settings(db: Session, data: dict) -> None:
    """Upsert settings to DB."""
    db.execute(
        text(
            "INSERT INTO user_settings (user_id, settings, updated_at) "
            "VALUES (:uid, CAST(:data AS jsonb), NOW()) "
            "ON CONFLICT (user_id) DO UPDATE SET settings = CAST(:data AS jsonb), updated_at = NOW()"
        ),
        {"uid": USER_ID, "data": json.dumps(data)},
    )
    db.commit()


def _build_response(data: dict) -> SettingsResponse:
    """Build a typed response from settings dict."""
    return SettingsResponse(
        general=GeneralSettings(**data["general"]),
        marketplace_connections=[
            MarketplaceConnection(**mc) for mc in data["marketplace_connections"]
        ],
        notifications=NotificationSettings(**data["notifications"]),
        data_export=DataExportSettings(**data["data_export"]),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get all application settings (from DB)."""
    data = _load_settings(db)
    return _build_response(data)


@router.put("", response_model=SettingsResponse)
@limiter.limit("10/minute")
async def update_settings(
    request: Request,
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update settings — merges each section independently.
    Persisted to Supabase so they survive restarts.
    """
    data = _load_settings(db)

    if payload.general is not None:
        data["general"].update(payload.general.model_dump(exclude_unset=True))

    if payload.marketplace_connections is not None:
        data["marketplace_connections"] = [
            mc.model_dump() for mc in payload.marketplace_connections
        ]

    if payload.notifications is not None:
        data["notifications"].update(payload.notifications.model_dump(exclude_unset=True))

    if payload.data_export is not None:
        data["data_export"].update(payload.data_export.model_dump(exclude_unset=True))

    _save_settings(db, data)
    logger.info("settings_saved", user_id=USER_ID)
    return _build_response(data)
