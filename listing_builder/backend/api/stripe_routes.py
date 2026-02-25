# backend/api/stripe_routes.py
# Purpose: REST endpoints for Stripe license-key payment flow
# NOT for: Stripe API logic (see services/stripe_service.py)

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from schemas.subscription import (
    CheckoutRequest,
    CheckoutResponse,
    ValidateLicenseRequest,
    ValidateLicenseResponse,
    RecoverLicenseRequest,
    RecoverLicenseResponse,
    SessionLicenseResponse,
)
from services.stripe_service import (
    create_checkout_session,
    handle_webhook_event,
    validate_license,
    get_license_by_email,
    get_license_by_session,
    create_portal_session,
    get_subscription_status,
)
from typing import Optional

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/stripe", tags=["Stripe"])


def _get_email_from_jwt(request: Request) -> Optional[str]:
    """Extract email from Supabase JWT. Shared by subscription + portal endpoints.

    WHY reuse middleware: get_user_id_from_jwt handles ES256 (JWKS) + HS256 fallback.
    We call it to verify the token, then read email from request.state.
    """
    from middleware.supabase_auth import get_user_id_from_jwt

    user_id = get_user_id_from_jwt(request)
    if not user_id:
        return None
    return getattr(request.state, "user_email", None)


@router.post("/create-checkout", response_model=CheckoutResponse)
@limiter.limit("10/minute")
async def checkout(request: Request, body: CheckoutRequest):
    """Create Stripe Checkout session for monthly plan."""
    try:
        url = create_checkout_session(body.plan_type, body.email)
        return CheckoutResponse(checkout_url=url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Nieprawidłowy plan lub email")
    except Exception as e:
        logger.error("stripe_checkout_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
@limiter.limit("60/minute")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook receiver.
    WHY raw body: Stripe signature verification requires raw bytes.
    PUBLIC endpoint — Stripe authenticates via signature header.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        handle_webhook_event(payload, sig_header, db)
        return {"status": "ok"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        logger.error("stripe_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/validate-license", response_model=ValidateLicenseResponse)
@limiter.limit("30/minute")
async def validate(request: Request, body: ValidateLicenseRequest, db: Session = Depends(get_db)):
    """Validate a license key — returns tier."""
    is_valid = validate_license(body.license_key, db)
    return ValidateLicenseResponse(
        valid=is_valid,
        tier="premium" if is_valid else "free",
    )


@router.post("/recover-license", response_model=RecoverLicenseResponse)
@limiter.limit("5/minute")
async def recover(request: Request, body: RecoverLicenseRequest, db: Session = Depends(get_db)):
    """Recover license key by email address.

    WHY JWT required: Without auth, anyone who knows an email could steal
    a license key. JWT proves the caller owns the email they're querying.
    """
    jwt_email = _get_email_from_jwt(request)
    if not jwt_email:
        raise HTTPException(status_code=401, detail="Zaloguj się aby odzyskać klucz")
    if jwt_email.lower() != body.email.strip().lower():
        raise HTTPException(status_code=403, detail="Email nie pasuje do zalogowanego konta")

    key = get_license_by_email(body.email, db)
    if key:
        return RecoverLicenseResponse(found=True, license_key=key)
    return RecoverLicenseResponse(found=False)


@router.get("/session/{session_id}/license", response_model=SessionLicenseResponse)
@limiter.limit("10/minute")
async def session_license(request: Request, session_id: str, db: Session = Depends(get_db)):
    """Get license key after successful Stripe checkout redirect.

    WHY JWT required: Without auth, anyone with a session_id (leaked via
    browser history, referrer, logs) could steal the associated license key.
    JWT proves the caller is the same person who initiated checkout.
    """
    jwt_email = _get_email_from_jwt(request)
    if not jwt_email:
        raise HTTPException(status_code=401, detail="Zaloguj się aby pobrać klucz licencji")

    key = get_license_by_session(session_id, db)
    if key:
        return SessionLicenseResponse(license_key=key, status="ready")
    # WHY: Webhook may not have fired yet — tell frontend to poll
    return SessionLicenseResponse(status="pending")


@router.get("/subscription")
@limiter.limit("30/minute")
async def subscription_status(request: Request, db: Session = Depends(get_db)):
    """Get current user's subscription status (plan, renewal date)."""
    email = _get_email_from_jwt(request)
    if not email:
        return {"plan": "free", "status": "active", "customer_id": None, "renewal_date": None}

    return get_subscription_status(email, db)


@router.post("/portal-session")
@limiter.limit("5/minute")
async def portal_session(request: Request, db: Session = Depends(get_db)):
    """Create Stripe Customer Portal session — manage billing, cancel, invoices."""
    email = _get_email_from_jwt(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    status = get_subscription_status(email, db)
    if not status.get("customer_id"):
        raise HTTPException(status_code=400, detail="Brak aktywnej subskrypcji Stripe")

    try:
        url = create_portal_session(status["customer_id"])
        return {"portal_url": url}
    except Exception as e:
        logger.error("stripe_portal_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create portal session")
