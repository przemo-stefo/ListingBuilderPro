# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/ai_routes.py
# Purpose: API routes for AI optimization (Groq)
# NOT for: Import or export logic

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProductOptimizationRequest, ProductResponse
from services.ai_service import AIService
from models import Product
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ai", tags=["AI Optimization"])


@router.post("/optimize/{product_id}", response_model=ProductResponse)
async def optimize_product(
    product_id: int,
    target_marketplace: str = "amazon",
    db: Session = Depends(get_db)
):
    """
    Optimize a product listing with AI.
    Uses Groq llama-3.3-70b-versatile for fast, high-quality results.

    Args:
        product_id: Product ID to optimize
        target_marketplace: amazon, ebay, or kaufland

    Returns:
        Optimized product data
    """
    logger.info("ai_optimization_requested", product_id=product_id, marketplace=target_marketplace)

    try:
        service = AIService(db)
        product = service.optimize_product(product_id, target_marketplace)
        return product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("optimization_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/optimize-title/{product_id}")
async def optimize_title_only(
    product_id: int,
    target_marketplace: str = "amazon",
    db: Session = Depends(get_db)
):
    """
    Optimize only the product title (faster).
    """
    logger.info("title_optimization_requested", product_id=product_id)

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        service = AIService(db)
        optimized_title = service.optimize_title(product, target_marketplace)

        return {
            "product_id": product_id,
            "original_title": product.title_original,
            "optimized_title": optimized_title,
            "marketplace": target_marketplace,
        }
    except Exception as e:
        logger.error("title_optimization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-description/{product_id}")
async def optimize_description_only(
    product_id: int,
    target_marketplace: str = "amazon",
    db: Session = Depends(get_db)
):
    """
    Optimize only the product description (faster).
    """
    logger.info("description_optimization_requested", product_id=product_id)

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        service = AIService(db)
        optimized_desc = service.optimize_description(product, target_marketplace)

        return {
            "product_id": product_id,
            "optimized_description": optimized_desc,
            "marketplace": target_marketplace,
        }
    except Exception as e:
        logger.error("description_optimization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-optimize")
async def batch_optimize(
    product_ids: list[int],
    target_marketplace: str = "amazon",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Optimize multiple products in background.
    Returns immediately with job status.

    TODO: Implement with Dramatiq worker for true async processing.
    """
    logger.info("batch_optimization_requested", count=len(product_ids))

    # For now, process synchronously (should be async with Dramatiq)
    results = []
    for product_id in product_ids:
        try:
            service = AIService(db)
            product = service.optimize_product(product_id, target_marketplace)
            results.append({
                "product_id": product_id,
                "status": "success",
                "score": product.optimization_score
            })
        except Exception as e:
            results.append({
                "product_id": product_id,
                "status": "failed",
                "error": str(e)
            })

    success_count = sum(1 for r in results if r["status"] == "success")

    return {
        "status": "completed",
        "total": len(product_ids),
        "success": success_count,
        "failed": len(product_ids) - success_count,
        "results": results
    }
