# backend/schemas/subscription.py
# Purpose: Pydantic request/response models for Stripe subscription endpoints
# NOT for: Database models or Stripe API calls

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status for the user."""
    tier: str = "free"
    status: str = "inactive"
    stripe_customer_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

    class Config:
        from_attributes = True


class CheckoutSessionResponse(BaseModel):
    """Stripe Checkout session URL."""
    checkout_url: str


class PortalSessionResponse(BaseModel):
    """Stripe Customer Portal URL for managing subscription."""
    portal_url: str
