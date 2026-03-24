# backend/api/optimizer_routes.py
# Purpose: API endpoints for listing optimization via direct Groq service
# NOT for: LLM prompts or keyword logic (that's in services/optimizer_service.py)

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
from datetime import date
import structlog

from services.optimizer_service import optimize_listing
from services.llm_providers import PROVIDERS
from services.stripe_service import validate_license
from database import get_db
from models.optimization import OptimizationRun
from models.shared_listing import SharedListing
from api.dependencies import require_user_id, require_admin
from utils.privacy import hash_ip
import secrets

limiter = Limiter(key_func=get_remote_address)

logger = structlog.get_logger()


def _hashed_ip(request: Request) -> str:
    """WHY: GDPR — store hashed IP, not raw. Rate limiting still works (same hash = same person)."""
    return hash_ip(get_remote_address(request))

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])

# WHY: No free tier — Mateusz 24.03. Everyone pays 19 PLN/mies from day one.
FREE_DAILY_LIMIT = 0


def _check_tier_limit(request: Request, db: Session, requested_count: int = 1):
    """
    Check if user can optimize. Valid license key = unlimited. No key = blocked.
    SECURITY: This is the real gate — frontend limit is cosmetic only.
    """
    license_key = request.headers.get("X-License-Key", "")
    if license_key and validate_license(license_key, db):
        return  # unlimited

    # WHY: No free tier — reject all non-premium users
    raise HTTPException(
        status_code=402,
        detail="Wymagana subskrypcja Premium (19 zł/mies). Wykup aby korzystać z Optymalizatora!",
    )


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
    audience_context: Optional[str] = Field(default="", max_length=5000)
    account_type: str = Field(default="seller", pattern="^(seller|vendor)$")
    # WHY: Multi-LLM support — client picks provider, sends their own API key
    llm_provider: Optional[str] = Field(default=None, max_length=20)
    llm_api_key: Optional[str] = Field(default=None, max_length=200)
    # WHY: Imported product data — AI uses as reference to improve listing
    original_description: Optional[str] = Field(default="", max_length=5000)
    original_bullets: Optional[List[str]] = Field(default_factory=list, max_length=10)

    @field_validator("original_bullets")
    @classmethod
    def truncate_bullets(cls, v: Optional[List[str]]) -> List[str]:
        """WHY: Each bullet max 500 chars — prevents oversized payloads from reaching LLM."""
        if not v:
            return []
        return [b[:500] for b in v]


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


class RankingJuiceResponse(BaseModel):
    score: float = 0
    grade: str = ""
    verdict: str = ""
    components: Dict[str, float] = {}
    weights: Dict[str, float] = {}


class CoverageBreakdown(BaseModel):
    title_pct: float = 0
    bullets_pct: float = 0
    backend_pct: float = 0
    description_pct: float = 0


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
    ranking_juice: Optional[RankingJuiceResponse] = None
    llm_provider: str = "groq"  # WHY: Shows which LLM generated the listing
    llm_fallback_from: Optional[str] = None  # WHY: Set when provider failed and fell back to Groq
    optimization_source: str = "direct"
    listing_history_id: Optional[str] = None  # WHY: Used by frontend feedback widget
    trace: Optional[Dict[str, Any]] = None  # WHY: Observability — tokens, latency, cost per run
    coverage_breakdown: Optional[CoverageBreakdown] = None  # WHY: Per-placement coverage bars
    coverage_target: float = 95.0
    meets_coverage_target: bool = False
    ppc_recommendations: Optional[Dict[str, Any]] = None  # WHY: PPC match-type suggestions
    account_type: str = "seller"


