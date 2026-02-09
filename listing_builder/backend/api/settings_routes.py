# backend/api/settings_routes.py
# Purpose: Mock settings endpoint — store config, marketplace connections, notifications, export
# NOT for: Real settings persistence (swap to DB when user accounts exist)

from typing import List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from schemas import (
    SettingsResponse,
    GeneralSettings,
    MarketplaceConnection,
    NotificationSettings,
    DataExportSettings,
)


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

# Module-level mutable state — survives across requests until server restart
_settings: dict = {
    "general": {
        "store_name": "My Marketplace Store",
        "default_marketplace": "amazon",
        "timezone": "America/New_York",
    },
    # WHY: No mock API keys — even masked ones look like real credentials in responses
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


def _build_response() -> SettingsResponse:
    """Build a typed response from the mutable state dict."""
    return SettingsResponse(
        general=GeneralSettings(**_settings["general"]),
        marketplace_connections=[
            MarketplaceConnection(**mc) for mc in _settings["marketplace_connections"]
        ],
        notifications=NotificationSettings(**_settings["notifications"]),
        data_export=DataExportSettings(**_settings["data_export"]),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """
    Get all application settings.
    """
    return _build_response()


@router.put("", response_model=SettingsResponse)
@limiter.limit("10/minute")
async def update_settings(request: Request, payload: SettingsUpdateRequest):
    """
    Update settings — merges each section independently.
    Accepts partial updates: send only the sections you want to change.

    Example body: {"general": {"store_name": "New Name"}}
    """
    # WHY: Pydantic model ensures only known fields are accepted
    if payload.general is not None:
        _settings["general"].update(payload.general.model_dump(exclude_unset=True))

    if payload.marketplace_connections is not None:
        _settings["marketplace_connections"] = [
            mc.model_dump() for mc in payload.marketplace_connections
        ]

    if payload.notifications is not None:
        _settings["notifications"].update(payload.notifications.model_dump(exclude_unset=True))

    if payload.data_export is not None:
        _settings["data_export"].update(payload.data_export.model_dump(exclude_unset=True))

    return _build_response()
