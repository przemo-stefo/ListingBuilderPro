# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/alert_service.py
# Purpose: Alert evaluation, creation, cooldown, and delivery (email/webhook)
# NOT for: Scheduling, scraping, or API routes

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
import httpx
import structlog

from models.monitoring import AlertConfig, Alert

logger = structlog.get_logger()


class AlertService:
    """Evaluates monitoring data against alert configs, fires notifications."""

    def __init__(self, db_session_factory):
        # WHY factory not session: scheduler runs in background thread,
        # needs fresh sessions per poll cycle
        self._session_factory = db_session_factory

    def check_price_change(
        self,
        db: Session,
        user_id: str,
        marketplace: str,
        product_id: str,
        old_price: float,
        new_price: float,
    ) -> Optional[Alert]:
        """Fire alert if price changed beyond threshold."""
        if old_price <= 0:
            return None

        pct_change = abs(new_price - old_price) / old_price * 100
        configs = self._get_matching_configs(db, user_id, "price_change", marketplace)

        for config in configs:
            threshold = config.threshold or 5.0
            if pct_change >= threshold:
                direction = "increased" if new_price > old_price else "decreased"
                return self._fire_alert(
                    db=db,
                    config=config,
                    severity="warning" if pct_change < 15 else "critical",
                    title=f"Price {direction} {pct_change:.1f}% on {marketplace}",
                    message=(
                        f"Product {product_id}: {old_price:.2f} → {new_price:.2f} "
                        f"({direction} {pct_change:.1f}%)"
                    ),
                    details={
                        "marketplace": marketplace,
                        "product_id": product_id,
                        "old_price": old_price,
                        "new_price": new_price,
                        "pct_change": round(pct_change, 2),
                    },
                )
        return None

    def check_buy_box_lost(
        self,
        db: Session,
        user_id: str,
        product_id: str,
        old_owner: str,
        new_owner: str,
    ) -> Optional[Alert]:
        """Fire alert when Buy Box ownership changes (Amazon)."""
        if old_owner == new_owner:
            return None

        configs = self._get_matching_configs(db, user_id, "buy_box_lost", "amazon")
        for config in configs:
            return self._fire_alert(
                db=db,
                config=config,
                severity="critical",
                title=f"Buy Box lost on ASIN {product_id}",
                message=f"Buy Box owner changed: {old_owner} → {new_owner}",
                details={
                    "product_id": product_id,
                    "old_owner": old_owner,
                    "new_owner": new_owner,
                },
            )
        return None

    def check_stock_level(
        self,
        db: Session,
        user_id: str,
        marketplace: str,
        product_id: str,
        old_stock: int,
        new_stock: int,
    ) -> Optional[Alert]:
        """Fire alert when stock drops to zero or below threshold."""
        configs = self._get_matching_configs(db, user_id, "low_stock", marketplace)
        for config in configs:
            threshold = int(config.threshold or 0)
            if new_stock <= threshold and old_stock > threshold:
                return self._fire_alert(
                    db=db,
                    config=config,
                    severity="critical" if new_stock == 0 else "warning",
                    title=f"Low stock on {marketplace}: {product_id}",
                    message=f"Stock dropped from {old_stock} to {new_stock}",
                    details={
                        "marketplace": marketplace,
                        "product_id": product_id,
                        "old_stock": old_stock,
                        "new_stock": new_stock,
                    },
                )
        return None

    def check_listing_deactivated(
        self,
        db: Session,
        user_id: str,
        marketplace: str,
        product_id: str,
        was_active: bool,
        is_active: bool,
    ) -> Optional[Alert]:
        """Fire alert when a listing goes from active to inactive."""
        if not was_active or is_active:
            return None

        configs = self._get_matching_configs(db, user_id, "listing_deactivated", marketplace)
        for config in configs:
            return self._fire_alert(
                db=db,
                config=config,
                severity="critical",
                title=f"Listing deactivated on {marketplace}",
                message=f"Product {product_id} is no longer active",
                details={"marketplace": marketplace, "product_id": product_id},
            )
        return None

    def get_alerts(
        self,
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
    ) -> tuple:
        """Get alert history for a user. Returns (alerts, total_count)."""
        query = (
            db.query(Alert)
            .join(AlertConfig)
            .filter(AlertConfig.user_id == user_id)
        )
        if severity:
            query = query.filter(Alert.severity == severity)

        total = query.count()
        alerts = (
            query
            .order_by(Alert.triggered_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return alerts, total

    def acknowledge_alert(self, db: Session, alert_id: str) -> Optional[Alert]:
        """Mark an alert as acknowledged."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now(timezone.utc)
            db.commit()
        return alert

    # ── Internal helpers ──

    def _get_matching_configs(
        self, db: Session, user_id: str, alert_type: str, marketplace: str,
    ) -> List[AlertConfig]:
        """Find enabled configs matching type + marketplace."""
        return (
            db.query(AlertConfig)
            .filter(
                AlertConfig.user_id == user_id,
                AlertConfig.alert_type == alert_type,
                AlertConfig.enabled == True,
                # Match specific marketplace OR configs with no marketplace filter
                (AlertConfig.marketplace == marketplace) | (AlertConfig.marketplace == None),
            )
            .all()
        )

    def _fire_alert(
        self,
        db: Session,
        config: AlertConfig,
        severity: str,
        title: str,
        message: str,
        details: dict,
    ) -> Optional[Alert]:
        """Create alert record if cooldown has passed, then deliver."""
        now = datetime.now(timezone.utc)

        # WHY cooldown: prevent alert spam during volatile price periods
        if config.last_triggered:
            cooldown_end = config.last_triggered + timedelta(minutes=config.cooldown_minutes)
            if now < cooldown_end:
                logger.debug("alert_cooldown", config_id=config.id, minutes_left=(cooldown_end - now).seconds // 60)
                return None

        alert = Alert(
            config_id=config.id,
            alert_type=config.alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details,
        )
        db.add(alert)
        config.last_triggered = now
        db.commit()
        db.refresh(alert)

        logger.info("alert_fired", alert_id=alert.id, type=config.alert_type, severity=severity)

        # Deliver notification (non-blocking — failure doesn't roll back alert)
        self._deliver(config, alert)
        return alert

    def _deliver(self, config: AlertConfig, alert: Alert) -> None:
        """Send alert via webhook. Email delivery is a future enhancement."""
        if config.webhook_url:
            try:
                httpx.post(
                    config.webhook_url,
                    json={
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "title": alert.title,
                        "message": alert.message,
                        "details": alert.details,
                        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
                    },
                    timeout=10.0,
                )
                logger.info("webhook_delivered", url=config.webhook_url[:50])
            except Exception as e:
                logger.error("webhook_failed", url=config.webhook_url[:50], error=str(e))


# ── Singleton ──

_alert_service: Optional[AlertService] = None


def init_alert_service(session_factory) -> AlertService:
    """Initialize singleton at app startup. Called from main.py."""
    global _alert_service
    _alert_service = AlertService(db_session_factory=session_factory)
    logger.info("alert_service_initialized")
    return _alert_service


def get_alert_service() -> AlertService:
    """Get the singleton AlertService instance."""
    if _alert_service is None:
        raise RuntimeError("AlertService not initialized. Call init_alert_service() at startup.")
    return _alert_service
