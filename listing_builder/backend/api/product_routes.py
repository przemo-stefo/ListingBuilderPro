# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/product_routes.py
# Purpose: CRUD API routes for products
# NOT for: Import, AI, or export logic

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models import Product, ProductStatus
from schemas import ProductResponse, ProductList, DashboardStatsResponse, ProductUpdate
from api.dependencies import require_user_id
from typing import Optional
import structlog

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductList)
@limiter.limit("30/minute")
async def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    List products with pagination and filters.

    Query params:
        - page: Page number (default 1)
        - page_size: Items per page (default 20, max 100)
        - status: Filter by status (imported, optimized, published, etc)
        - source: Filter by source platform (allegro, etc)
    """
    # WHY: Multi-tenant — each user sees only their own products
    query = db.query(Product).filter(Product.user_id == user_id)

    # Apply filters
    if status:
        query = query.filter(Product.status == status)
    if source:
        query = query.filter(Product.source_platform == source)

    # Count total
    total = query.count()

    # WHY: ORDER BY is required for deterministic pagination — without it,
    # rows can shift between pages as the DB optimizer changes row order
    offset = (page - 1) * page_size
    products = query.order_by(Product.id.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return ProductList(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# IMPORTANT: /stats/summary MUST be above /{product_id} — otherwise FastAPI
# matches "stats" as a product_id and returns 422
@router.get("/stats/summary", response_model=DashboardStatsResponse)
@limiter.limit("30/minute")
async def get_stats(request: Request, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Dashboard stats — 8 cards on the main dashboard page.
    Returns counts by status + aggregate metrics the frontend expects.
    """
    # WHY: Single GROUP BY instead of N+1 (was 7 queries, now 2)
    status_rows = db.query(
        Product.status, func.count(Product.id)
    ).filter(Product.user_id == user_id).group_by(Product.status).all()
    counts = {str(s.value) if hasattr(s, 'value') else str(s): c for s, c in status_rows}
    total = sum(counts.values())

    # WHY: Real avg from DB instead of hardcoded 78.5
    avg_score = db.query(func.avg(Product.optimization_score)).filter(
        Product.user_id == user_id,
        Product.optimization_score.isnot(None)
    ).scalar()

    return DashboardStatsResponse(
        total_products=total,
        pending_optimization=counts.get("imported", 0),
        optimized_products=counts.get("optimized", 0),
        published_products=counts.get("published", 0),
        failed_products=counts.get("failed", 0),
        average_optimization_score=round(float(avg_score), 1) if avg_score else 0.0,
        recent_imports=counts.get("imported", 0),
        recent_publishes=counts.get("published", 0),
    )


@router.get("/{product_id}", response_model=ProductResponse)
@limiter.limit("30/minute")
async def get_product(request: Request, product_id: int, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Get a single product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
@limiter.limit("10/minute")
async def update_product(
    request: Request,
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Update product fields — only provided (non-null) fields are changed."""
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # WHY: exclude_unset so only explicitly provided fields are updated
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    logger.info("product_updated", product_id=product_id)
    return product


@router.delete("/{product_id}")
@limiter.limit("5/minute")
async def delete_product(request: Request, product_id: int, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Delete a product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    logger.info("product_deleted", product_id=product_id)
    return {"status": "success", "message": "Product deleted"}
