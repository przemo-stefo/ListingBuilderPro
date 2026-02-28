# backend/api/dependencies.py
# Purpose: FastAPI dependencies for extracting user context from requests
# NOT for: Auth verification logic (that's middleware/)

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from config import settings
from services.stripe_service import validate_license


def get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by auth middleware).

    DEPRECATED: Use require_user_id() instead — it rejects the unsafe "default"
    fallback. This function is kept only for backward compatibility with tests.
    No route should use Depends(get_user_id) — all routes should use
    Depends(require_user_id) which enforces real authentication.
    Remove once all references are cleaned up.
    """
    return getattr(request.state, "user_id", "default")


def require_user_id(request: Request) -> str:
    """Extract user_id and REJECT if it's the generic "default" fallback.

    WHY: Defense-in-depth for data-sensitive endpoints (OAuth, products,
    settings). Even if frontend JWT breaks, backend won't leak user data.
    "default" means no real user was identified — block access.
    """
    user_id = getattr(request.state, "user_id", "default")
    if user_id == "default":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    return user_id


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
