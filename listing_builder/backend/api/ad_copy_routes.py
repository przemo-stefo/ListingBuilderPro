# backend/api/ad_copy_routes.py
# Purpose: Ad copy generation endpoint — Facebook/Meta ad variations from product listings
# NOT for: Listing optimization (optimizer_routes) or Expert Q&A (knowledge_routes)

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from services.ad_copy_service import generate_ad_copy
from api.dependencies import require_premium

logger = structlog.get_logger()

# WHY: Rate limiter prevents Groq quota burn — 5/min is generous for ad generation
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/ads", tags=["ads"])


class AdCopyRequest(BaseModel):
    product_title: str = Field(..., min_length=3, max_length=300)
    product_features: list[str] = Field(..., min_length=1, max_length=10)
    target_audience: str = Field(default="", max_length=200)
    platform: str = Field(default="facebook", pattern="^(facebook|instagram|tiktok)$")


class AdVariation(BaseModel):
    type: str
    headline: str
    primary_text: str
    description: str


class AdCopyResponse(BaseModel):
    variations: list[AdVariation]
    sources_used: int
    sources: list[str] = []
    platform: str = "facebook"


@router.post("/generate", response_model=AdCopyResponse)
@limiter.limit("5/minute")
async def generate_ads(
    request: Request,
    body: AdCopyRequest,
    db: Session = Depends(get_db),
):
    """Generate 3 ad copy variations (hook, story, benefit) using RAG from ad creative courses."""
    require_premium(request, db)
    try:
        result = await generate_ad_copy(
            product_title=body.product_title,
            product_features=body.product_features,
            target_audience=body.target_audience,
            db=db,
            platform=body.platform,
        )
        return result
    except Exception as e:
        logger.error("ad_copy_endpoint_error", error=str(e))
        # WHY: Raise 500 instead of silent empty response — user must know generation failed
        raise HTTPException(status_code=500, detail="Generowanie reklam nie powiodlo sie")
