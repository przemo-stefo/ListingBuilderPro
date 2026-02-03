# backend/api/optimizer_routes.py
# Purpose: Proxy endpoint for the n8n Listing Optimizer workflow
# NOT for: LLM logic or keyword analysis (that's all in the n8n workflow)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import structlog
import os

logger = structlog.get_logger()

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])

# WHY: n8n runs locally alongside the backend — no network hop
N8N_WEBHOOK_URL = os.getenv(
    "N8N_OPTIMIZER_URL",
    "http://localhost:5678/webhook/listing-optimizer"
)

# WHY: n8n LLM calls can take 10-15s for 3 sequential API calls
N8N_TIMEOUT = 60.0


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
    Generate an optimized listing via n8n Listing Optimizer workflow.

    WHY: The n8n workflow handles LLM calls, keyword tiering, backend byte-packing,
    and compliance checks — this endpoint just proxies to it.
    """
    # Build payload matching what the n8n webhook expects
    payload = {
        "product_title": request.product_title,
        "brand": request.brand,
        "product_line": request.product_line or "",
        "keywords": [
            {"phrase": k.phrase, "search_volume": k.search_volume}
            for k in request.keywords
        ],
        "marketplace": request.marketplace,
        "mode": request.mode,
        "asin": request.asin or "",
        "category": request.category or "",
    }

    # WHY: Only set language if explicitly provided — n8n auto-detects from marketplace
    if request.language:
        payload["language"] = request.language

    logger.info(
        "optimizer_request",
        product=request.product_title[:50],
        brand=request.brand,
        marketplace=request.marketplace,
        keyword_count=len(request.keywords),
    )

    try:
        async with httpx.AsyncClient(timeout=N8N_TIMEOUT) as client:
            response = await client.post(N8N_WEBHOOK_URL, json=payload)

        if response.status_code != 200:
            logger.error(
                "n8n_error",
                status=response.status_code,
                body=response.text[:500],
            )
            raise HTTPException(
                status_code=502,
                detail=f"n8n workflow returned {response.status_code}",
            )

        result = response.json()

        logger.info(
            "optimizer_success",
            coverage=result.get("scores", {}).get("coverage_pct", 0),
            compliance=result.get("scores", {}).get("compliance_status", "UNKNOWN"),
        )

        return result

    except httpx.TimeoutException:
        logger.error("n8n_timeout", url=N8N_WEBHOOK_URL)
        raise HTTPException(
            status_code=504,
            detail="Optimization timed out — n8n workflow took too long",
        )
    except httpx.ConnectError:
        logger.error("n8n_unreachable", url=N8N_WEBHOOK_URL)
        raise HTTPException(
            status_code=502,
            detail="n8n is not reachable — check if it's running on localhost:5678",
        )
    except Exception as e:
        logger.error("optimizer_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}",
        )


@router.get("/health")
async def optimizer_health():
    """Check if n8n workflow is reachable"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:5678/healthz")
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "n8n_status": response.status_code,
            "webhook_url": N8N_WEBHOOK_URL,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "webhook_url": N8N_WEBHOOK_URL,
        }
