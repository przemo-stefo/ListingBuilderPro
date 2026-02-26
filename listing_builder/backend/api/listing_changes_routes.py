# backend/api/listing_changes_routes.py
# Purpose: GET endpoints for listing change history (timeline view)
# NOT for: Change detection logic (that's listing_diff_service + monitor_scheduler)

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from database import get_db
from api.dependencies import require_user_id
from models.listing_change import ListingChange

router = APIRouter(prefix="/api/monitoring", tags=["Listing Changes"])


@router.get("/listing-changes")
def get_listing_changes(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
    product_id: str | None = Query(None),
    change_type: Literal["title", "bullets", "description", "images", "price", "brand"] | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Paginated listing changes for the current user."""
    q = db.query(ListingChange).filter(ListingChange.user_id == user_id)

    if product_id:
        q = q.filter(ListingChange.product_id == product_id)
    if change_type:
        q = q.filter(ListingChange.change_type == change_type)

    # WHY: Fetch limit+1 to detect "has more" without a separate COUNT query
    items = (
        q.order_by(ListingChange.detected_at.desc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )
    has_more = len(items) > limit
    items = items[:limit]

    return {
        "items": [_serialize(c) for c in items],
        "has_more": has_more,
        "limit": limit,
        "offset": offset,
    }


@router.get("/listing-changes/summary")
def get_listing_changes_summary(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Per-product summary: change count + last change timestamp."""
    rows = (
        db.query(
            ListingChange.product_id,
            ListingChange.marketplace,
            sql_func.count(ListingChange.id).label("change_count"),
            sql_func.max(ListingChange.detected_at).label("last_change"),
        )
        .filter(ListingChange.user_id == user_id)
        .group_by(ListingChange.product_id, ListingChange.marketplace)
        .all()
    )

    return {
        "items": [
            {
                "product_id": r.product_id,
                "marketplace": r.marketplace,
                "change_count": r.change_count,
                "last_change": r.last_change.isoformat() if r.last_change else None,
            }
            for r in rows
        ]
    }


@router.get("/listing-changes/{change_id}")
def get_listing_change_detail(
    change_id: str,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Single listing change by ID."""
    change = (
        db.query(ListingChange)
        .filter(ListingChange.id == change_id, ListingChange.user_id == user_id)
        .first()
    )
    if not change:
        raise HTTPException(status_code=404, detail="Listing change not found")
    return _serialize(change)


def _serialize(c: ListingChange) -> dict:
    return {
        "id": c.id,
        "tracked_product_id": c.tracked_product_id,
        "user_id": c.user_id,
        "marketplace": c.marketplace,
        "product_id": c.product_id,
        "change_type": c.change_type,
        "field_name": c.field_name,
        "old_value": c.old_value,
        "new_value": c.new_value,
        "detected_at": c.detected_at.isoformat() if c.detected_at else None,
    }
