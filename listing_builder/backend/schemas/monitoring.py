# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/schemas/monitoring.py
# Purpose: Pydantic schemas for monitoring/alerts API request/response validation
# NOT for: ORM models, alert logic, or scheduling

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class AlertTypeEnum(str, Enum):
    PRICE_CHANGE = "price_change"
    BUY_BOX_LOST = "buy_box_lost"
    LOW_STOCK = "low_stock"
    LISTING_DEACTIVATED = "listing_deactivated"
    NEGATIVE_REVIEW = "negative_review"
    RETURN_SPIKE = "return_spike"
    COMPLIANCE_FAIL = "compliance_fail"


class SeverityEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MarketplaceEnum(str, Enum):
    ALLEGRO = "allegro"
    AMAZON = "amazon"
    KAUFLAND = "kaufland"
    EBAY = "ebay"


# ── Tracked Products ──

class TrackProductRequest(BaseModel):
    marketplace: MarketplaceEnum
    product_id: str = Field(..., min_length=1, max_length=500)
    product_url: Optional[str] = None
    product_title: Optional[str] = None
    poll_interval_hours: int = Field(default=6, ge=1, le=24)

    @field_validator("product_url")
    @classmethod
    def validate_url(cls, v):
        if v and not v.startswith("http"):
            raise ValueError("product_url must start with http")
        return v


class TrackedProductResponse(BaseModel):
    id: str
    marketplace: str
    product_id: str
    product_url: Optional[str]
    product_title: Optional[str]
    poll_interval_hours: int
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TrackedProductsListResponse(BaseModel):
    items: List[TrackedProductResponse]
    total: int


# ── Snapshots ──

class SnapshotResponse(BaseModel):
    id: str
    marketplace: str
    product_id: str
    ean: Optional[str]
    snapshot_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotsListResponse(BaseModel):
    items: List[SnapshotResponse]
    total: int


# ── Alert Configs ──

class AlertConfigCreate(BaseModel):
    alert_type: AlertTypeEnum
    name: str = Field(..., min_length=1, max_length=200)
    enabled: bool = True
    threshold: Optional[float] = None
    marketplace: Optional[MarketplaceEnum] = None
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    cooldown_minutes: int = Field(default=60, ge=5, le=1440)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, v):
        if v and not v.startswith("http"):
            raise ValueError("webhook_url must start with http")
        return v


class AlertConfigResponse(BaseModel):
    id: str
    alert_type: str
    name: str
    enabled: bool
    threshold: Optional[float]
    marketplace: Optional[str]
    email: Optional[str]
    webhook_url: Optional[str]
    cooldown_minutes: int
    last_triggered: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertConfigsListResponse(BaseModel):
    items: List[AlertConfigResponse]
    total: int


# ── Alerts ──

class AlertResponse(BaseModel):
    id: str
    config_id: Optional[str]
    alert_type: str
    severity: str
    title: str
    message: str
    details: dict
    triggered_at: datetime
    acknowledged: bool
    acknowledged_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    items: List[AlertResponse]
    total: int


# ── Dashboard ──

class DashboardStats(BaseModel):
    tracked_products: int
    active_alerts: int
    alerts_today: int
    last_poll: Optional[datetime]
    marketplaces: dict  # {marketplace: count}
