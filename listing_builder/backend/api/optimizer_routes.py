# backend/api/optimizer_routes.py
# Purpose: API endpoints for listing optimization via direct Groq service
# NOT for: LLM prompts or keyword logic (that's in services/optimizer_service.py)

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from services.optimizer_service import optimize_listing
from database import get_db
from models.optimization import OptimizationRun

limiter = Limiter(key_func=get_remote_address)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


class OptimizerKeyword(BaseModel):
    """Single keyword with optional search volume"""
    phrase: str = Field(..., min_length=1, max_length=200)
    search_volume: int = Field(default=0, ge=0)


class OptimizerRequest(BaseModel):
    """Request payload for listing optimization"""
    product_title: str = Field(..., min_length=3, max_length=500)
    brand: str = Field(..., min_length=1, max_length=200)
    product_line: Optional[str] = Field(default="", max_length=200)
    keywords: List[OptimizerKeyword] = Field(..., min_length=1, max_length=200)
    marketplace: str = Field(default="amazon_de", max_length=50)
    mode: str = Field(default="aggressive", max_length=20)
    language: Optional[str] = Field(default=None, max_length=10)
    asin: Optional[str] = Field(default="", max_length=20)
    category: Optional[str] = Field(default="", max_length=200)


class OptimizerScores(BaseModel):
    coverage_pct: float = 0
    coverage_mode: str = "UNKNOWN"
    exact_matches_in_title: int = 0
    title_coverage_pct: float = 0
    backend_utilization_pct: float = 0
    backend_byte_size: int = 0
    compliance_status: str = "UNKNOWN"


class OptimizerListing(BaseModel):
    title: str = ""
    bullet_points: List[str] = []
    description: str = ""
    backend_keywords: str = ""


class OptimizerCompliance(BaseModel):
    status: str = "UNKNOWN"
    errors: List[str] = []
    warnings: List[str] = []
    error_count: int = 0
    warning_count: int = 0


class OptimizerKeywordIntel(BaseModel):
    total_analyzed: int = 0
    tier1_title: int = 0
    tier2_bullets: int = 0
    tier3_backend: int = 0
    missing_keywords: List[str] = []
    root_words: List[Dict[str, Any]] = []


class OptimizerResponse(BaseModel):
    status: str
    marketplace: str = ""
    brand: str = ""
    mode: str = ""
    language: str = ""
    listing: OptimizerListing = OptimizerListing()
    scores: OptimizerScores = OptimizerScores()
    compliance: OptimizerCompliance = OptimizerCompliance()
    keyword_intel: OptimizerKeywordIntel = OptimizerKeywordIntel()


@router.post("/generate", response_model=OptimizerResponse)
@limiter.limit("10/minute")
async def generate_listing(request: Request, body: OptimizerRequest, db: Session = Depends(get_db)):
    """
    Generate an optimized listing using Groq LLM + keyword analysis.

    WHY: Runs 3 LLM calls (title, bullets, description) then computes
    coverage scores, backend keyword packing, and compliance checks.
    """
    logger.info(
        "optimizer_request",
        product=body.product_title[:50],
        brand=body.brand,
        marketplace=body.marketplace,
        keyword_count=len(body.keywords),
    )

    try:
        result = await optimize_listing(
            product_title=body.product_title,
            brand=body.brand,
            keywords=[
                {"phrase": k.phrase, "search_volume": k.search_volume}
                for k in body.keywords
            ],
            marketplace=body.marketplace,
            mode=body.mode,
            product_line=body.product_line or "",
            language=body.language,
        )

        logger.info(
            "optimizer_success",
            coverage=result.get("scores", {}).get("coverage_pct", 0),
            compliance=result.get("compliance", {}).get("status", "UNKNOWN"),
        )

        # WHY: Auto-save to history — non-blocking, don't fail the response if DB save fails
        try:
            run = OptimizationRun(
                product_title=body.product_title,
                brand=body.brand,
                marketplace=body.marketplace,
                mode=body.mode,
                coverage_pct=result.get("scores", {}).get("coverage_pct", 0),
                compliance_status=result.get("compliance", {}).get("status", "UNKNOWN"),
                request_data=body.model_dump(),
                response_data=result,
            )
            db.add(run)
            db.commit()
        except Exception as save_err:
            logger.warning("optimizer_history_save_failed", error=str(save_err))

        return result

    except Exception as e:
        logger.error("optimizer_error", error=str(e))
        raise HTTPException(status_code=500, detail="Optimization failed")


