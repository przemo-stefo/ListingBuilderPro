# backend/api/listings_routes.py
# Purpose: CRUD endpoints for product listings with compliance status
# NOT for: Compliance evaluation logic (that's in compliance_routes.py)

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from database import get_db
from models.listing import Listing
from schemas import ListingCreate, ListingItem, ListingsResponse

router = APIRouter(prefix="/api/listings", tags=["Listings"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=ListingsResponse)
async def get_listings(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance status"),
    db: Session = Depends(get_db),
):
    """
    List all product listings with compliance status.
    Summary counts are computed from the FULL dataset (before filtering).
    """
    # WHY full-dataset counts: dashboard cards must stay consistent regardless of filters
    all_query = db.query(Listing)

    compliant_count = all_query.filter(Listing.compliance_status == "compliant").count()
    warning_count = all_query.filter(Listing.compliance_status == "warning").count()
    suppressed_count = all_query.filter(Listing.compliance_status == "suppressed").count()
    blocked_count = all_query.filter(Listing.compliance_status == "blocked").count()

    # Apply filters for the table view
    filtered = all_query
    if marketplace:
        filtered = filtered.filter(Listing.marketplace == marketplace)
    if compliance_status:
        filtered = filtered.filter(Listing.compliance_status == compliance_status)

    items = filtered.order_by(Listing.last_checked.desc()).all()

    # WHY manual serialization: last_checked is datetime, frontend expects ISO string
    listing_items = [
        ListingItem(
            id=str(row.id),
            sku=row.sku,
            title=row.title,
            marketplace=row.marketplace,
            compliance_status=row.compliance_status,
            issues_count=row.issues_count,
            last_checked=row.last_checked.isoformat() if row.last_checked else None,
        )
        for row in items
    ]

    return ListingsResponse(
        listings=listing_items,
        total=len(listing_items),
        compliant_count=compliant_count,
        warning_count=warning_count,
        suppressed_count=suppressed_count,
        blocked_count=blocked_count,
    )


@router.post("", response_model=ListingItem, status_code=201)
@limiter.limit("20/minute")
async def create_listing(
    request: Request,
    body: ListingCreate,
    db: Session = Depends(get_db),
):
    """Add a new product listing."""
    existing = db.query(Listing).filter(Listing.sku == body.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Listing with SKU {body.sku} already exists")

    listing = Listing(
        sku=body.sku,
        title=body.title,
        marketplace=body.marketplace,
        compliance_status=body.compliance_status.value,
        issues_count=body.issues_count,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    return ListingItem(
        id=str(listing.id),
        sku=listing.sku,
        title=listing.title,
        marketplace=listing.marketplace,
        compliance_status=listing.compliance_status,
        issues_count=listing.issues_count,
        last_checked=listing.last_checked.isoformat() if listing.last_checked else None,
    )


@router.delete("/{listing_id}")
async def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    """Remove a listing by ID."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(listing)
    db.commit()
    return {"status": "deleted", "id": listing_id}
