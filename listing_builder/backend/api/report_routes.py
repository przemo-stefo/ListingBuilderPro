# backend/api/report_routes.py
# Purpose: API endpoint for generating Google Sheets reports via gws CLI
# NOT for: Analytics queries (analytics_routes.py) or PDF export (separate)

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import asyncio
import structlog

from database import get_db
from api.dependencies import require_user_id
from services.gws_reports import create_report_spreadsheet, send_report_email, share_spreadsheet

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    """Request to generate a Google Sheets report."""
    marketplace: Optional[str] = Field(None, max_length=50)
    period: Optional[str] = Field(None, pattern="^(7d|30d|90d|12m)$")
    send_email: bool = Field(default=False)
    email_to: Optional[str] = Field(None, max_length=200)
    share_with: Optional[str] = Field(None, max_length=200)


class ReportResponse(BaseModel):
    status: str
    spreadsheet_id: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    email_sent: bool = False


@router.post("/generate", response_model=ReportResponse)
@limiter.limit("3/minute")
async def generate_report(
    request: Request,
    body: ReportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Generate a Google Sheets report with optimization, revenue, and inventory data.

    WHY: Mateusz wants shareable reports he can view on phone — Google Sheets is ideal.
    """
    # Build WHERE clause
    params: dict = {"uid": user_id}
    conditions = ["user_id = :uid"]
    if body.marketplace:
        conditions.append("marketplace = :mp")
        params["mp"] = body.marketplace
    where = "WHERE " + " AND ".join(conditions)

    # Query optimization runs
    opt_rows = db.execute(
        text(
            "SELECT created_at, product_title, brand, marketplace, mode, "
            "coverage_pct, compliance_status "
            "FROM optimization_runs " + where + " "
            "ORDER BY created_at DESC LIMIT 100"
        ),
        params,
    ).fetchall()
    optimization_data = [dict(r._mapping) for r in opt_rows]

    # Query revenue data
    mp_rows = db.execute(
        text(
            "SELECT marketplace, SUM(revenue) AS revenue, SUM(orders) AS orders "
            "FROM revenue_data " + where + " GROUP BY marketplace ORDER BY SUM(revenue) DESC"
        ),
        params,
    ).fetchall()

    grand_revenue = sum(r.revenue for r in mp_rows)
    total_orders = sum(r.orders for r in mp_rows)

    month_limit = {"7d": 1, "30d": 2, "90d": 3}.get(body.period, 12)
    monthly_rows = db.execute(
        text(
            "SELECT month, SUM(revenue) AS revenue, SUM(orders) AS orders "
            "FROM revenue_data " + where + " GROUP BY month "
            "ORDER BY MIN(created_at) DESC LIMIT :lim"
        ),
        {**params, "lim": month_limit},
    ).fetchall()

    # Top products
    tp_rows = db.execute(
        text(
            "SELECT product_title, marketplace, total_value, quantity "
            "FROM inventory_items " + where + " ORDER BY total_value DESC LIMIT 8"
        ),
        params,
    ).fetchall()

    analytics_data = {
        "total_revenue": round(grand_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(grand_revenue / total_orders, 2) if total_orders > 0 else 0,
        "revenue_by_marketplace": [
            {
                "marketplace": r.marketplace,
                "revenue": round(r.revenue, 2),
                "orders": r.orders,
                "percentage": round(r.revenue / grand_revenue * 100, 1) if grand_revenue > 0 else 0,
            }
            for r in mp_rows
        ],
        "monthly_revenue": [
            {"month": r.month, "revenue": round(r.revenue, 2), "orders": r.orders}
            for r in reversed(monthly_rows)
        ],
        "top_products": [
            {
                "title": r.product_title,
                "marketplace": r.marketplace,
                "revenue": round(r.total_value, 2),
                "units_sold": r.quantity,
                "conversion_rate": round(r.quantity / max(r.total_value, 1) * 100, 1),
            }
            for r in tp_rows
        ],
    }

    # Query inventory
    inv_rows = db.execute(
        text(
            "SELECT sku, product_title, marketplace, quantity, reorder_point, "
            "days_of_supply, unit_cost, total_value, status "
            "FROM inventory_items " + where + " ORDER BY total_value DESC LIMIT 50"
        ),
        params,
    ).fetchall()
    inventory_data = [dict(r._mapping) for r in inv_rows]

    # Create spreadsheet via gws
    from datetime import datetime
    title = f"Raport LBP — {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    spreadsheet_id = await asyncio.to_thread(
        create_report_spreadsheet, title, optimization_data, analytics_data, inventory_data,
    )

    if not spreadsheet_id:
        raise HTTPException(status_code=503, detail="Nie udalo sie utworzyc arkusza Google.")

    # Share if requested
    if body.share_with:
        await asyncio.to_thread(share_spreadsheet, spreadsheet_id, body.share_with)

    # Send email if requested
    email_sent = False
    if body.send_email and body.email_to:
        summary = (
            f"Raport wygenerowany: {len(optimization_data)} optymalizacji, "
            f"przychod {grand_revenue:.2f}, {total_orders} zamowien."
        )
        email_sent = await asyncio.to_thread(
            send_report_email, body.email_to,
            f"Raport LBP — {datetime.now().strftime('%Y-%m-%d')}", spreadsheet_id, summary,
        )

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    logger.info("report_generated", spreadsheet_id=spreadsheet_id, user_id=user_id)

    return ReportResponse(
        status="ok",
        spreadsheet_id=spreadsheet_id,
        spreadsheet_url=url,
        email_sent=email_sent,
    )
