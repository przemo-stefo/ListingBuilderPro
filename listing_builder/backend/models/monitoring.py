# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/models/monitoring.py
# Purpose: SQLAlchemy ORM models for product tracking, snapshots, alerts
# NOT for: Alert logic, scheduling, or API routes

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, JSON, DateTime, Text,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid


def _uuid():
    return str(uuid.uuid4())


class TrackedProduct(Base):
    """A product being monitored across a specific marketplace."""
    __tablename__ = "tracked_products"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(Text, nullable=False, index=True)
    marketplace = Column(String(50), nullable=False)
    product_id = Column(Text, nullable=False)
    product_url = Column(Text)
    product_title = Column(Text)
    poll_interval_hours = Column(Integer, default=6)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    snapshots = relationship(
        "MonitoringSnapshot",
        back_populates="tracked_product",
        cascade="all, delete-orphan",
        order_by="MonitoringSnapshot.created_at.desc()",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "marketplace", "product_id", name="uq_tracked_product"),
    )


class MonitoringSnapshot(Base):
    """Point-in-time capture of product price/stock/status."""
    __tablename__ = "monitoring_snapshots"

    id = Column(String(36), primary_key=True, default=_uuid)
    tracked_product_id = Column(
        String(36),
        ForeignKey("tracked_products.id", ondelete="CASCADE"),
        index=True,
    )
    marketplace = Column(String(50), nullable=False)
    product_id = Column(Text, nullable=False)
    ean = Column(String(14))
    # WHY JSONB: snapshot shape varies per marketplace (Amazon has buy_box_owner, Allegro doesn't)
    snapshot_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tracked_product = relationship("TrackedProduct", back_populates="snapshots")


class AlertConfig(Base):
    """User-defined rule: when to fire an alert."""
    __tablename__ = "alert_configs"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(Text, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    name = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    threshold = Column(Float)
    marketplace = Column(String(50))  # NULL = all marketplaces
    email = Column(Text)
    webhook_url = Column(Text)
    cooldown_minutes = Column(Integer, default=60)
    last_triggered = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    alerts = relationship(
        "Alert",
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="Alert.triggered_at.desc()",
    )


class Alert(Base):
    """A single triggered alert instance."""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    config_id = Column(
        String(36),
        ForeignKey("alert_configs.id", ondelete="CASCADE"),
        index=True,
    )
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, critical
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True))

    config = relationship("AlertConfig", back_populates="alerts")
