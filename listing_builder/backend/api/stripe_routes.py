# backend/api/stripe_routes.py
# Purpose: REST endpoints for Stripe subscription management
# NOT for: Stripe API logic (see services/stripe_service.py)

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from schemas.subscription import (
    SubscriptionStatusResponse,
    CheckoutSessionResponse,
    PortalSessionResponse,
)
from services.stripe_service import (
    get_subscription_status,
    create_checkout_session,
    create_portal_session,
    handle_webhook_event,
)

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/stripe", tags=["Stripe"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(db: Session = Depends(get_db)):
    """Get current subscription tier and status."""
    sub = get_subscription_status(db)
    return SubscriptionStatusResponse(
        tier=sub.tier,
        status=sub.status,
        stripe_customer_id=sub.stripe_customer_id,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
    )


@router.post("/checkout", response_model=CheckoutSessionResponse)
@limiter.limit("10/minute")
async def checkout(request: Request, db: Session = Depends(get_db)):
    """Create a Stripe Checkout session and return the URL."""
    try:
        url = create_checkout_session(db)
        return CheckoutSessionResponse(checkout_url=url)
    except Exception as e:
        logger.error("stripe_checkout_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal", response_model=PortalSessionResponse)
@limiter.limit("10/minute")
async def portal(request: Request, db: Session = Depends(get_db)):
    """Create a Stripe Customer Portal session for managing subscription."""
    try:
        url = create_portal_session(db)
        return PortalSessionResponse(portal_url=url)
    except Exception as e:
        logger.error("stripe_portal_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook receiver.

    WHY raw body: Stripe signature verification requires the raw bytes,
    not parsed JSON. This endpoint is PUBLIC (no API key) — Stripe
    authenticates via the webhook signature header.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event_type = handle_webhook_event(payload, sig_header, db)
        return {"status": "ok", "event_type": event_type}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        logger.error("stripe_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")
