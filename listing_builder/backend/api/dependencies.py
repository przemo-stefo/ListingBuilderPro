# backend/api/dependencies.py
# Purpose: FastAPI dependencies for extracting user context from requests
# NOT for: Auth verification logic (that's middleware/)

from fastapi import Request


def get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by auth middleware).

    WHY dependency: Routes call this via Depends() to get the current user_id
    without importing middleware directly. Falls back to "default" for
    backward compatibility with API-key-only auth.
    """
    return getattr(request.state, "user_id", "default")