@router.post("/generate", response_model=OptimizerResponse)
@limiter.limit("10/minute")
async def generate_listing(request: Request, body: OptimizerRequest, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Generate an optimized listing using Groq LLM + keyword analysis.

    WHY: Runs 3 LLM calls (title, bullets, description) then computes
    coverage scores, backend keyword packing, and compliance checks.
    """
    # SECURITY: Server-side tier check before any LLM calls
    _check_tier_limit(request, db)

    logger.info(
        "optimizer_request",
        product=body.product_title[:50],
        brand=body.brand,
        marketplace=body.marketplace,
        keyword_count=len(body.keywords),
    )

    # WHY: Build provider_config if client requested non-Groq provider
    provider_config = None
    if body.llm_provider and body.llm_provider != "groq":
        if body.llm_provider not in PROVIDERS:
            raise HTTPException(status_code=400, detail=f"Nieznany provider: {body.llm_provider}")

        # WHY: Beast uses local Ollama — no API key needed, just BEAST_OLLAMA_URL in .env
        if body.llm_provider == "beast":
            from config import settings as app_settings
            if not app_settings.beast_ollama_url:
                raise HTTPException(status_code=400, detail="Beast AI nie jest skonfigurowany. Skontaktuj sie z administratorem.")
            provider_config = {
                "provider": "beast",
                "api_key": "ollama",  # WHY: Ollama ignores this but call_llm needs it
            }
        else:
            api_key = body.llm_api_key
            # WHY: If frontend didn't send a key, try to read the saved key from user settings
            if not api_key:
                from api.settings_routes import _load_settings
                settings_data = _load_settings(db, user_id)
                saved_providers = settings_data.get("llm", {}).get("providers", {})
                saved_conf = saved_providers.get(body.llm_provider, {})
                api_key = saved_conf.get("api_key", "") if isinstance(saved_conf, dict) else ""

            if not api_key:
                raise HTTPException(status_code=400, detail="Klucz API wymagany dla tego providera. Zapisz go w Ustawieniach lub wklej w formularzu.")

            provider_config = {
                "provider": body.llm_provider,
                "api_key": api_key,
            }

    # WHY: Beast (qwen3:235b) runs 4 sequential LLM calls ~14s each = ~56s total.
    # Groq is fast (2-5s total), so 60s is fine. Beast needs 180s.
    llm_timeout = 180.0 if (provider_config and provider_config.get("provider") == "beast") else 60.0

    try:
        result = await asyncio.wait_for(
            optimize_listing(
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
                db=db,
                audience_context=body.audience_context or "",
                account_type=body.account_type,
                category=body.category or "",
                provider_config=provider_config,
                user_id=user_id,
                original_description=body.original_description or "",
                original_bullets=body.original_bullets or [],
            ),
            timeout=llm_timeout,
        )

        logger.info(
            "optimizer_success",
            coverage=result.get("scores", {}).get("coverage_pct", 0),
            compliance=result.get("compliance", {}).get("status", "UNKNOWN"),
        )

        # WHY: Auto-save to history — non-blocking, don't fail the response if DB save fails
        try:
            run = OptimizationRun(
                user_id=user_id,
                product_title=body.product_title,
                brand=body.brand,
                marketplace=body.marketplace,
                mode=body.mode,
                coverage_pct=result.get("scores", {}).get("coverage_pct", 0),
                compliance_status=result.get("compliance", {}).get("status", "UNKNOWN"),
                # SECURITY: Strip API key before persisting — never store user keys in history
                request_data={k: v for k, v in body.model_dump().items() if k != "llm_api_key"},
                response_data=result,
                trace_data=result.get("trace"),
                client_ip=_hashed_ip(request),
            )
            db.add(run)
            db.commit()
        except Exception as save_err:
            logger.warning("optimizer_history_save_failed", error=str(save_err))

        return result

    except asyncio.TimeoutError:
        logger.error("optimizer_timeout", product=body.product_title[:50])
        raise HTTPException(
            status_code=504,
            detail="Optymalizacja przekroczyła limit czasu (60s). Spróbuj ponownie za chwilę.",
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        logger.error("optimizer_error", error=str(e), product=body.product_title[:50], exc_info=True)
        # WHY: Differentiate between rate limit (all keys exhausted) and other errors
        if "rate_limit" in error_msg or "429" in error_msg or "too many" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Serwer AI jest chwilowo przeciążony. Spróbuj ponownie za minutę.",
            )
        raise HTTPException(status_code=500, detail="Optymalizacja nie powiodła się. Spróbuj ponownie.")


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
async def generate_batch(request: Request, body: BatchOptimizerRequest, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Generate optimized listings for multiple products.

    WHY: Processes sequentially because each product runs 3 LLM calls.
    Per-product error handling ensures one failure doesn't abort the batch.
    """
    # SECURITY: Server-side tier check — batch counts ALL items against daily limit
    _check_tier_limit(request, db, requested_count=len(body.products))

    results: List[BatchOptimizerResult] = []
    succeeded = 0
    failed = 0

    logger.info("batch_optimizer_start", total_products=len(body.products))

    for i, product in enumerate(body.products):
        try:
            # WHY: Build provider_config per product — each could have different provider
            batch_provider_config = None
            if product.llm_provider and product.llm_provider != "groq":
                if product.llm_provider in PROVIDERS and product.llm_api_key:
                    batch_provider_config = {
                        "provider": product.llm_provider,
                        "api_key": product.llm_api_key,
                    }

            batch_timeout = 180.0 if (batch_provider_config and batch_provider_config.get("provider") == "beast") else 60.0
            data = await asyncio.wait_for(
                optimize_listing(
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
                    db=db,
                    audience_context=product.audience_context or "",
                    account_type=product.account_type,
                    category=product.category or "",
                    provider_config=batch_provider_config,
                    user_id=user_id,
                    original_description=product.original_description or "",
                    original_bullets=product.original_bullets or [],
                ),
                timeout=batch_timeout,
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

        except asyncio.TimeoutError:
            logger.error("batch_item_timeout", index=i, product=product.product_title[:50])
            results.append(BatchOptimizerResult(
                product_title=product.product_title,
                status="error",
                error="Timeout — produkt zbyt duży lub serwer AI przeciążony",
            ))
            failed += 1
            continue

        except Exception as e:
            error_msg = str(e).lower()
            logger.error("batch_item_error", index=i, error=str(e))
            # WHY: Rate limit = all keys exhausted — remaining products will also fail
            if "rate_limit" in error_msg or "429" in error_msg:
                results.append(BatchOptimizerResult(
                    product_title=product.product_title,
                    status="error",
                    error="Serwer AI przeciążony — spróbuj za minutę",
                ))
                failed += 1
                # WHY: Skip remaining products — they'll all hit the same rate limit
                for remaining in body.products[i + 1:]:
                    results.append(BatchOptimizerResult(
                        product_title=remaining.product_title,
                        status="error",
                        error="Pominięto — serwer AI przeciążony",
                    ))
                    failed += 1
                break

            results.append(BatchOptimizerResult(
                product_title=product.product_title,
                status="error",
                error="Optymalizacja nie powiodła się",
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
    user_id: str = Depends(require_user_id),
):
    """List optimization runs, newest first."""
    offset = (page - 1) * page_size
    total = db.query(OptimizationRun).filter(OptimizationRun.user_id == user_id).count()
    runs = (
        db.query(OptimizationRun)
        .filter(OptimizationRun.user_id == user_id)
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
async def get_history_detail(run_id: int, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Get a single run with full response_data for reload."""
    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id, OptimizationRun.user_id == user_id).first()
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
async def delete_history(request: Request, run_id: int, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Delete a single optimization run."""
    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id, OptimizationRun.user_id == user_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(run)
    db.commit()
    return {"status": "deleted", "id": run_id}


@router.post("/history/{run_id}/improve")
@limiter.limit("5/minute")
async def improve_from_history(request: Request, run_id: int, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """
    Re-optimize a listing from history with improvement hints.
    WHY: Loads request_data + response_data, builds hints from missing keywords
    and low coverage, then re-runs optimize_listing with those hints.
    """
    _check_tier_limit(request, db)

    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id, OptimizationRun.user_id == user_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    req = run.request_data or {}
    resp = run.response_data or {}
    scores = resp.get("scores", {})
    intel = resp.get("keyword_intel", {})

    # WHY: Build improvement context from previous run's weaknesses
    hints = []
    missing = intel.get("missing_keywords", [])
    if missing:
        hints.append(f"BRAKUJACE SLOWA KLUCZOWE z poprzedniej optymalizacji (MUSISZ je umiescic): {', '.join(missing)}")
    if scores.get("coverage_pct", 100) < 95:
        hints.append(f"Poprzednie pokrycie: {scores.get('coverage_pct')}% — cel to 96%+. Uzyj wiecej slow kluczowych w tytule i bulletach.")
    if scores.get("backend_utilization_pct", 100) < 80:
        hints.append(f"Backend wykorzystany w {scores.get('backend_utilization_pct')}% — wypelnij do 249 bajtow unikalnymi slowami.")

    improvement_context = '\n'.join(hints) if hints else "Popraw ogolna jakosc listingu."
    audience_ctx = req.get("audience_context", "")
    if audience_ctx:
        improvement_context = audience_ctx + "\n\n--- IMPROVEMENT HINTS ---\n" + improvement_context
    else:
        improvement_context = "--- IMPROVEMENT HINTS ---\n" + improvement_context

    keywords = req.get("keywords", [])
    if not keywords:
        raise HTTPException(status_code=400, detail="Brak slow kluczowych w historii — nie mozna re-optymalizowac.")

    try:
        result = await asyncio.wait_for(
            optimize_listing(
                product_title=req.get("product_title", ""),
                brand=req.get("brand", ""),
                keywords=keywords,
                marketplace=req.get("marketplace", "amazon_de"),
                mode=req.get("mode", "aggressive"),
                product_line=req.get("product_line", ""),
                language=req.get("language"),
                db=db,
                audience_context=improvement_context,
                account_type=req.get("account_type", "seller"),
                category=req.get("category", ""),
                provider_config=None,
                user_id=user_id,
                original_description=req.get("original_description", ""),
                original_bullets=req.get("original_bullets", []),
            ),
            timeout=60.0,
        )

        # WHY: Auto-save improved version to history
        try:
            new_run = OptimizationRun(
                user_id=user_id,
                product_title=req.get("product_title", ""),
                brand=req.get("brand", ""),
                marketplace=req.get("marketplace", "amazon_de"),
                mode=req.get("mode", "aggressive"),
                coverage_pct=result.get("scores", {}).get("coverage_pct", 0),
                compliance_status=result.get("compliance", {}).get("status", "UNKNOWN"),
                request_data={**req, "audience_context": improvement_context, "improved_from": run_id},
                response_data=result,
                trace_data=result.get("trace"),
                client_ip=_hashed_ip(request),
            )
            db.add(new_run)
            db.commit()
        except Exception as save_err:
            logger.warning("improve_history_save_failed", error=str(save_err))

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Re-optymalizacja przekroczyla limit czasu.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("improve_error", error=str(e), run_id=run_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Re-optymalizacja nie powiodła się")


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)


@router.patch("/history/{listing_id}/feedback")
@limiter.limit("10/minute")
async def submit_feedback(
    request: Request,
    listing_id: str,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """User rates a listing 1-5. Updates listing_history table."""
    from services.learning_service import submit_feedback as do_feedback

    success = do_feedback(db, listing_id, body.rating, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"status": "updated", "listing_id": listing_id, "rating": body.rating}


@router.get("/health")
async def optimizer_health(_admin: str = Depends(require_admin)):
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
        # WHY: 503 so monitoring systems detect unhealthy state via HTTP status
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "provider": "groq",
            "error": "Connection failed",
        })


# --- Trace / observability endpoints ---

@router.get("/traces")
async def list_traces(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List optimization runs that have trace data, with summary info."""
    runs = (
        db.query(OptimizationRun)
        .filter(OptimizationRun.trace_data.isnot(None), OptimizationRun.user_id == user_id)
        .order_by(OptimizationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(OptimizationRun).filter(OptimizationRun.trace_data.isnot(None), OptimizationRun.user_id == user_id).count()

    return {
        "items": [
            {
                "id": r.id,
                "product_title": r.product_title,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "total_duration_ms": (r.trace_data or {}).get("total_duration_ms"),
                "total_tokens": (r.trace_data or {}).get("total_tokens"),
                "estimated_cost_usd": (r.trace_data or {}).get("estimated_cost_usd"),
                "span_count": len((r.trace_data or {}).get("spans", [])),
            }
            for r in runs
        ],
        "total": total,
    }


@router.get("/traces/stats")
async def trace_stats(db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Aggregate trace stats: avg tokens, avg latency, total cost, run count."""
    # WHY: JSONB operators let us aggregate without pulling all rows into Python
    # WHY :user_id param: tenant isolation — only show stats for the current user
    row = db.execute(text("""
        SELECT
            COUNT(*) AS runs,
            COALESCE(AVG((trace_data->>'total_tokens')::numeric), 0) AS avg_tokens,
            COALESCE(AVG((trace_data->>'total_duration_ms')::numeric), 0) AS avg_duration_ms,
            COALESCE(SUM((trace_data->>'estimated_cost_usd')::numeric), 0) AS total_cost_usd,
            COALESCE(SUM((trace_data->>'total_tokens')::numeric), 0) AS total_tokens
        FROM optimization_runs
        WHERE trace_data IS NOT NULL AND user_id = :user_id
    """), {"user_id": user_id}).fetchone()

    return {
        "runs_with_traces": row[0],
        "avg_tokens_per_run": round(float(row[1]), 0),
        "avg_duration_ms": round(float(row[2]), 1),
        "total_cost_usd": round(float(row[3]), 4),
        "total_tokens": int(row[4]),
    }


# --- Grey Market Risk Scoring ---

class GreyMarketRequest(BaseModel):
    """Grey market risk scoring inputs — requires SP-API data"""
    unauthorized_sellers: int = Field(default=0, ge=0)
    buy_box_rate: float = Field(default=100.0, ge=0, le=100)
    suppressed_asins: int = Field(default=0, ge=0)
    hijack_reports: int = Field(default=0, ge=0)


@router.post("/grey-market-score")
@limiter.limit("10/minute")
async def grey_market_score(request: Request, body: GreyMarketRequest, _user_id: str = Depends(require_user_id)):
    """
    Calculate grey market risk score 0-100.
    WHY: Standalone endpoint — doesn't need optimization data, just SP-API signals.
    """
    from services.grey_market_service import score_grey_market

    return score_grey_market(
        unauthorized_sellers=body.unauthorized_sellers,
        buy_box_rate=body.buy_box_rate,
        suppressed_asins=body.suppressed_asins,
        hijack_reports=body.hijack_reports,
    )


# --- Share endpoints ---

class ShareListingData(BaseModel):
    """WHY: Validate listing structure — prevent arbitrary JSON storage."""
    title: str = Field(..., min_length=1, max_length=500)
    bullet_points: List[str] = Field(default_factory=list, max_length=10)
    description: str = Field(default="", max_length=10000)
    backend_keywords: str = Field(default="", max_length=500)


class ShareRequest(BaseModel):
    listing: ShareListingData
    scores: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    product_title: str = Field(..., min_length=1, max_length=500)
    brand: str = Field(..., min_length=1, max_length=200)
    marketplace: str = "amazon_de"


@router.post("/share")
@limiter.limit("10/minute")
async def create_share(request: Request, body: ShareRequest, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Create a public share link for a listing snapshot."""
    token = secrets.token_urlsafe(16)

    shared = SharedListing(
        token=token,
        user_id=user_id,
        product_title=body.product_title,
        brand=body.brand,
        marketplace=body.marketplace,
        listing_data=body.listing.model_dump(),
        scores_data=body.scores,
        compliance_data=body.compliance,
    )
    db.add(shared)
    db.commit()

    logger.info("share_created", token=token, product=body.product_title[:50])
    return {"token": token}


@router.get("/share/{token}")
@limiter.limit("30/minute")
async def get_share(request: Request, token: str, db: Session = Depends(get_db)):
    """
    Public endpoint — no auth required. Returns shared listing snapshot.
    WHY: Anyone with the link can view the listing.
    """
    # WHY: Reject obviously invalid tokens before hitting DB
    if not token or len(token) < 10 or len(token) > 30:
        raise HTTPException(status_code=404, detail="Link nie istnieje lub wygasl")

    shared = db.query(SharedListing).filter(SharedListing.token == token).first()
    if not shared:
        logger.debug("share_not_found", token_prefix=token[:6])
        raise HTTPException(status_code=404, detail="Link nie istnieje lub wygasl")

    # WHY: Check expiry if set
    if shared.expires_at:
        from datetime import datetime, timezone
        if shared.expires_at < datetime.now(timezone.utc):
            logger.info("share_expired", token_prefix=token[:6])
            raise HTTPException(status_code=410, detail="Link wygasl")

    return {
        "product_title": shared.product_title,
        "brand": shared.brand,
        "marketplace": shared.marketplace,
        "listing": shared.listing_data,
        "scores": shared.scores_data,
        "compliance": shared.compliance_data,
        "created_at": shared.created_at.isoformat() if shared.created_at else None,
    }


# --- Keyword Suggestions ---

@router.get("/keyword-suggestions")
@limiter.limit("20/minute")
async def keyword_suggestions(
    request: Request,
    marketplace: Optional[str] = Query(None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Return popular keywords from user's optimization history.

    WHY: Users re-use similar keywords across products — suggesting from
    history saves typing and ensures consistency.
    """
    # WHY: Extract keywords from request_data JSON across all user's runs
    query = db.query(OptimizationRun.request_data).filter(
        OptimizationRun.user_id == user_id,
        OptimizationRun.request_data.isnot(None),
    )
    if marketplace:
        query = query.filter(OptimizationRun.marketplace == marketplace)

    # WHY: Last 100 runs max — enough for good suggestions, fast query
    rows = query.order_by(OptimizationRun.created_at.desc()).limit(100).all()

    # Count keyword phrase frequency across runs
    freq: dict[str, int] = {}
    for (req_data,) in rows:
        if not req_data or not isinstance(req_data, dict):
            continue
        kws = req_data.get("keywords", [])
        for kw in kws:
            phrase = kw.get("phrase", "").strip().lower() if isinstance(kw, dict) else str(kw).strip().lower()
            if phrase and len(phrase) >= 2:
                freq[phrase] = freq.get(phrase, 0) + 1

    # Sort by frequency, return top N
    sorted_kws = sorted(freq.items(), key=lambda x: -x[1])[:limit]
    return [{"phrase": p, "count": c} for p, c in sorted_kws]
