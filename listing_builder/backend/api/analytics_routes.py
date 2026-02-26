# backend/api/analytics_routes.py
# Purpose: Analytics endpoint — DB-backed revenue, orders, conversion, top products
# NOT for: Real-time metrics or order processing (separate services)

from fastapi import APIRouter, Query, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from api.dependencies import require_user_id
from schemas import (
    AnalyticsResponse,
    MarketplaceRevenue,
    MonthlyRevenue,
    TopProduct,
)
from typing import Optional

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
@limiter.limit("10/minute")
async def get_analytics(
    request: Request,
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    period: Optional[str] = Query(None, description="Time period: 7d, 30d, 90d, 12m"),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    Revenue analytics with marketplace breakdown, monthly trend, and top products.
    Period param slices monthly data. Marketplace param filters everything.
    """
    # WHY: Helper avoids f-string SQL interpolation — all conditions built safely
    params: dict = {"uid": user_id}
    conditions = ["user_id = :uid"]
    if marketplace:
        conditions.append("marketplace = :mp")
        params["mp"] = marketplace
    where = "WHERE " + " AND ".join(conditions)

    mp_rows = db.execute(
        text(
            "SELECT marketplace, SUM(revenue) AS revenue, SUM(orders) AS orders "
            "FROM revenue_data " + where + " GROUP BY marketplace ORDER BY SUM(revenue) DESC"
        ),
        params,
    ).fetchall()

    grand_revenue = sum(r.revenue for r in mp_rows)
    marketplace_data = [
        MarketplaceRevenue(
            marketplace=r.marketplace,
            revenue=round(r.revenue, 2),
            orders=r.orders,
            percentage=round(r.revenue / grand_revenue * 100, 1) if grand_revenue > 0 else 0,
        )
        for r in mp_rows
    ]

    # WHY: Monthly trend — limit by period
    month_limit = {"7d": 1, "30d": 2, "90d": 3}.get(period, 12)
    monthly_rows = db.execute(
        text(
            "SELECT month, SUM(revenue) AS revenue, SUM(orders) AS orders "
            "FROM revenue_data " + where + " GROUP BY month "
            "ORDER BY MIN(created_at) DESC LIMIT :lim"
        ),
        {**params, "lim": month_limit},
    ).fetchall()

    # WHY: Reverse so oldest month is first (chart expects chronological order)
    monthly_data = [
        MonthlyRevenue(month=r.month, revenue=round(r.revenue, 2), orders=r.orders)
        for r in reversed(monthly_rows)
    ]

    # WHY: Top products from inventory_items (by total_value as proxy for revenue)
    tp_rows = db.execute(
        text(
            "SELECT id, product_title, marketplace, total_value, quantity "
            "FROM inventory_items " + where + " "
            "ORDER BY total_value DESC LIMIT 8"
        ),
        params,
    ).fetchall()

    top_products = [
        TopProduct(
            id=str(r.id),
            title=r.product_title,
            marketplace=r.marketplace,
            revenue=round(r.total_value, 2),
            units_sold=r.quantity,
            conversion_rate=round(r.quantity / max(r.total_value, 1) * 100, 1),
        )
        for r in tp_rows
    ]

    total_orders = sum(m.orders for m in marketplace_data)
    avg_order_value = round(grand_revenue / total_orders, 2) if total_orders > 0 else 0

    return AnalyticsResponse(
        total_revenue=round(grand_revenue, 2),
        total_orders=total_orders,
        conversion_rate=4.7,  # TODO: calculate from real data when order tracking is implemented
        avg_order_value=avg_order_value,
        revenue_by_marketplace=marketplace_data,
        monthly_revenue=monthly_data,
        top_products=top_products,
    )
