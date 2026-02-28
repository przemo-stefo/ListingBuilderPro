# backend/api/alert_settings_routes.py
# Purpose: CRUD endpoints for Sellerboard-style alert type settings
# NOT for: Alert evaluation, notification delivery, or product monitoring

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List
import structlog

from database import get_db
from api.dependencies import require_user_id

limiter = Limiter(key_func=get_remote_address)
from models.monitoring import AlertTypeSetting
from schemas.alert_settings import (
    AlertTypeInfo,
    AlertSettingsBulkUpdate,
    AlertSettingResponse,
)
from services.alert_type_registry import ALERT_TYPES, ALERT_TYPE_MAP, ACTIVE_TYPES

logger = structlog.get_logger()
router = APIRouter(prefix="/api/alert-settings", tags=["Alert Settings"])


@router.get("/types", response_model=List[AlertTypeInfo])
async def get_alert_types(_user_id: str = Depends(require_user_id)):
    """Return full registry of alert types with active/inactive status."""
    return [
        AlertTypeInfo(
            type=a["type"],
            label=a["label"],
            category=a["category"],
            data_source=a["data_source"],
            default_priority=a["default_priority"],
            active=a["type"] in ACTIVE_TYPES,
        )
        for a in ALERT_TYPES
    ]


@router.get("", response_model=List[AlertSettingResponse])
async def get_alert_settings(db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """User's saved settings merged with registry defaults."""
    saved = (
        db.query(AlertTypeSetting)
        .filter(AlertTypeSetting.user_id == user_id)
        .all()
    )
    saved_map = {s.alert_type: s for s in saved}

    result = []
    for a in ALERT_TYPES:
        s = saved_map.get(a["type"])
        result.append(AlertSettingResponse(
            alert_type=a["type"],
            label=a["label"],
            category=a["category"],
            data_source=a["data_source"],
            active=a["type"] in ACTIVE_TYPES,
            priority=s.priority if s else a["default_priority"],
            notify_in_app=s.notify_in_app if s else True,
            notify_email=s.notify_email if s else False,
            email_recipients=s.email_recipients if s else [],
            enabled=s.enabled if s else True,
        ))
    return result


@router.put("")
@limiter.limit("10/minute")
async def update_alert_settings(
    request: Request,
    body: AlertSettingsBulkUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Bulk upsert all alert settings (Save button)."""
    # WHY: Reject payload with duplicate alert_type entries
    seen = set()
    for item in body.settings:
        if item.alert_type in seen:
            raise HTTPException(status_code=400, detail=f"Duplicate alert type: {item.alert_type}")
        seen.add(item.alert_type)
        if item.alert_type not in ALERT_TYPE_MAP:
            raise HTTPException(status_code=400, detail=f"Unknown alert type: {item.alert_type}")

    # WHY batch: Avoid N+1 — one SELECT instead of 24
    existing_rows = (
        db.query(AlertTypeSetting)
        .filter(AlertTypeSetting.user_id == user_id)
        .all()
    )
    existing_map = {row.alert_type: row for row in existing_rows}

    for item in body.settings:
        reg = ALERT_TYPE_MAP[item.alert_type]
        existing = existing_map.get(item.alert_type)
        if existing:
            existing.priority = item.priority
            existing.notify_in_app = item.notify_in_app
            existing.notify_email = item.notify_email
            existing.email_recipients = item.email_recipients
            existing.enabled = item.enabled
        else:
            db.add(AlertTypeSetting(
                user_id=user_id,
                alert_type=item.alert_type,
                category=reg["category"],
                priority=item.priority,
                notify_in_app=item.notify_in_app,
                notify_email=item.notify_email,
                email_recipients=item.email_recipients,
                enabled=item.enabled,
            ))

    db.commit()
    logger.info("alert_settings_saved", count=len(body.settings))
    return {"status": "saved", "count": len(body.settings)}


@router.patch("/{alert_type:path}")
@limiter.limit("20/minute")
async def toggle_alert_setting(
    request: Request,
    alert_type: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Quick toggle a single alert type on/off."""
    if alert_type not in ALERT_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown alert type: {alert_type}")

    reg = ALERT_TYPE_MAP[alert_type]
    existing = (
        db.query(AlertTypeSetting)
        .filter(
            AlertTypeSetting.user_id == user_id,
            AlertTypeSetting.alert_type == alert_type,
        )
        .first()
    )

    if existing:
        existing.enabled = not existing.enabled
        db.commit()
        return {"alert_type": alert_type, "enabled": existing.enabled}

    # WHY: First toggle on a never-saved type — create with defaults but disabled
    new_setting = AlertTypeSetting(
        user_id=user_id,
        alert_type=alert_type,
        category=reg["category"],
        priority=reg["default_priority"],
        enabled=False,
    )
    db.add(new_setting)
    db.commit()
    return {"alert_type": alert_type, "enabled": False}
