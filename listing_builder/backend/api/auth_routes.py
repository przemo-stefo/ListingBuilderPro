# backend/api/auth_routes.py
# Purpose: Auth endpoints — user info from JWT session
# NOT for: OAuth marketplace connections (that's oauth_routes.py)

from fastapi import APIRouter, Request, HTTPException
import structlog

from middleware.supabase_auth import get_user_id_from_jwt

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me")
async def get_me(request: Request):
    """Return current user info from JWT. Frontend uses to verify session."""
    user_id = get_user_id_from_jwt(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {"user_id": user_id}
