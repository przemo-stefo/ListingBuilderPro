# backend/api/settings_routes.py
# Purpose: Mock settings endpoint — store config, marketplace connections, notifications, export
# NOT for: Real settings persistence (swap to DB when user accounts exist)

from fastapi import APIRouter
from schemas import (
    SettingsResponse,
    GeneralSettings,
    MarketplaceConnection,
    NotificationSettings,
    DataExportSettings,
)

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Module-level mutable state — survives across requests until server restart
_settings: dict = {
    "general": {
        "store_name": "My Marketplace Store",
        "default_marketplace": "amazon",
        "timezone": "America/New_York",
    },
    "marketplace_connections": [
        {"id": "amazon", "name": "Amazon", "connected": True, "api_key": "****-****-****-1234", "last_synced": "2026-02-01T10:00:00Z"},
        {"id": "ebay", "name": "eBay", "connected": True, "api_key": "****-****-****-5678", "last_synced": "2026-02-01T08:30:00Z"},
        {"id": "walmart", "name": "Walmart", "connected": False, "api_key": "", "last_synced": None},
        {"id": "shopify", "name": "Shopify", "connected": True, "api_key": "****-****-****-9012", "last_synced": "2026-02-01T07:00:00Z"},
        {"id": "allegro", "name": "Allegro", "connected": True, "api_key": "****-****-****-3456", "last_synced": "2026-02-01T12:00:00Z"},
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
async def update_settings(payload: dict):
    """
    Update settings — merges each section independently.
    Accepts partial updates: send only the sections you want to change.

    Example body: {"general": {"store_name": "New Name"}}
    """
    # Merge each top-level section if provided
    if "general" in payload and isinstance(payload["general"], dict):
        _settings["general"].update(payload["general"])

    if "marketplace_connections" in payload and isinstance(payload["marketplace_connections"], list):
        _settings["marketplace_connections"] = payload["marketplace_connections"]

    if "notifications" in payload and isinstance(payload["notifications"], dict):
        _settings["notifications"].update(payload["notifications"])

    if "data_export" in payload and isinstance(payload["data_export"], dict):
        _settings["data_export"].update(payload["data_export"])

    return _build_response()
