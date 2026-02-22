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
from services.scraper.amazon_scraper import parse_input
from services.sp_api_catalog import fetch_catalog_item

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


class FetchRequest(BaseModel):
    input: str = Field(..., min_length=2, max_length=500, description="Amazon URL or ASIN")


class FetchResponse(BaseModel):
    asin: str = ""
    marketplace: str = ""
    title: str = ""
    bullets: list[str] = []
    description: str = ""
    url: str = ""
    error: str = ""


@router.post("/fetch", response_model=FetchResponse)
@limiter.limit("10/minute")
async def fetch_listing_endpoint(request: Request, body: FetchRequest):
    """Parse Amazon URL/ASIN, detect marketplace, fetch listing data via SP-API."""
    parsed = parse_input(body.input)

    if parsed.error and not parsed.asin:
        return FetchResponse(error=parsed.error)

    # WHY: Use SP-API Catalog Items (official API) instead of HTML scraping
    # — reliable, structured data, no anti-bot issues
    marketplace = parsed.marketplace or "DE"
    if parsed.asin:
        catalog = await fetch_catalog_item(parsed.asin, marketplace)
        if catalog.get("error"):
            return FetchResponse(
                asin=parsed.asin, marketplace=marketplace,
                url=parsed.url, error=catalog["error"],
            )
        return FetchResponse(
            asin=parsed.asin,
            marketplace=marketplace,
            title=catalog.get("title", ""),
            bullets=catalog.get("bullets", []),
            description=catalog.get("description", ""),
            url=parsed.url or f"https://www.amazon.{parsed.domain or 'de'}/dp/{parsed.asin}",
        )

    return FetchResponse(asin=parsed.asin, marketplace=marketplace, url=parsed.url)


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
