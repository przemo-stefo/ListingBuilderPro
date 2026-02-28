# backend/middleware/supabase_auth.py
# Purpose: JWT verification for Supabase Auth — extracts user_id from token
# NOT for: API key auth (that's auth.py) or business logic

import jwt
import structlog
from typing import Optional
from fastapi import Request

from config import settings

logger = structlog.get_logger()

# WHY: Supabase signs auth JWTs with ES256 (asymmetric). JWKS client
# fetches public key from Supabase and caches it for verification.
_jwks_client = None


def _get_jwks_client():
    """Lazy-init JWKS client (cached, thread-safe in PyJWT 2.8+)."""
    global _jwks_client
    if _jwks_client is None and settings.supabase_url:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def get_user_id_from_jwt(request: Request) -> Optional[str]:
    """Extract user_id from Supabase JWT in Authorization header.

    WHY separate function: Used by both middleware (auth.py) and
    FastAPI dependency (dependencies.py) to avoid duplication.

    WHY two algorithms: Supabase migrated from HS256 to ES256 (2024+).
    Try ES256 via JWKS first (production), fall back to HS256 (legacy/test).

    Returns user_id (sub claim) or None if no valid JWT.
    Also sets request.state.user_email for admin checks.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Strip "Bearer "
    if not token:
        return None

    payload = None

    # WHY: Issuer must match Supabase project to reject tokens from other projects
    expected_issuer = f"{settings.supabase_url}/auth/v1" if settings.supabase_url else None

    # WHY ES256 first: Supabase production uses asymmetric keys (JWKS)
    jwks = _get_jwks_client()
    if jwks:
        try:
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
                issuer=expected_issuer,
            )
        except jwt.ExpiredSignatureError:
            logger.debug("jwt_expired_es256")
            return None  # WHY: Token IS expired — don't try HS256, just reject
        except jwt.InvalidTokenError:
            pass  # WHY: Might be HS256 token — fall through
        except Exception as e:
            logger.debug("jwks_error", error=str(e))
            pass  # WHY: JWKS fetch failed — try HS256 as fallback

    # WHY HS256 fallback: Legacy Supabase projects or test environments.
    # SECURITY NOTE: HS256 uses a symmetric secret — anyone with the JWT secret
    # can forge tokens. Remove this fallback once ES256 (JWKS) is confirmed
    # working reliably in production. Target removal: after 30 days of stable ES256.
    if payload is None and settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token, settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=expected_issuer,
            )
        except jwt.ExpiredSignatureError:
            logger.debug("jwt_expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug("jwt_invalid", error=str(e))
            return None

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id:
        # WHY: Store email on request state so require_admin() can check it
        request.state.user_email = payload.get("email", "")
        logger.debug("jwt_verified", user_id=user_id[:8])
    return user_id
