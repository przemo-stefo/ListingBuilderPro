# backend/api/competitors_routes.py
# Purpose: Mock competitors endpoint — price comparison, ratings, win/loss status
# NOT for: Real competitor data (swap to DB when scraping/API integrations arrive)

from fastapi import APIRouter, Query
from schemas import CompetitorsResponse, CompetitorItem
from typing import Optional

router = APIRouter(prefix="/api/competitors", tags=["Competitors"])

# In-memory mock data — 15 competitors across 5 marketplaces
MOCK_COMPETITORS: list[dict] = [
    {"id": "comp-001", "competitor_name": "TechGear Pro", "asin": "B09XYZ1234", "product_title": "Premium Wireless Headphones ANC", "marketplace": "Amazon", "their_price": 79.99, "our_price": 69.99, "price_difference": 10.00, "their_rating": 4.3, "their_reviews_count": 2847, "status": "winning", "last_checked": "2026-02-01T10:00:00Z"},
    {"id": "comp-002", "competitor_name": "SoundMax", "asin": "B09ABC5678", "product_title": "Wireless Bluetooth Headphones V5", "marketplace": "Amazon", "their_price": 54.99, "our_price": 69.99, "price_difference": -15.00, "their_rating": 4.5, "their_reviews_count": 5621, "status": "losing", "last_checked": "2026-02-01T10:00:00Z"},
    {"id": "comp-003", "competitor_name": "CableWorld", "asin": "B09DEF9012", "product_title": "USB-C to USB-C Cable 6ft Braided", "marketplace": "Amazon", "their_price": 12.99, "our_price": 12.99, "price_difference": 0.00, "their_rating": 4.1, "their_reviews_count": 8934, "status": "tied", "last_checked": "2026-02-01T09:30:00Z"},
    {"id": "comp-004", "competitor_name": "LeatherCraft Co", "asin": "EBAY-LC-001", "product_title": "Genuine Leather Bifold Wallet", "marketplace": "eBay", "their_price": 45.00, "our_price": 39.99, "price_difference": 5.01, "their_rating": 4.7, "their_reviews_count": 1203, "status": "winning", "last_checked": "2026-02-01T08:00:00Z"},
    {"id": "comp-005", "competitor_name": "WalletKing", "asin": "EBAY-WK-002", "product_title": "Slim RFID Blocking Wallet", "marketplace": "eBay", "their_price": 29.99, "our_price": 39.99, "price_difference": -10.00, "their_rating": 4.4, "their_reviews_count": 3456, "status": "losing", "last_checked": "2026-02-01T08:00:00Z"},
    {"id": "comp-006", "competitor_name": "HydroFlask Direct", "asin": "EBAY-HF-003", "product_title": "Insulated Water Bottle 32oz", "marketplace": "eBay", "their_price": 34.95, "our_price": 28.99, "price_difference": 5.96, "their_rating": 4.6, "their_reviews_count": 7821, "status": "winning", "last_checked": "2026-02-01T08:00:00Z"},
    {"id": "comp-007", "competitor_name": "BedLux Home", "asin": "WMT-BL-001", "product_title": "Premium Cotton Sheet Set Queen", "marketplace": "Walmart", "their_price": 59.99, "our_price": 49.99, "price_difference": 10.00, "their_rating": 4.2, "their_reviews_count": 1567, "status": "winning", "last_checked": "2026-02-01T11:00:00Z"},
    {"id": "comp-008", "competitor_name": "SleepWell", "asin": "WMT-SW-002", "product_title": "Organic Sateen Sheet Set", "marketplace": "Walmart", "their_price": 44.99, "our_price": 49.99, "price_difference": -5.00, "their_rating": 4.0, "their_reviews_count": 892, "status": "losing", "last_checked": "2026-02-01T11:00:00Z"},
    {"id": "comp-009", "competitor_name": "CookMaster", "asin": "WMT-CM-003", "product_title": "Ceramic Non-Stick Pan 12in", "marketplace": "Walmart", "their_price": 35.99, "our_price": 32.99, "price_difference": 3.00, "their_rating": 4.3, "their_reviews_count": 2341, "status": "winning", "last_checked": "2026-02-01T11:00:00Z"},
    {"id": "comp-010", "competitor_name": "CandleLove", "asin": "SHP-CL-001", "product_title": "Natural Soy Wax Candle Set", "marketplace": "Shopify", "their_price": 28.00, "our_price": 24.99, "price_difference": 3.01, "their_rating": 4.8, "their_reviews_count": 456, "status": "winning", "last_checked": "2026-02-01T07:00:00Z"},
    {"id": "comp-011", "competitor_name": "AromaHouse", "asin": "SHP-AH-002", "product_title": "Luxury Lavender Candle 8oz", "marketplace": "Shopify", "their_price": 22.50, "our_price": 24.99, "price_difference": -2.49, "their_rating": 4.6, "their_reviews_count": 789, "status": "losing", "last_checked": "2026-02-01T07:00:00Z"},
    {"id": "comp-012", "competitor_name": "DeskCraft", "asin": "SHP-DC-003", "product_title": "Bamboo Desktop Organizer", "marketplace": "Shopify", "their_price": 42.00, "our_price": 38.99, "price_difference": 3.01, "their_rating": 4.4, "their_reviews_count": 234, "status": "winning", "last_checked": "2026-02-01T07:00:00Z"},
    {"id": "comp-013", "competitor_name": "Outdoorowy Swiat", "asin": "ALG-OS-001", "product_title": "Plecak gorski 45L z pokrowcem", "marketplace": "Allegro", "their_price": 189.00, "our_price": 159.99, "price_difference": 29.01, "their_rating": 4.5, "their_reviews_count": 342, "status": "winning", "last_checked": "2026-02-01T12:00:00Z"},
    {"id": "comp-014", "competitor_name": "TrekkingPro", "asin": "ALG-TP-002", "product_title": "Plecak turystyczny 40L", "marketplace": "Allegro", "their_price": 139.00, "our_price": 159.99, "price_difference": -20.99, "their_rating": 4.2, "their_reviews_count": 567, "status": "losing", "last_checked": "2026-02-01T12:00:00Z"},
    {"id": "comp-015", "competitor_name": "NarzedziaMax", "asin": "ALG-NM-003", "product_title": "Zestaw narzedzi 150 elementow", "marketplace": "Allegro", "their_price": 249.00, "our_price": 219.99, "price_difference": 29.01, "their_rating": 4.1, "their_reviews_count": 189, "status": "winning", "last_checked": "2026-02-01T12:00:00Z"},
]


@router.get("", response_model=CompetitorsResponse)
async def get_competitors(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    search: Optional[str] = Query(None, description="Search competitor name or product title"),
):
    """
    List competitors with price comparison and rating data.
    Summary stats are computed from the FULL dataset (before filtering).
    """
    all_items = [CompetitorItem(**c) for c in MOCK_COMPETITORS]

    # Summary stats from full dataset
    winning_count = sum(1 for c in all_items if c.status == "winning")
    losing_count = sum(1 for c in all_items if c.status == "losing")
    avg_price_gap = round(sum(abs(c.price_difference) for c in all_items) / len(all_items), 2)

    # Apply filters for the table view
    filtered = all_items
    if marketplace:
        filtered = [c for c in filtered if c.marketplace == marketplace]
    if search:
        q = search.lower()
        filtered = [
            c for c in filtered
            if q in c.competitor_name.lower() or q in c.product_title.lower()
        ]

    return CompetitorsResponse(
        competitors=filtered,
        total=len(filtered),
        winning_count=winning_count,
        losing_count=losing_count,
        avg_price_gap=avg_price_gap,
    )
