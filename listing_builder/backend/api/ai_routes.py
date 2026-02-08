# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/ai_routes.py
# Purpose: API routes for AI optimization (Groq)
# NOT for: Import or export logic

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProductOptimizationRequest, ProductResponse
from services.ai_service import AIService
from models import Product, BulkJob, JobStatus
from workers.ai_worker import run_batch_optimize
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
    """Optimize only the product title (faster)."""
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
    """Optimize only the product description (faster)."""
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Optimize multiple products in background.
    Returns immediately with a job ID — poll /batch-optimize/{job_id} for progress.
    """
    if not product_ids:
        raise HTTPException(status_code=400, detail="product_ids cannot be empty")
    if len(product_ids) > 50:
        raise HTTPException(status_code=400, detail="Max 50 products per batch")

    logger.info("batch_optimization_requested", count=len(product_ids))

    # Create a BulkJob to track progress
    job = BulkJob(
        job_type="optimize",
        target_marketplace=target_marketplace,
        status=JobStatus.PENDING,
        product_ids=product_ids,
        total_count=len(product_ids),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue background work
    background_tasks.add_task(run_batch_optimize, job.id, product_ids, target_marketplace)

    return {
        "job_id": job.id,
        "status": "pending",
        "total": len(product_ids),
        "message": f"Batch optimization queued. Poll GET /api/ai/batch-optimize/{job.id} for progress.",
    }


@router.get("/batch-optimize/{job_id}")
async def get_batch_status(job_id: int, db: Session = Depends(get_db)):
    """Check progress of a batch optimization job."""
    job = db.query(BulkJob).filter(BulkJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status.value if job.status else "unknown",
        "total": job.total_count,
        "success": job.success_count,
        "failed": job.failed_count,
        "results": job.results or [],
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
