# backend/api/listings_routes.py
# Purpose: Mock listings endpoint — compliance status across marketplaces
# NOT for: Real listing data (swap to DB when marketplace integrations arrive)

from fastapi import APIRouter, Query
from schemas import ListingsResponse, ListingItem
from typing import Optional

router = APIRouter(prefix="/api/listings", tags=["Listings"])

# In-memory mock data — 10 listings across 5 marketplaces
MOCK_LISTINGS: list[dict] = [
    {"sku": "AMZ-001", "title": "Wireless Bluetooth Headphones Pro", "marketplace": "Amazon", "compliance_status": "compliant", "issues_count": 0, "last_checked": "2026-02-01T10:30:00Z"},
    {"sku": "AMZ-002", "title": "USB-C Fast Charging Cable 6ft", "marketplace": "Amazon", "compliance_status": "warning", "issues_count": 2, "last_checked": "2026-02-01T09:15:00Z"},
    {"sku": "EBY-001", "title": "Vintage Leather Wallet Men", "marketplace": "eBay", "compliance_status": "compliant", "issues_count": 0, "last_checked": "2026-02-01T08:00:00Z"},
    {"sku": "EBY-002", "title": "Stainless Steel Water Bottle 32oz", "marketplace": "eBay", "compliance_status": "suppressed", "issues_count": 3, "last_checked": "2026-01-31T22:45:00Z"},
    {"sku": "WMT-001", "title": "Organic Cotton Bed Sheets Queen", "marketplace": "Walmart", "compliance_status": "compliant", "issues_count": 0, "last_checked": "2026-02-01T11:00:00Z"},
    {"sku": "WMT-002", "title": "Non-Stick Frying Pan 12 inch", "marketplace": "Walmart", "compliance_status": "blocked", "issues_count": 5, "last_checked": "2026-01-31T18:30:00Z"},
    {"sku": "SHP-001", "title": "Handmade Soy Candle Lavender", "marketplace": "Shopify", "compliance_status": "compliant", "issues_count": 0, "last_checked": "2026-02-01T07:20:00Z"},
    {"sku": "SHP-002", "title": "Minimalist Desk Organizer Wood", "marketplace": "Shopify", "compliance_status": "warning", "issues_count": 1, "last_checked": "2026-02-01T06:45:00Z"},
    {"sku": "ALG-001", "title": "Plecak turystyczny 40L wodoodporny", "marketplace": "Allegro", "compliance_status": "compliant", "issues_count": 0, "last_checked": "2026-02-01T12:00:00Z"},
    {"sku": "ALG-002", "title": "Zestaw narzedzi domowych 120 elementow", "marketplace": "Allegro", "compliance_status": "warning", "issues_count": 1, "last_checked": "2026-01-31T20:10:00Z"},
]


@router.get("", response_model=ListingsResponse)
async def get_listings(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance status"),
):
    """
    List all product listings with compliance status.
    Summary counts are computed from the FULL dataset (before filtering).
    """
    all_items = [ListingItem(**item) for item in MOCK_LISTINGS]

    # Summary counts from full dataset — dashboard cards stay consistent
    compliant_count = sum(1 for i in all_items if i.compliance_status == "compliant")
    warning_count = sum(1 for i in all_items if i.compliance_status == "warning")
    suppressed_count = sum(1 for i in all_items if i.compliance_status == "suppressed")
    blocked_count = sum(1 for i in all_items if i.compliance_status == "blocked")

    # Apply filters for the table view
    filtered = all_items
    if marketplace:
        filtered = [i for i in filtered if i.marketplace == marketplace]
    if compliance_status:
        filtered = [i for i in filtered if i.compliance_status == compliance_status]

    return ListingsResponse(
        listings=filtered,
        total=len(filtered),
        compliant_count=compliant_count,
        warning_count=warning_count,
        suppressed_count=suppressed_count,
        blocked_count=blocked_count,
    )
