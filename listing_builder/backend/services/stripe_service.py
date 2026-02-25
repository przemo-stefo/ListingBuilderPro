# backend/services/stripe_service.py
# Purpose: Stripe Checkout + license key generation/validation
# NOT for: Route definitions (see api/stripe_routes.py)

from __future__ import annotations

import secrets
import stripe
import structlog
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config import settings
from models.premium_license import PremiumLicense

logger = structlog.get_logger()

stripe.api_key = getattr(settings, "stripe_secret_key", "")

FRONTEND_URL = (
    "https://panel.octohelper.com"
    if settings.is_production
    else "http://localhost:3000"
)


def create_checkout_session(plan_type: str, email: str) -> str:
    """
    Create Stripe Checkout session for monthly subscription.
    Returns Checkout URL.
    """
    if plan_type != "monthly":
        raise ValueError(f"Invalid plan_type: {plan_type}. Only 'monthly' is available.")

    price_id = settings.stripe_price_monthly
    mode = "subscription"

    if not price_id:
        raise ValueError(f"Stripe price not configured for {plan_type}")

    session = stripe.checkout.Session.create(
        mode=mode,
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        # WHY: Mateusz (spotkanie 24.02) — promo 39 zł na start, kody tworzone w Stripe Dashboard
        allow_promotion_codes=True,
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/payment/cancel",
        metadata={"plan_type": plan_type},
    )

    logger.info("stripe_checkout_created", session_id=session.id, plan_type=plan_type)
    return session.url


def handle_checkout_completed(session_data: dict, db: Session):
    """
    After successful payment — generate license key and store in DB.
    Idempotent via UNIQUE constraint on stripe_checkout_session_id.
    """
    session_id = session_data.get("id")
    customer_id = session_data.get("customer")
    email = session_data.get("customer_email") or session_data.get("customer_details", {}).get("email", "")
    plan_type = session_data.get("metadata", {}).get("plan_type", "monthly")
    subscription_id = session_data.get("subscription")

    license_key = secrets.token_urlsafe(32)

    license_obj = PremiumLicense(
        email=email,
        license_key=license_key,
        stripe_customer_id=customer_id,
        stripe_checkout_session_id=session_id,
        stripe_subscription_id=subscription_id,
        plan_type=plan_type,
        status="active",
        expires_at=None,  # WHY: Lifetime = never expires, monthly managed by Stripe webhooks
    )

    try:
        db.add(license_obj)
        db.commit()
        logger.info("license_created", email=email, plan_type=plan_type, session_id=session_id)
    except IntegrityError:
        # WHY: Idempotent — Stripe may send duplicate webhooks
        db.rollback()
        logger.info("license_already_exists", session_id=session_id)


def handle_subscription_cancelled(sub_data: dict, db: Session):
    """Revoke license when monthly subscription is cancelled."""
    stripe_sub_id = sub_data.get("id")

    license_obj = db.query(PremiumLicense).filter(
        PremiumLicense.stripe_subscription_id == stripe_sub_id
    ).first()

    if not license_obj:
        logger.warning("subscription_cancel_no_license", stripe_sub_id=stripe_sub_id)
        return

    license_obj.status = "revoked"
    license_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("license_revoked", email=license_obj.email, stripe_sub_id=stripe_sub_id)


def validate_license(license_key: str, db: Session) -> bool:
    """Check if license key is active (not revoked/expired)."""
    if not license_key:
        return False

    license_obj = db.query(PremiumLicense).filter(
        PremiumLicense.license_key == license_key,
        PremiumLicense.status == "active",
    ).first()

    if not license_obj:
        return False

    # WHY: Monthly licenses can expire if Stripe says so
    if license_obj.expires_at and license_obj.expires_at < datetime.now(timezone.utc):
        license_obj.status = "expired"
        license_obj.updated_at = datetime.now(timezone.utc)
        db.commit()
        return False

    return True


def get_license_by_email(email: str, db: Session) -> str | None:
    """Recover active license key by email."""
    license_obj = db.query(PremiumLicense).filter(
        PremiumLicense.email == email,
        PremiumLicense.status == "active",
    ).order_by(PremiumLicense.created_at.desc()).first()

    return license_obj.license_key if license_obj else None


def get_license_by_session(session_id: str, db: Session) -> str | None:
    """Get license key by Stripe checkout session ID (for success page redirect)."""
    license_obj = db.query(PremiumLicense).filter(
        PremiumLicense.stripe_checkout_session_id == session_id,
    ).first()

    return license_obj.license_key if license_obj else None


def create_portal_session(customer_id: str) -> str:
    """Create Stripe Customer Portal session — user manages subscription/billing.

    WHY Customer Portal: Stripe handles cancellation, card updates, invoice history.
    We don't need to build billing management UI ourselves.
    """
    if not customer_id:
        raise ValueError("No Stripe customer ID found")

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{FRONTEND_URL}/account",
    )
    return session.url


def get_subscription_status(email: str, db: Session) -> dict:
    """Get subscription status by email — plan, renewal date, Stripe customer ID.

    WHY by email: PremiumLicense stores email (from Stripe checkout),
    which matches the user's Supabase email.
    """
    license_obj = db.query(PremiumLicense).filter(
        PremiumLicense.email == email,
        PremiumLicense.status == "active",
    ).order_by(PremiumLicense.created_at.desc()).first()

    if not license_obj:
        return {"plan": "free", "status": "active", "customer_id": None, "renewal_date": None}

    renewal_date = None
    if license_obj.stripe_subscription_id:
        try:
            sub = stripe.Subscription.retrieve(license_obj.stripe_subscription_id)
            renewal_date = sub.current_period_end
        except Exception:
            pass

    return {
        "plan": license_obj.plan_type or "monthly",
        "status": license_obj.status,
        "customer_id": license_obj.stripe_customer_id,
        "renewal_date": renewal_date,
        "email": license_obj.email,
    }


def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> str:
    """
    Verify Stripe webhook signature and process the event.
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
        handle_checkout_completed(data, db)
    elif event_type == "customer.subscription.deleted":
        handle_subscription_cancelled(data, db)

    return event_type
