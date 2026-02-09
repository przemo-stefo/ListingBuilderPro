# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/monitoring_routes.py
# Purpose: API endpoints for product tracking, alerts config, alert history, dashboard
# NOT for: Alert evaluation logic, scheduling, or scraper implementations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from datetime import datetime, timedelta, timezone
import structlog

from database import get_db
from models.monitoring import TrackedProduct, MonitoringSnapshot, AlertConfig, Alert
from schemas.monitoring import (
    TrackProductRequest,
    TrackedProductResponse,
    TrackedProductsListResponse,
    SnapshotResponse,
    SnapshotsListResponse,
    AlertConfigCreate,
    AlertConfigResponse,
    AlertConfigsListResponse,
    AlertResponse,
    AlertsListResponse,
    DashboardStats,
)

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/monitoring", tags=["Monitoring & Alerts"])

# WHY hardcoded user_id: V1 is internal-only, no multi-tenant auth yet
DEFAULT_USER_ID = "internal"


# ── Product Tracking ──

@router.post("/track", response_model=TrackedProductResponse, status_code=201)
@limiter.limit("10/minute")
async def track_product(
    request: Request,
    body: TrackProductRequest,
    db: Session = Depends(get_db),
):
    """Start monitoring a product on a marketplace."""
    existing = (
        db.query(TrackedProduct)
        .filter(
            TrackedProduct.user_id == DEFAULT_USER_ID,
            TrackedProduct.marketplace == body.marketplace.value,
            TrackedProduct.product_id == body.product_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Product already tracked")

    product = TrackedProduct(
        user_id=DEFAULT_USER_ID,
        marketplace=body.marketplace.value,
        product_id=body.product_id,
        product_url=body.product_url,
        product_title=body.product_title,
        poll_interval_hours=body.poll_interval_hours,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    logger.info("product_tracked", marketplace=body.marketplace.value, product_id=body.product_id)
    return product


@router.get("/tracked", response_model=TrackedProductsListResponse)
async def list_tracked_products(
    marketplace: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all tracked products."""
    query = db.query(TrackedProduct).filter(TrackedProduct.user_id == DEFAULT_USER_ID)
    if marketplace:
        query = query.filter(TrackedProduct.marketplace == marketplace)

    total = query.count()
    items = query.order_by(TrackedProduct.created_at.desc()).offset(offset).limit(limit).all()
    return TrackedProductsListResponse(items=items, total=total)


@router.delete("/track/{product_id}")
async def untrack_product(product_id: str, db: Session = Depends(get_db)):
    """Stop tracking a product. Deletes snapshots via CASCADE."""
    product = (
        db.query(TrackedProduct)
        .filter(TrackedProduct.id == product_id, TrackedProduct.user_id == DEFAULT_USER_ID)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Tracked product not found")

    db.delete(product)
    db.commit()
    return {"status": "deleted", "id": product_id}


@router.patch("/track/{product_id}/toggle")
async def toggle_tracking(product_id: str, db: Session = Depends(get_db)):
    """Enable/disable polling for a tracked product."""
    product = (
        db.query(TrackedProduct)
        .filter(TrackedProduct.id == product_id, TrackedProduct.user_id == DEFAULT_USER_ID)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Tracked product not found")

    product.enabled = not product.enabled
    db.commit()
    return {"id": product_id, "enabled": product.enabled}


# ── Snapshots ──

@router.get("/snapshots/{tracked_id}", response_model=SnapshotsListResponse)
async def get_snapshots(
    tracked_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get price/stock history for a tracked product."""
    query = (
        db.query(MonitoringSnapshot)
        .filter(MonitoringSnapshot.tracked_product_id == tracked_id)
    )
    total = query.count()
    items = query.order_by(MonitoringSnapshot.created_at.desc()).offset(offset).limit(limit).all()
    return SnapshotsListResponse(items=items, total=total)


# ── Alert Configs ──

@router.post("/alerts/config", response_model=AlertConfigResponse, status_code=201)
@limiter.limit("10/minute")
async def create_alert_config(
    request: Request,
    body: AlertConfigCreate,
    db: Session = Depends(get_db),
):
    """Create an alert rule."""
    config = AlertConfig(
        user_id=DEFAULT_USER_ID,
        alert_type=body.alert_type.value,
        name=body.name,
        enabled=body.enabled,
        threshold=body.threshold,
        marketplace=body.marketplace.value if body.marketplace else None,
        email=body.email,
        webhook_url=body.webhook_url,
        cooldown_minutes=body.cooldown_minutes,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/alerts/configs", response_model=AlertConfigsListResponse)
async def list_alert_configs(
    alert_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all alert configs."""
    query = db.query(AlertConfig).filter(AlertConfig.user_id == DEFAULT_USER_ID)
    if alert_type:
        query = query.filter(AlertConfig.alert_type == alert_type)

    total = query.count()
    items = query.order_by(AlertConfig.created_at.desc()).all()
    return AlertConfigsListResponse(items=items, total=total)


@router.delete("/alerts/config/{config_id}")
async def delete_alert_config(config_id: str, db: Session = Depends(get_db)):
    """Delete an alert config and its alert history."""
    config = (
        db.query(AlertConfig)
        .filter(AlertConfig.id == config_id, AlertConfig.user_id == DEFAULT_USER_ID)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    db.delete(config)
    db.commit()
    return {"status": "deleted", "id": config_id}


@router.patch("/alerts/config/{config_id}/toggle")
async def toggle_alert_config(config_id: str, db: Session = Depends(get_db)):
    """Enable/disable an alert config."""
    config = (
        db.query(AlertConfig)
        .filter(AlertConfig.id == config_id, AlertConfig.user_id == DEFAULT_USER_ID)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    config.enabled = not config.enabled
    db.commit()
    return {"id": config_id, "enabled": config.enabled}


# ── Alert History ──

@router.get("/alerts", response_model=AlertsListResponse)
async def list_alerts(
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get alert history."""
    from services.alert_service import get_alert_service
    svc = get_alert_service()
    alerts, total = svc.get_alerts(db, DEFAULT_USER_ID, limit, offset, severity)
    return AlertsListResponse(items=alerts, total=total)


@router.patch("/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    from services.alert_service import get_alert_service
    svc = get_alert_service()
    alert = svc.acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": alert_id, "acknowledged": True}


# ── Scheduler Status ──

@router.get("/status")
async def scheduler_status():
    """Show scheduler and alert service health. Used to verify startup."""
    from services.monitor_scheduler import _scheduler
    from services.alert_service import get_alert_service

    scheduler_info = {"running": False, "jobs": []}
    if _scheduler:
        scheduler_info["running"] = _scheduler.running
        for job in _scheduler.get_jobs():
            scheduler_info["jobs"].append({
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })

    try:
        svc = get_alert_service()
        alert_ready = svc is not None
    except Exception:
        alert_ready = False

    return {
        "scheduler": scheduler_info,
        "alert_service": alert_ready,
    }


# ── Dashboard ──

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: Session = Depends(get_db)):
    """Aggregated monitoring dashboard stats."""
    tracked_count = (
        db.query(sa_func.count(TrackedProduct.id))
        .filter(TrackedProduct.user_id == DEFAULT_USER_ID)
        .scalar()
    )

    active_configs = (
        db.query(sa_func.count(AlertConfig.id))
        .filter(AlertConfig.user_id == DEFAULT_USER_ID, AlertConfig.enabled == True)
        .scalar()
    )

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = (
        db.query(sa_func.count(Alert.id))
        .join(AlertConfig)
        .filter(AlertConfig.user_id == DEFAULT_USER_ID, Alert.triggered_at >= today_start)
        .scalar()
    )

    last_snapshot = (
        db.query(MonitoringSnapshot.created_at)
        .join(TrackedProduct)
        .filter(TrackedProduct.user_id == DEFAULT_USER_ID)
        .order_by(MonitoringSnapshot.created_at.desc())
        .first()
    )

    # Count tracked products per marketplace
    marketplace_counts = (
        db.query(TrackedProduct.marketplace, sa_func.count(TrackedProduct.id))
        .filter(TrackedProduct.user_id == DEFAULT_USER_ID)
        .group_by(TrackedProduct.marketplace)
        .all()
    )

    return DashboardStats(
        tracked_products=tracked_count or 0,
        active_alerts=active_configs or 0,
        alerts_today=alerts_today or 0,
        last_poll=last_snapshot[0] if last_snapshot else None,
        marketplaces={m: c for m, c in marketplace_counts},
    )