# WHY: Batch endpoint processes multiple products sequentially
BATCH_MAX_PRODUCTS = 50


class BatchOptimizerRequest(BaseModel):
    """Batch of products to optimize"""
    products: List[OptimizerRequest] = Field(..., min_length=1, max_length=BATCH_MAX_PRODUCTS)


class BatchOptimizerResult(BaseModel):
    """Single product result within a batch — includes error field for failures"""
    product_title: str
    status: str  # "completed" or "error"
    error: Optional[str] = None
    result: Optional[OptimizerResponse] = None


class BatchOptimizerResponse(BaseModel):
    """Aggregated batch response"""
    total: int
    succeeded: int
    failed: int
    results: List[BatchOptimizerResult]


@router.post("/generate-batch", response_model=BatchOptimizerResponse)
@limiter.limit("3/minute")
async def generate_batch(request: Request, body: BatchOptimizerRequest = None):
    """
    Generate optimized listings for multiple products.

    WHY: Processes sequentially because each product runs 3 LLM calls.
    Per-product error handling ensures one failure doesn't abort the batch.
    """
    results: List[BatchOptimizerResult] = []
    succeeded = 0
    failed = 0

    logger.info("batch_optimizer_start", total_products=len(body.products))

    for i, product in enumerate(body.products):
        try:
            data = await optimize_listing(
                product_title=product.product_title,
                brand=product.brand,
                keywords=[
                    {"phrase": k.phrase, "search_volume": k.search_volume}
                    for k in product.keywords
                ],
                marketplace=product.marketplace,
                mode=product.mode,
                product_line=product.product_line or "",
                language=product.language,
            )

            results.append(BatchOptimizerResult(
                product_title=product.product_title,
                status="completed",
                result=OptimizerResponse(**data),
            ))
            succeeded += 1

            logger.info(
                "batch_item_success",
                index=i,
                product=product.product_title[:50],
                coverage=data.get("scores", {}).get("coverage_pct", 0),
            )

        except Exception as e:
            logger.error("batch_item_error", index=i, error=str(e))
            results.append(BatchOptimizerResult(
                product_title=product.product_title,
                status="error",
                error="Optimization failed for this product",
            ))
            failed += 1

    logger.info(
        "batch_optimizer_done",
        total=len(body.products),
        succeeded=succeeded,
        failed=failed,
    )

    return BatchOptimizerResponse(
        total=len(body.products),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


# --- History endpoints ---

@router.get("/history")
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List optimization runs, newest first."""
    offset = (page - 1) * page_size
    total = db.query(OptimizationRun).count()
    runs = (
        db.query(OptimizationRun)
        .order_by(OptimizationRun.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "product_title": r.product_title,
                "brand": r.brand,
                "marketplace": r.marketplace,
                "mode": r.mode,
                "coverage_pct": r.coverage_pct,
                "compliance_status": r.compliance_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
        "total": total,
        "page": page,
    }


@router.get("/history/{run_id}")
async def get_history_detail(run_id: int, db: Session = Depends(get_db)):
    """Get a single run with full response_data for reload."""
    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "product_title": run.product_title,
        "brand": run.brand,
        "marketplace": run.marketplace,
        "mode": run.mode,
        "coverage_pct": run.coverage_pct,
        "compliance_status": run.compliance_status,
        "request_data": run.request_data,
        "response_data": run.response_data,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.delete("/history/{run_id}")
@limiter.limit("10/minute")
async def delete_history(request: Request, run_id: int, db: Session = Depends(get_db)):
    """Delete a single optimization run."""
    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(run)
    db.commit()
    return {"status": "deleted", "id": run_id}


@router.get("/health")
async def optimizer_health():
    """Check if Groq API is reachable"""
    try:
        from groq import Groq
        from config import settings

        client = Groq(api_key=settings.groq_api_key)
        # WHY: Minimal call to verify API key is valid
        client.models.list()

        return {
            "status": "healthy",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "provider": "groq",
            "error": "Connection failed",
        }
