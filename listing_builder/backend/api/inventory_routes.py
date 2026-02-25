# backend/api/inventory_routes.py
# Purpose: Inventory endpoint — DB-backed stock levels, reorder points, supply days
# NOT for: Product CRUD or competitor tracking (separate files)

from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from schemas import InventoryResponse, InventoryItem
from typing import Optional

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("", response_model=InventoryResponse)
async def get_inventory(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    status: Optional[str] = Query(None, description="Filter by stock status"),
    search: Optional[str] = Query(None, description="Search SKU or product title"),
    db: Session = Depends(get_db),
):
    """
    List inventory items with stock levels and supply metrics.
    Summary stats are computed from the FULL dataset (before filtering).
    """
    # WHY: Summary stats from full dataset for dashboard cards
    stats = db.execute(text(
        "SELECT "
        "  COUNT(*) FILTER (WHERE status = 'in_stock') AS in_stock, "
        "  COUNT(*) FILTER (WHERE status = 'low_stock') AS low_stock, "
        "  COUNT(*) FILTER (WHERE status = 'out_of_stock') AS out_of_stock, "
        "  COALESCE(ROUND(SUM(total_value)::numeric, 2), 0) AS total_val "
        "FROM inventory_items"
    )).fetchone()

    # WHY: Filtered query for the table view — built with text() fragments, never f-string user input
    clauses = ["SELECT * FROM inventory_items"]
    params = {}
    conditions = []
    if marketplace:
        conditions.append("marketplace = :mp")
        params["mp"] = marketplace
    if status:
        conditions.append("status = :st")
        params["st"] = status
    if search:
        conditions.append("(LOWER(sku) LIKE :q OR LOWER(product_title) LIKE :q)")
        params["q"] = f"%{search.lower()}%"

    if conditions:
        clauses.append("WHERE " + " AND ".join(conditions))
    clauses.append("ORDER BY marketplace, sku")
    rows = db.execute(text(" ".join(clauses)), params).fetchall()

    items = [
        InventoryItem(
            id=str(r.id), sku=r.sku, product_title=r.product_title,
            marketplace=r.marketplace, quantity=r.quantity,
            reorder_point=r.reorder_point, days_of_supply=r.days_of_supply,
            status=r.status, unit_cost=r.unit_cost, total_value=r.total_value,
            last_restocked=r.last_restocked.isoformat() if r.last_restocked else "",
        )
        for r in rows
    ]

    return InventoryResponse(
        items=items,
        total=len(items),
        in_stock_count=stats.in_stock,
        low_stock_count=stats.low_stock,
        out_of_stock_count=stats.out_of_stock,
        total_value=float(stats.total_val),
    )
