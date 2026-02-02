# backend/api/inventory_routes.py
# Purpose: Mock inventory endpoint — stock levels, reorder points, supply days
# NOT for: Real inventory data (swap to DB when warehouse integrations arrive)

from fastapi import APIRouter, Query
from schemas import InventoryResponse, InventoryItem
from typing import Optional

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

# In-memory mock data — 15 inventory items across 5 marketplaces
MOCK_INVENTORY: list[dict] = [
    {"id": "inv-001", "sku": "AMZ-001", "product_title": "Wireless Bluetooth Headphones Pro", "marketplace": "Amazon", "quantity": 342, "reorder_point": 100, "days_of_supply": 45, "status": "in_stock", "unit_cost": 22.50, "total_value": 7695.00, "last_restocked": "2026-01-15T10:00:00Z"},
    {"id": "inv-002", "sku": "AMZ-002", "product_title": "USB-C Fast Charging Cable 6ft", "marketplace": "Amazon", "quantity": 89, "reorder_point": 200, "days_of_supply": 12, "status": "low_stock", "unit_cost": 3.20, "total_value": 284.80, "last_restocked": "2026-01-20T14:00:00Z"},
    {"id": "inv-003", "sku": "AMZ-003", "product_title": "Portable Phone Charger 10000mAh", "marketplace": "Amazon", "quantity": 0, "reorder_point": 50, "days_of_supply": 0, "status": "out_of_stock", "unit_cost": 15.00, "total_value": 0.00, "last_restocked": "2025-12-10T09:00:00Z"},
    {"id": "inv-004", "sku": "EBY-001", "product_title": "Vintage Leather Wallet Men", "marketplace": "eBay", "quantity": 156, "reorder_point": 50, "days_of_supply": 62, "status": "in_stock", "unit_cost": 12.00, "total_value": 1872.00, "last_restocked": "2026-01-10T08:30:00Z"},
    {"id": "inv-005", "sku": "EBY-002", "product_title": "Stainless Steel Water Bottle 32oz", "marketplace": "eBay", "quantity": 23, "reorder_point": 75, "days_of_supply": 8, "status": "low_stock", "unit_cost": 8.50, "total_value": 195.50, "last_restocked": "2026-01-05T11:00:00Z"},
    {"id": "inv-006", "sku": "EBY-003", "product_title": "Retro Sunglasses Unisex", "marketplace": "eBay", "quantity": 567, "reorder_point": 100, "days_of_supply": 120, "status": "overstock", "unit_cost": 4.75, "total_value": 2693.25, "last_restocked": "2026-01-25T16:00:00Z"},
    {"id": "inv-007", "sku": "WMT-001", "product_title": "Organic Cotton Bed Sheets Queen", "marketplace": "Walmart", "quantity": 201, "reorder_point": 80, "days_of_supply": 38, "status": "in_stock", "unit_cost": 18.00, "total_value": 3618.00, "last_restocked": "2026-01-18T10:30:00Z"},
    {"id": "inv-008", "sku": "WMT-002", "product_title": "Non-Stick Frying Pan 12 inch", "marketplace": "Walmart", "quantity": 0, "reorder_point": 60, "days_of_supply": 0, "status": "out_of_stock", "unit_cost": 11.00, "total_value": 0.00, "last_restocked": "2025-12-28T13:00:00Z"},
    {"id": "inv-009", "sku": "WMT-003", "product_title": "Kitchen Knife Set 8-Piece", "marketplace": "Walmart", "quantity": 78, "reorder_point": 40, "days_of_supply": 30, "status": "in_stock", "unit_cost": 25.00, "total_value": 1950.00, "last_restocked": "2026-01-22T09:00:00Z"},
    {"id": "inv-010", "sku": "SHP-001", "product_title": "Handmade Soy Candle Lavender", "marketplace": "Shopify", "quantity": 445, "reorder_point": 100, "days_of_supply": 90, "status": "overstock", "unit_cost": 6.50, "total_value": 2892.50, "last_restocked": "2026-01-28T07:00:00Z"},
    {"id": "inv-011", "sku": "SHP-002", "product_title": "Minimalist Desk Organizer Wood", "marketplace": "Shopify", "quantity": 34, "reorder_point": 30, "days_of_supply": 15, "status": "in_stock", "unit_cost": 14.00, "total_value": 476.00, "last_restocked": "2026-01-12T15:00:00Z"},
    {"id": "inv-012", "sku": "SHP-003", "product_title": "Macrame Plant Hanger Set of 3", "marketplace": "Shopify", "quantity": 12, "reorder_point": 25, "days_of_supply": 5, "status": "low_stock", "unit_cost": 7.00, "total_value": 84.00, "last_restocked": "2026-01-08T10:00:00Z"},
    {"id": "inv-013", "sku": "ALG-001", "product_title": "Plecak turystyczny 40L wodoodporny", "marketplace": "Allegro", "quantity": 88, "reorder_point": 30, "days_of_supply": 44, "status": "in_stock", "unit_cost": 45.00, "total_value": 3960.00, "last_restocked": "2026-01-14T12:00:00Z"},
    {"id": "inv-014", "sku": "ALG-002", "product_title": "Zestaw narzedzi domowych 120 elementow", "marketplace": "Allegro", "quantity": 0, "reorder_point": 20, "days_of_supply": 0, "status": "out_of_stock", "unit_cost": 65.00, "total_value": 0.00, "last_restocked": "2025-12-20T14:00:00Z"},
    {"id": "inv-015", "sku": "ALG-003", "product_title": "Lampa biurkowa LED regulowana", "marketplace": "Allegro", "quantity": 210, "reorder_point": 50, "days_of_supply": 70, "status": "in_stock", "unit_cost": 18.00, "total_value": 3780.00, "last_restocked": "2026-01-30T08:00:00Z"},
]


@router.get("", response_model=InventoryResponse)
async def get_inventory(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    status: Optional[str] = Query(None, description="Filter by stock status"),
    search: Optional[str] = Query(None, description="Search SKU or product title"),
):
    """
    List inventory items with stock levels and supply metrics.
    Summary stats are computed from the FULL dataset (before filtering).
    """
    all_items = [InventoryItem(**item) for item in MOCK_INVENTORY]

    # Summary stats from full dataset
    in_stock_count = sum(1 for i in all_items if i.status == "in_stock")
    low_stock_count = sum(1 for i in all_items if i.status == "low_stock")
    out_of_stock_count = sum(1 for i in all_items if i.status == "out_of_stock")
    total_value = round(sum(i.total_value for i in all_items), 2)

    # Apply filters for the table view
    filtered = all_items
    if marketplace:
        filtered = [i for i in filtered if i.marketplace == marketplace]
    if status:
        filtered = [i for i in filtered if i.status == status]
    if search:
        q = search.lower()
        filtered = [
            i for i in filtered
            if q in i.sku.lower() or q in i.product_title.lower()
        ]

    return InventoryResponse(
        items=filtered,
        total=len(filtered),
        in_stock_count=in_stock_count,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        total_value=total_value,
    )
