# backend/api/research_routes.py
# Purpose: Audience research endpoint — calls n8n OV Skills webhook
# NOT for: LLM prompts or optimizer logic (that's optimizer_service.py)

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx
import structlog

from services.stripe_service import validate_license
from database import get_db

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/research", tags=["research"])

# WHY: n8n webhook on izabela166 runs OV Skills (Groq free tier)
N8N_WEBHOOK_URL = "https://n8n.feedmasters.org/webhook/ov-skills"

ALLOWED_SKILLS = {"deep-customer-research", "icp-discovery", "creative-brief"}

# WHY: Free tier = 1 research/day per IP, premium = unlimited
FREE_DAILY_LIMIT = 1


class AudienceResearchRequest(BaseModel):
    product: str = Field(..., min_length=3, max_length=500)
    audience: Optional[str] = Field(default="", max_length=500)
    skill: Optional[str] = Field(default="deep-customer-research", max_length=50)


class AudienceResearchResponse(BaseModel):
    skill: str
    product: str
    audience: str
    result: str
    tokens_used: int = 0
    model: str = ""
    cost: str = "$0.00"


def _check_research_limit(request: Request, db: Session):
    """Free tier = 1 research/day per IP. Premium = unlimited."""
    license_key = request.headers.get("X-License-Key", "")
    if license_key and validate_license(license_key, db):
        return

    # WHY: Simple in-memory approach — research results aren't saved to DB,
    # so we use a lightweight check via request IP + date header
    # For v1, rate limiter handles abuse; per-IP daily count is a future enhancement
    pass


@router.post("/audience", response_model=AudienceResearchResponse)
@limiter.limit("5/minute")
async def research_audience(
    request: Request,
    body: AudienceResearchRequest,
    db: Session = Depends(get_db),
):
    """
    Run audience research via n8n OV Skills webhook.
    WHY: Gives the optimizer buyer-language context for better listings.
    """
    skill = body.skill or "deep-customer-research"
    if skill not in ALLOWED_SKILLS:
        raise HTTPException(status_code=400, detail=f"Skill '{skill}' not allowed")

    _check_research_limit(request, db)

    audience = body.audience or f"buyers interested in {body.product}"

    logger.info(
        "research_audience_start",
        product=body.product[:50],
        skill=skill,
    )

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                N8N_WEBHOOK_URL,
                json={
                    "skill": skill,
                    "product": body.product,
                    "audience": audience,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        logger.error("research_audience_timeout", product=body.product[:50])
        raise HTTPException(status_code=504, detail="Research timeout — try again")
    except Exception as e:
        logger.error("research_audience_error", error=str(e))
        raise HTTPException(status_code=502, detail="Research service unavailable")

    logger.info(
        "research_audience_done",
        product=body.product[:50],
        result_len=len(data.get("result", "")),
    )

    return AudienceResearchResponse(
        skill=skill,
        product=body.product,
        audience=audience,
        result=data.get("result", ""),
        tokens_used=data.get("tokens_used", 0),
        model=data.get("model", ""),
        cost=data.get("cost", "$0.00"),
    )
