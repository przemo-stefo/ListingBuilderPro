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
from api.dependencies import get_user_id
from schemas import (
    SettingsResponse,
    GeneralSettings,
    MarketplaceConnection,
    NotificationSettings,
    DataExportSettings,
    LLMSettings,
    LLMProviderConfig,
    GPSRSettings,
)
from services.llm_providers import mask_api_key
import structlog

logger = structlog.get_logger()

# WHY: USER_ID constant removed — now comes from get_user_id() dependency


class SettingsUpdateRequest(BaseModel):
    """Typed update payload — only known sections accepted.

    WHY: Using dict allowed arbitrary keys (injection risk).
    Pydantic ignores unknown fields and validates types.
    """
    general: Optional[GeneralSettings] = None
    marketplace_connections: Optional[List[MarketplaceConnection]] = None
    notifications: Optional[NotificationSettings] = None
    data_export: Optional[DataExportSettings] = None
    llm: Optional[LLMSettings] = None
    gpsr: Optional[GPSRSettings] = None


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
    "llm": {
        "default_provider": "groq",
        "providers": {},
    },
    "gpsr": {
        "manufacturer_contact": "",
        "manufacturer_address": "",
        "manufacturer_city": "",
        "manufacturer_country": "",
        "country_of_origin": "",
        "safety_attestation": "",
        "responsible_person_type": "",
        "responsible_person_name": "",
        "responsible_person_address": "",
        "responsible_person_country": "",
        "amazon_browse_node": "",
        "amazon_product_type": "",
        "ebay_category_id": "",
        "kaufland_category": "",
    },
}


def _load_settings(db: Session, user_id: str) -> dict:
    """Load settings from DB, falling back to defaults."""
    row = db.execute(
        text("SELECT settings FROM user_settings WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if row and row[0]:
        return row[0]
    return dict(_DEFAULT_SETTINGS)


def _save_settings(db: Session, data: dict, user_id: str) -> None:
    """Upsert settings to DB."""
    db.execute(
        text(
            "INSERT INTO user_settings (user_id, settings, updated_at) "
            "VALUES (:uid, CAST(:data AS jsonb), NOW()) "
            "ON CONFLICT (user_id) DO UPDATE SET settings = CAST(:data AS jsonb), updated_at = NOW()"
        ),
        {"uid": user_id, "data": json.dumps(data)},
    )
    db.commit()


def _build_response(data: dict) -> SettingsResponse:
    """Build a typed response from settings dict. Masks LLM API keys for safety."""
    llm_data = data.get("llm", _DEFAULT_SETTINGS["llm"])
    # WHY: Never return raw API keys in GET — mask them
    masked_providers = {}
    for pname, pconf in llm_data.get("providers", {}).items():
        raw_key = pconf.get("api_key", "") if isinstance(pconf, dict) else ""
        masked_providers[pname] = LLMProviderConfig(api_key=mask_api_key(raw_key))

    return SettingsResponse(
        general=GeneralSettings(**data["general"]),
        marketplace_connections=[
            MarketplaceConnection(**mc) for mc in data["marketplace_connections"]
        ],
        notifications=NotificationSettings(**data["notifications"]),
        data_export=DataExportSettings(**data["data_export"]),
        llm=LLMSettings(
            default_provider=llm_data.get("default_provider", "groq"),
            providers=masked_providers,
        ),
        gpsr=GPSRSettings(**data.get("gpsr", _DEFAULT_SETTINGS["gpsr"])),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings(request: Request, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    """Get all application settings (from DB)."""
    data = _load_settings(db, user_id)
    return _build_response(data)


@router.put("", response_model=SettingsResponse)
@limiter.limit("10/minute")
async def update_settings(
    request: Request,
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Update settings — merges each section independently.
    Persisted to Supabase so they survive restarts.
    """
    data = _load_settings(db, user_id)

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

    if payload.llm is not None:
        if "llm" not in data:
            data["llm"] = dict(_DEFAULT_SETTINGS["llm"])
        llm_update = payload.llm.model_dump(exclude_unset=True)
        if "default_provider" in llm_update:
            data["llm"]["default_provider"] = llm_update["default_provider"]
        # WHY: Merge per-provider keys — don't wipe unrelated providers
        if "providers" in llm_update:
            if "providers" not in data["llm"]:
                data["llm"]["providers"] = {}
            for pname, pconf in llm_update["providers"].items():
                key_val = pconf.get("api_key", "") if isinstance(pconf, dict) else ""
                # WHY: Skip masked keys (****) — means client didn't change the key
                if key_val and "****" not in key_val:
                    data["llm"]["providers"][pname] = {"api_key": key_val}

    if payload.gpsr is not None:
        if "gpsr" not in data:
            data["gpsr"] = dict(_DEFAULT_SETTINGS["gpsr"])
        data["gpsr"].update(payload.gpsr.model_dump(exclude_unset=True))

    _save_settings(db, data, user_id)
    logger.info("settings_saved", user_id=user_id)
    return _build_response(data)
