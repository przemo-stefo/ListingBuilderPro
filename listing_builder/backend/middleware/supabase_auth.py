# backend/middleware/supabase_auth.py
# Purpose: JWT verification for Supabase Auth — extracts user_id from token
# NOT for: API key auth (that's auth.py) or business logic

import jwt
import structlog
from typing import Optional
from fastapi import Request

from config import settings

logger = structlog.get_logger()


def get_user_id_from_jwt(request: Request) -> Optional[str]:
    """Extract user_id from Supabase JWT in Authorization header.

    WHY separate function: Used by both middleware (auth.py) and
    FastAPI dependency (dependencies.py) to avoid duplication.

    Returns user_id (sub claim) or None if no valid JWT.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Strip "Bearer "
    if not token or not settings.supabase_jwt_secret:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if user_id:
            logger.debug("jwt_verified", user_id=user_id[:8])
        return user_id
    except jwt.ExpiredSignatureError:
        logger.debug("jwt_expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug("jwt_invalid", error=str(e))
        return None
