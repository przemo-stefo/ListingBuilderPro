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
)

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/stripe", tags=["Stripe"])


@router.post("/create-checkout", response_model=CheckoutResponse)
@limiter.limit("10/minute")
async def checkout(request: Request, body: CheckoutRequest, db: Session = Depends(get_db)):
    """Create Stripe Checkout session for monthly plan."""
    try:
        url = create_checkout_session(body.plan_type, body.email)
        return CheckoutResponse(checkout_url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    """Recover license key by email address."""
    key = get_license_by_email(body.email, db)
    if key:
        return RecoverLicenseResponse(found=True, license_key=key)
    return RecoverLicenseResponse(found=False)


@router.get("/session/{session_id}/license", response_model=SessionLicenseResponse)
@limiter.limit("30/minute")
async def session_license(request: Request, session_id: str, db: Session = Depends(get_db)):
    """Get license key after successful Stripe checkout redirect."""
    key = get_license_by_session(session_id, db)
    if key:
        return SessionLicenseResponse(license_key=key, status="ready")
    # WHY: Webhook may not have fired yet — tell frontend to poll
    return SessionLicenseResponse(status="pending")
