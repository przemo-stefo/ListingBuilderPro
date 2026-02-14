# backend/services/stripe_service.py
# Purpose: Stripe Checkout session creation and webhook event handling
# NOT for: Database models or route definitions

import stripe
import structlog
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from config import settings
from models.subscription import Subscription

logger = structlog.get_logger()

# WHY: Set API key at module level — stripe lib uses global state
stripe.api_key = getattr(settings, "stripe_secret_key", "")

# WHY: Hardcoded success/cancel URLs — frontend handles ?payment=success|canceled
FRONTEND_URL = (
    "https://listing.feedmasters.org"
    if settings.is_production
    else "http://localhost:3000"
)


def _get_or_create_subscription(db: Session, user_id: str = "default") -> Subscription:
    """Get existing subscription row or create a free one."""
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        sub = Subscription(user_id=user_id)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


def get_subscription_status(db: Session, user_id: str = "default") -> Subscription:
    """Return current subscription state."""
    return _get_or_create_subscription(db, user_id)


def create_checkout_session(db: Session, user_id: str = "default") -> str:
    """
    Create a Stripe Checkout session and return the URL.

    Flow: creates/reuses Stripe customer → creates checkout → returns URL.
    """
    sub = _get_or_create_subscription(db, user_id)

    # WHY: Reuse Stripe customer to keep subscription history clean
    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            metadata={"user_id": user_id},
        )
        sub.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{FRONTEND_URL}?payment=success",
        cancel_url=f"{FRONTEND_URL}?payment=canceled",
        # WHY: Allow only one active subscription per customer
        subscription_data={"metadata": {"user_id": user_id}},
    )

    logger.info("stripe_checkout_created", session_id=session.id, user_id=user_id)
    return session.url


def create_portal_session(db: Session, user_id: str = "default") -> str:
    """Create a Stripe Customer Portal session for managing subscription."""
    sub = _get_or_create_subscription(db, user_id)

    if not sub.stripe_customer_id:
        raise ValueError("No Stripe customer — subscribe first")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=FRONTEND_URL,
    )
    return session.url


def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> str:
    """
    Verify Stripe webhook signature and process the event.

    Returns event type string for logging.
    WHY bytes+sig: Stripe requires raw body for signature verification.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        logger.warning("stripe_webhook_invalid_signature")
        raise ValueError("Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("stripe_webhook_received", event_type=event_type)

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data, db)
    elif event_type in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        _handle_subscription_change(data, db)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data, db)

    return event_type


def _handle_checkout_completed(session_data: dict, db: Session):
    """After successful checkout — link subscription to user."""
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")

    if not customer_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if not sub:
        logger.warning("stripe_no_subscription_row", customer_id=customer_id)
        return

    sub.stripe_subscription_id = subscription_id
    sub.status = "active"
    sub.tier = "premium"
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("stripe_subscription_activated", user_id=sub.user_id)


def _handle_subscription_change(sub_data: dict, db: Session):
    """Handle subscription updated/deleted events."""
    stripe_sub_id = sub_data.get("id")
    status = sub_data.get("status")  # active, past_due, canceled, unpaid
    cancel_at_period_end = sub_data.get("cancel_at_period_end", False)

    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if not sub:
        # WHY: Fallback — find by customer ID if subscription ID not yet saved
        customer_id = sub_data.get("customer")
        if customer_id:
            sub = db.query(Subscription).filter(
                Subscription.stripe_customer_id == customer_id
            ).first()

    if not sub:
        logger.warning("stripe_subscription_not_found", stripe_sub_id=stripe_sub_id)
        return

    sub.status = status
    sub.tier = "premium" if status == "active" else "free"
    sub.cancel_at_period_end = cancel_at_period_end
    sub.stripe_subscription_id = stripe_sub_id

    # WHY: Store period dates for frontend "expires on" display
    period_start = sub_data.get("current_period_start")
    period_end = sub_data.get("current_period_end")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    sub.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("stripe_subscription_updated", user_id=sub.user_id, status=status, tier=sub.tier)


def _handle_payment_failed(invoice_data: dict, db: Session):
    """Mark subscription as past_due on payment failure."""
    customer_id = invoice_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if sub:
        sub.status = "past_due"
        sub.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.warning("stripe_payment_failed", user_id=sub.user_id)
