# backend/api/analytics_routes.py
# Purpose: Mock analytics endpoint — revenue, orders, conversion, top products
# NOT for: Real analytics data (swap to DB when order tracking integrations arrive)

from fastapi import APIRouter, Query
from schemas import (
    AnalyticsResponse,
    MarketplaceRevenue,
    MonthlyRevenue,
    TopProduct,
)
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# In-memory mock data
MOCK_MARKETPLACE_REVENUE: list[dict] = [
    {"marketplace": "Amazon", "revenue": 84520.00, "orders": 1247, "percentage": 42.3},
    {"marketplace": "eBay", "revenue": 35890.00, "orders": 623, "percentage": 18.0},
    {"marketplace": "Walmart", "revenue": 41200.00, "orders": 534, "percentage": 20.6},
    {"marketplace": "Shopify", "revenue": 22750.00, "orders": 312, "percentage": 11.4},
    {"marketplace": "Allegro", "revenue": 15440.00, "orders": 198, "percentage": 7.7},
]

MOCK_MONTHLY_REVENUE: list[dict] = [
    {"month": "Sep 2025", "revenue": 28400.00, "orders": 389},
    {"month": "Oct 2025", "revenue": 32150.00, "orders": 445},
    {"month": "Nov 2025", "revenue": 45600.00, "orders": 612},
    {"month": "Dec 2025", "revenue": 52800.00, "orders": 723},
    {"month": "Jan 2026", "revenue": 38200.00, "orders": 498},
    {"month": "Feb 2026", "revenue": 2650.00, "orders": 47},
]

MOCK_TOP_PRODUCTS: list[dict] = [
    {"id": "tp-001", "title": "Wireless Bluetooth Headphones Pro", "marketplace": "Amazon", "revenue": 24500.00, "units_sold": 350, "conversion_rate": 8.2},
    {"id": "tp-002", "title": "Organic Cotton Bed Sheets Queen", "marketplace": "Walmart", "revenue": 18900.00, "units_sold": 315, "conversion_rate": 6.8},
    {"id": "tp-003", "title": "Vintage Leather Wallet Men", "marketplace": "eBay", "revenue": 12400.00, "units_sold": 310, "conversion_rate": 7.5},
    {"id": "tp-004", "title": "Handmade Soy Candle Lavender", "marketplace": "Shopify", "revenue": 11200.00, "units_sold": 448, "conversion_rate": 9.1},
    {"id": "tp-005", "title": "USB-C Fast Charging Cable 6ft", "marketplace": "Amazon", "revenue": 9800.00, "units_sold": 980, "conversion_rate": 5.4},
    {"id": "tp-006", "title": "Plecak turystyczny 40L wodoodporny", "marketplace": "Allegro", "revenue": 8600.00, "units_sold": 54, "conversion_rate": 4.2},
    {"id": "tp-007", "title": "Non-Stick Frying Pan 12 inch", "marketplace": "Walmart", "revenue": 7200.00, "units_sold": 240, "conversion_rate": 5.9},
    {"id": "tp-008", "title": "Minimalist Desk Organizer Wood", "marketplace": "Shopify", "revenue": 5400.00, "units_sold": 135, "conversion_rate": 6.1},
]


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    period: Optional[str] = Query(None, description="Time period: 7d, 30d, 90d, 12m"),
):
    """
    Revenue analytics with marketplace breakdown, monthly trend, and top products.
    Period param slices monthly data. Marketplace param filters everything.
    """
    marketplace_data = [MarketplaceRevenue(**m) for m in MOCK_MARKETPLACE_REVENUE]
    monthly_data = [MonthlyRevenue(**m) for m in MOCK_MONTHLY_REVENUE]
    top_products = [TopProduct(**p) for p in MOCK_TOP_PRODUCTS]

    # Period slices monthly data (keep most recent N months)
    if period == "7d":
        monthly_data = monthly_data[-1:]
    elif period == "30d":
        monthly_data = monthly_data[-2:]
    elif period == "90d":
        monthly_data = monthly_data[-3:]
    # "12m" or None = all data

    # Marketplace filter — narrow everything to one marketplace
    if marketplace:
        marketplace_data = [m for m in marketplace_data if m.marketplace == marketplace]
        top_products = [p for p in top_products if p.marketplace == marketplace]
        # Recalculate percentage to 100% for single marketplace
        if marketplace_data:
            marketplace_data[0] = MarketplaceRevenue(
                marketplace=marketplace_data[0].marketplace,
                revenue=marketplace_data[0].revenue,
                orders=marketplace_data[0].orders,
                percentage=100.0,
            )

    # Aggregate totals from marketplace breakdown
    total_revenue = round(sum(m.revenue for m in marketplace_data), 2)
    total_orders = sum(m.orders for m in marketplace_data)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # Weighted conversion rate from top products (rough aggregate)
    conversion_rate = 4.7  # default overall
    if marketplace and top_products:
        conversion_rate = round(
            sum(p.conversion_rate for p in top_products) / len(top_products), 1
        )

    return AnalyticsResponse(
        total_revenue=total_revenue,
        total_orders=total_orders,
        conversion_rate=conversion_rate,
        avg_order_value=avg_order_value,
        revenue_by_marketplace=marketplace_data,
        monthly_revenue=monthly_data,
        top_products=top_products,
    )
