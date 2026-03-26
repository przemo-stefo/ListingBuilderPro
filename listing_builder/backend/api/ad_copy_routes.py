# backend/api/ad_copy_routes.py
# Purpose: Ad copy, headlines, video hooks, creative brief endpoints
# NOT for: Listing optimization (optimizer_routes) or Expert Q&A (knowledge_routes)

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from services.ad_copy_service import generate_ad_copy, generate_headlines, generate_hooks, generate_brief
from api.dependencies import require_premium, require_admin, require_user_id

logger = structlog.get_logger()

# WHY: Rate limiter prevents Groq quota burn
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/ads", tags=["ads"])


class AdCopyRequest(BaseModel):
    product_title: str = Field(..., min_length=3, max_length=300)
    product_features: list[str] = Field(..., min_length=1, max_length=10)
    target_audience: str = Field(default="", max_length=200)
    platform: str = Field(default="facebook", pattern="^(facebook|instagram|tiktok)$")
    framework: str = Field(default="mixed", pattern="^(mixed|aida|pas)$")


class ProductRequest(BaseModel):
    """Shared request for headlines, hooks, brief — no platform/framework needed."""
    product_title: str = Field(..., min_length=3, max_length=300)
    product_features: list[str] = Field(..., min_length=1, max_length=10)
    target_audience: str = Field(default="", max_length=200)


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_ads(
    request: Request,
    body: AdCopyRequest,
    db: Session = Depends(get_db),
    _user_id: str = Depends(require_user_id),
):
    """Generate ad copy variations (mixed/aida/pas) using RAG from ad creative courses."""
    require_premium(request, db)
    try:
        result = await generate_ad_copy(
            product_title=body.product_title,
            product_features=body.product_features,
            target_audience=body.target_audience,
            db=db,
            platform=body.platform,
            framework=body.framework,
        )
        return result
    except Exception as e:
        logger.error("ad_copy_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Generowanie reklam nie powiodlo sie")


@router.post("/headlines")
@limiter.limit("5/minute")
async def generate_headlines_endpoint(
    request: Request,
    body: ProductRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Generate 10 headlines using diverse copywriting formulas. Admin/beta only."""
    try:
        result = await generate_headlines(
            product_title=body.product_title,
            product_features=body.product_features,
            target_audience=body.target_audience,
            db=db,
        )
        return result
    except Exception as e:
        logger.error("headlines_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Generowanie naglowkow nie powiodlo sie")


@router.post("/hooks")
@limiter.limit("5/minute")
async def generate_hooks_endpoint(
    request: Request,
    body: ProductRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Generate 5 video hooks using Michael Diaz's 3-element formula. Admin/beta only."""
    try:
        result = await generate_hooks(
            product_title=body.product_title,
            product_features=body.product_features,
            target_audience=body.target_audience,
            db=db,
        )
        return result
    except Exception as e:
        logger.error("hooks_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Generowanie hookow nie powiodlo sie")


@router.post("/brief")
@limiter.limit("3/minute")
async def generate_brief_endpoint(
    request: Request,
    body: ProductRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Generate an 11-step creative brief. Admin/beta only."""
    try:
        result = await generate_brief(
            product_title=body.product_title,
            product_features=body.product_features,
            target_audience=body.target_audience,
            db=db,
        )
        return result
    except Exception as e:
        logger.error("brief_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Generowanie briefu nie powiodlo sie")
