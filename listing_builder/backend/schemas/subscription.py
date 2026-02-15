# backend/schemas/subscription.py
# Purpose: Pydantic request/response models for Stripe license-key endpoints
# NOT for: Database models or Stripe API calls

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class CheckoutRequest(BaseModel):
    """Request to create Stripe Checkout session."""
    plan_type: str = Field(default="monthly", pattern="^monthly$")
    email: EmailStr


class CheckoutResponse(BaseModel):
    """Stripe Checkout session URL."""
    checkout_url: str


class ValidateLicenseRequest(BaseModel):
    """Validate a license key."""
    license_key: str = Field(..., min_length=10)


class ValidateLicenseResponse(BaseModel):
    """License validation result."""
    valid: bool
    tier: str = "free"


class RecoverLicenseRequest(BaseModel):
    """Recover license key by email."""
    email: EmailStr


class RecoverLicenseResponse(BaseModel):
    """License recovery result — key only shown if found."""
    found: bool
    license_key: Optional[str] = None


class SessionLicenseResponse(BaseModel):
    """License key from a checkout session."""
    license_key: Optional[str] = None
    status: str = "pending"
