# backend/utils/validators.py
# Purpose: Shared input validation helpers for route handlers
# NOT for: Business logic validation (that's in services/)

from uuid import UUID
from fastapi import HTTPException


def validate_uuid(value: str, label: str = "ID") -> str:
    """Validate path parameter is a valid UUID. Returns the string unchanged.

    WHY: PostgreSQL UUID columns crash with 'invalid input syntax' when
    non-UUID strings reach the DB. Catch it early with a clear 400 error.
    """
    try:
        UUID(value)
        return value
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format — expected UUID")
