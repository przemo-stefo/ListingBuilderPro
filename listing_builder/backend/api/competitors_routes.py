# backend/api/competitors_routes.py
# Purpose: Competitors endpoint — DB-backed price comparison, ratings, win/loss status
# NOT for: Product CRUD or inventory tracking (separate files)

from fastapi import APIRouter, Query, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from api.dependencies import require_user_id
from schemas import CompetitorsResponse, CompetitorItem
from typing import Optional

router = APIRouter(prefix="/api/competitors", tags=["Competitors"])


@router.get("", response_model=CompetitorsResponse)
async def get_competitors(
    request: Request,
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    search: Optional[str] = Query(None, description="Search competitor name or product title"),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    List competitors with price comparison and rating data.
    Summary stats are computed from the user's FULL dataset (before filtering).
    """
    # WHY: Summary stats from user's full dataset for dashboard cards
    stats = db.execute(text(
        "SELECT "
        "  COUNT(*) FILTER (WHERE status = 'winning') AS winning, "
        "  COUNT(*) FILTER (WHERE status = 'losing') AS losing, "
        "  COALESCE(ROUND(AVG(ABS(price_difference))::numeric, 2), 0) AS avg_gap "
        "FROM competitors WHERE user_id = :uid"
    ), {"uid": user_id}).fetchone()

    # WHY: Filtered query for the table view — built with text() fragments, never f-string user input
    clauses = ["SELECT * FROM competitors"]
    params = {"uid": user_id}
    conditions = ["user_id = :uid"]
    if marketplace:
        conditions.append("marketplace = :mp")
        params["mp"] = marketplace
    if search:
        # WHY: Escape SQL LIKE wildcards to prevent wildcard injection (% and _ are special in LIKE)
        safe_search = search.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions.append(
            "(LOWER(competitor_name) LIKE :q ESCAPE '\\' OR LOWER(product_title) LIKE :q ESCAPE '\\')"
        )
        params["q"] = f"%{safe_search}%"

    clauses.append("WHERE " + " AND ".join(conditions))
    clauses.append("ORDER BY marketplace, competitor_name")
    rows = db.execute(text(" ".join(clauses)), params).fetchall()

    items = [
        CompetitorItem(
            id=str(r.id), competitor_name=r.competitor_name, asin=r.asin,
            product_title=r.product_title, marketplace=r.marketplace,
            their_price=r.their_price, our_price=r.our_price,
            price_difference=r.price_difference, their_rating=r.their_rating,
            their_reviews_count=r.their_reviews_count, status=r.status,
            last_checked=r.last_checked.isoformat() if r.last_checked else "",
        )
        for r in rows
    ]

    return CompetitorsResponse(
        competitors=items,
        total=len(items),
        winning_count=stats.winning,
        losing_count=stats.losing,
        avg_price_gap=float(stats.avg_gap),
    )
