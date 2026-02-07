# backend/api/optimizer_routes.py
# Purpose: API endpoints for listing optimization via direct Groq service
# NOT for: LLM prompts or keyword logic (that's in services/optimizer_service.py)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog

from services.optimizer_service import optimize_listing

logger = structlog.get_logger()

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


class OptimizerKeyword(BaseModel):
    """Single keyword with optional search volume"""
    phrase: str
    search_volume: int = 0


class OptimizerRequest(BaseModel):
    """Request payload for listing optimization"""
    product_title: str = Field(..., min_length=3)
    brand: str = Field(..., min_length=1)
    product_line: Optional[str] = ""
    keywords: List[OptimizerKeyword] = Field(..., min_length=1)
    marketplace: str = Field(default="amazon_de")
    mode: str = Field(default="aggressive")
    language: Optional[str] = None
    asin: Optional[str] = ""
    category: Optional[str] = ""


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
async def generate_listing(request: OptimizerRequest):
    """
    Generate an optimized listing using Groq LLM + keyword analysis.

    WHY: Runs 3 LLM calls (title, bullets, description) then computes
    coverage scores, backend keyword packing, and compliance checks.
    """
    logger.info(
        "optimizer_request",
        product=request.product_title[:50],
        brand=request.brand,
        marketplace=request.marketplace,
        keyword_count=len(request.keywords),
    )

    try:
        result = await optimize_listing(
            product_title=request.product_title,
            brand=request.brand,
            keywords=[
                {"phrase": k.phrase, "search_volume": k.search_volume}
                for k in request.keywords
            ],
            marketplace=request.marketplace,
            mode=request.mode,
            product_line=request.product_line or "",
            language=request.language,
        )

        logger.info(
            "optimizer_success",
            coverage=result.get("scores", {}).get("coverage_pct", 0),
            compliance=result.get("compliance", {}).get("status", "UNKNOWN"),
        )

        return result

    except Exception as e:
        logger.error("optimizer_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


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
async def generate_batch(request: BatchOptimizerRequest):
    """
    Generate optimized listings for multiple products.

    WHY: Processes sequentially because each product runs 3 LLM calls.
    Per-product error handling ensures one failure doesn't abort the batch.
    """
    results: List[BatchOptimizerResult] = []
    succeeded = 0
    failed = 0

    logger.info("batch_optimizer_start", total_products=len(request.products))

    for i, product in enumerate(request.products):
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
                error=str(e),
            ))
            failed += 1

    logger.info(
        "batch_optimizer_done",
        total=len(request.products),
        succeeded=succeeded,
        failed=failed,
    )

    return BatchOptimizerResponse(
        total=len(request.products),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


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
            "error": str(e),
        }
