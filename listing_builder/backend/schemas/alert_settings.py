# backend/schemas/alert_settings.py
# Purpose: Pydantic schemas for Sellerboard-style alert settings
# NOT for: ORM models, registry data, or route logic

from pydantic import BaseModel, Field
from typing import List


class AlertTypeInfo(BaseModel):
    """Registry entry returned by GET /alert-settings/types."""
    type: str
    label: str
    category: str
    data_source: str
    default_priority: str
    active: bool  # WHY: True if the alert works now (no SP-API needed)


class AlertTypeSetting(BaseModel):
    """Single alert type setting as saved by user."""
    alert_type: str = Field(..., max_length=80)
    priority: str = Field(default="minor", pattern="^(minor|major|critical)$")
    notify_in_app: bool = True
    notify_email: bool = False
    email_recipients: List[str] = Field(default=[], max_length=10)
    enabled: bool = True


class AlertSettingsBulkUpdate(BaseModel):
    """Bulk upsert payload from the frontend Save button."""
    # WHY max 50: Registry has 24 types — 50 is generous ceiling to prevent abuse
    settings: List[AlertTypeSetting] = Field(..., max_length=50)


class AlertSettingResponse(AlertTypeSetting):
    """What the user gets back — setting merged with registry info."""
    label: str
    category: str
    data_source: str
    active: bool

    class Config:
        from_attributes = True
