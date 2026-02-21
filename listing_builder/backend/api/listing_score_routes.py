# backend/api/listing_score_routes.py
# Purpose: Listing Score endpoint — rate listing quality 1-10 with copywriting frameworks
# NOT for: Listing generation (optimizer_routes) or ad copy (ad_copy_routes)

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from services.listing_score_service import score_listing

logger = structlog.get_logger()

# WHY: 5/min — scoring burns Groq tokens, prevent abuse while allowing normal usage
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/score", tags=["score"])


class ScoreRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    bullets: list[str] = Field(..., min_length=1, max_length=10)
    description: str = Field(default="", max_length=5000)


class DimensionScore(BaseModel):
    name: str
    score: int
    explanation: str
    tip: str


class ScoreResponse(BaseModel):
    overall_score: float
    dimensions: list[DimensionScore]
    sources_used: int


@router.post("/listing", response_model=ScoreResponse)
@limiter.limit("5/minute")
async def score_listing_endpoint(
    request: Request,
    body: ScoreRequest,
    db: Session = Depends(get_db),
):
    """Score an Amazon listing 1-10 on 5 copywriting dimensions with actionable tips."""
    try:
        result = await score_listing(
            title=body.title,
            bullets=body.bullets,
            description=body.description,
            db=db,
        )
        return result
    except Exception as e:
        logger.error("listing_score_endpoint_error", error=str(e))
        return ScoreResponse(
            overall_score=0.0,
            dimensions=[],
            sources_used=0,
        )
