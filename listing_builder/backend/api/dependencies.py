# backend/api/dependencies.py
# Purpose: FastAPI dependencies for extracting user context from requests
# NOT for: Auth verification logic (that's middleware/)

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from config import settings
from services.stripe_service import validate_license


def get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by auth middleware).

    WHY dependency: Routes call this via Depends() to get the current user_id
    without importing middleware directly. Falls back to "default" for
    backward compatibility with API-key-only auth.
    """
    return getattr(request.state, "user_id", "default")


def require_admin(request: Request) -> str:
    """Verify the current user is an admin (email in ADMIN_EMAILS env var).

    WHY: Protects admin-only endpoints (cost dashboard) from regular users.
    Returns the admin email on success, raises 403 otherwise.
    """
    email = getattr(request.state, "user_email", "")
    if not email or email.lower() not in settings.admin_emails_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return email


def require_premium(request: Request, db: Session):
    """Check if request has valid premium license. Raises 402 if not.

    WHY: Premium-only endpoints (Expert Q&A, Ad Copy, Compliance, Export)
    have no free tier — license key required for any access.
    SECURITY: Server-side check — frontend PremiumGate is cosmetic only.
    """
    license_key = request.headers.get("X-License-Key", "")
    if license_key and validate_license(license_key, db):
        return
    raise HTTPException(
        status_code=402,
        detail="Ta funkcja wymaga planu Premium. Wykup subskrypcję!",
    )
