# backend/api/research_routes.py
# Purpose: Audience research endpoint — calls Groq directly with key rotation
# NOT for: LLM prompts (that's ov_skills.py) or optimizer logic (optimizer_service.py)

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from groq import Groq
import structlog

from config import settings
from services.stripe_service import validate_license
from services.ov_skills import build_skill_prompt
from database import get_db

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/research", tags=["research"])

MODEL = "llama-3.3-70b-versatile"

# WHY: All 10 OV Skills validated server-side
ALLOWED_SKILLS = {
    "deep-customer-research", "icp-discovery", "creative-brief",
    "creative-testing", "facebook-ad-copy", "google-ad-copy",
    "video-script", "landing-page-optimization", "email-campaign",
    "idea-validation",
}

FREE_DAILY_LIMIT = 1


class AudienceResearchRequest(BaseModel):
    product: str = Field(..., min_length=3, max_length=500)
    audience: Optional[str] = Field(default="", max_length=500)
    skill: Optional[str] = Field(default="deep-customer-research", max_length=50)
    objective: Optional[str] = Field(default="", max_length=200)
    price: Optional[str] = Field(default="", max_length=100)
    keywords: Optional[str] = Field(default="", max_length=500)
    offer: Optional[str] = Field(default="", max_length=300)


class AudienceResearchResponse(BaseModel):
    skill: str
    product: str
    audience: str
    result: str
    tokens_used: int = 0
    model: str = ""
    cost: str = "$0.00"


def _check_research_limit(request: Request, db: Session):
    """Free tier = 1 research/day per IP. Premium = unlimited.

    WHY per-IP: Without this, free users burn Groq quota unlimited via curl.
    """
    license_key = request.headers.get("X-License-Key", "")
    if license_key and validate_license(license_key, db):
        return

    from datetime import date
    from models.optimization import OptimizationRun

    client_ip = get_remote_address(request)
    # WHY: Reuse optimization_runs table — research calls are tracked there too
    # Count research runs (marketplace='research') for today from this IP
    today_count = (
        db.query(OptimizationRun)
        .filter(
            OptimizationRun.created_at >= date.today(),
            OptimizationRun.client_ip == client_ip,
            OptimizationRun.marketplace == "research",
        )
        .count()
    )
    if today_count >= FREE_DAILY_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=f"Darmowy limit ({FREE_DAILY_LIMIT} badanie/dzien) wyczerpany. Wykup Premium!",
        )


def _call_groq_research(system_prompt: str, user_prompt: str) -> dict:
    """Call Groq with key rotation. Returns {text, tokens_used, model}."""
    keys = settings.groq_api_keys
    last_error = None

    for i, key in enumerate(keys):
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            text = response.choices[0].message.content.strip()
            total = response.usage.total_tokens if response.usage else 0
            return {"text": text, "tokens_used": total, "model": MODEL}
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("research_groq_rate_limit", key_index=i, remaining=len(keys) - i - 1)
                continue
            raise

    raise last_error or RuntimeError("All Groq keys exhausted")


@router.post("/audience", response_model=AudienceResearchResponse)
@limiter.limit("5/minute")
async def research_audience(
    request: Request,
    body: AudienceResearchRequest,
    db: Session = Depends(get_db),
):
    """
    Run audience research via Groq directly (6-key rotation).
    WHY: Direct call is more reliable than n8n single-key webhook.
    """
    skill = body.skill or "deep-customer-research"
    if skill not in ALLOWED_SKILLS:
        raise HTTPException(status_code=400, detail=f"Skill '{skill}' not allowed")

    _check_research_limit(request, db)

    audience = body.audience or f"buyers interested in {body.product}"

    prompts = build_skill_prompt(
        skill, body.product, audience,
        objective=body.objective or "",
        price=body.price or "",
        keywords=body.keywords or "",
        offer=body.offer or "",
    )
    if not prompts:
        raise HTTPException(status_code=400, detail=f"Unknown skill: {skill}")

    logger.info("research_audience_start", product=body.product[:50], skill=skill)

    try:
        result = _call_groq_research(prompts["system"], prompts["user"])
    except Exception as e:
        logger.error("research_audience_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=502, detail=f"Research error: {str(e)[:200]}")

    logger.info("research_audience_done", product=body.product[:50], result_len=len(result["text"]))

    # WHY: Track research runs for per-IP daily limit enforcement
    try:
        from models.optimization import OptimizationRun
        run = OptimizationRun(
            product_title=body.product[:200],
            brand=skill,
            marketplace="research",
            mode="research",
            coverage_pct=0,
            compliance_status="N/A",
            request_data={"skill": skill, "product": body.product[:200]},
            response_data={"tokens_used": result["tokens_used"]},
            client_ip=get_remote_address(request),
        )
        db.add(run)
        db.commit()
    except Exception as save_err:
        logger.warning("research_history_save_failed", error=str(save_err))

    return AudienceResearchResponse(
        skill=skill,
        product=body.product,
        audience=audience,
        result=result["text"],
        tokens_used=result["tokens_used"],
        model=result["model"],
        cost="$0.00",
    )
