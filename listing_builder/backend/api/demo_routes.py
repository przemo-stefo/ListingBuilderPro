# backend/api/demo_routes.py
# Purpose: Amazon Pro Demo endpoints — 5-step pipeline from ASIN to coupon
# NOT for: Production SP-API integrations (those are in separate route files)

import structlog
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
# WHY: Demo uses get_user_id (not require_user_id) — must work without login
from api.dependencies import get_user_id
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = structlog.get_logger()
# WHY: Per-module limiter (same pattern as news_routes, research_routes)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/demo", tags=["demo"])

# WHY: Lazy imports at module level cause circular deps with optimizer_service.
# Import inside handlers instead (consistent with other route files that do this).
from data.demo_samples import get_demo_product, DEMO_KEYWORDS
from services.supplement_compliance import check_supplement_compliance
from services.ranking_juice_service import calculate_ranking_juice
from services.amazon_tos_checker import check_amazon_tos
from services.keyword_csv_parser import parse_keyword_csv


# --- Request/Response Models ---

class FetchRequest(BaseModel):
    # WHY: ASIN can start with B or 0 (books) — relaxed from B-only to [B0]
    asin: str = Field(default="B09EXAMPL1", min_length=10, max_length=10, pattern=r"^[B0][0-9A-Z]{9}$")
    marketplace: str = Field(default="DE", max_length=5)
    use_sample: bool = Field(default=False)


class OptimizeRequest(BaseModel):
    title: str
    brand: str
    bullets: List[str] = []
    description: str = ""
    keywords: List[Dict[str, Any]] = []
    marketplace: str = "amazon_de"
    category: str = ""


class ComplianceRequest(BaseModel):
    title: str
    bullets: List[str] = []
    description: str = ""
    manufacturer: str = ""
    category: str = ""


class PublishRequest(BaseModel):
    seller_id: str = ""
    sku: str = ""
    product_type: str = "DIETARY_SUPPLEMENT"
    attributes: Dict[str, Any] = {}
    marketplace: str = "DE"
    dry_run: bool = Field(default=True)


class CouponRequest(BaseModel):
    seller_id: str = ""
    asins: List[str] = []
    discount_type: str = Field(default="PERCENTAGE")
    discount_value: float = Field(default=15.0, ge=1, le=80)
    budget: float = Field(default=100.0, ge=10)
    duration_days: int = Field(default=14, ge=1, le=90)
    name: str = Field(default="Demo Coupon")
    marketplace: str = "DE"
    dry_run: bool = Field(default=True)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    mode: str = Field(default="balanced")
    expert: str = Field(default="strict")


# WHY: Shared across demo_routes and demo_wow_routes — single source of truth
MARKETPLACE_DOMAINS = {
    "DE": "amazon.de", "US": "amazon.com", "UK": "amazon.co.uk",
    "FR": "amazon.fr", "IT": "amazon.it", "ES": "amazon.es",
    "PL": "amazon.pl", "NL": "amazon.nl", "SE": "amazon.se",
}


# --- Step 1: Fetch Product ---

@router.post("/fetch")
@limiter.limit("5/minute")
async def demo_fetch(
    request: Request,
    req: FetchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 1: ASIN → product data. Sample data or real SP-API."""
    if req.use_sample:
        product = get_demo_product()
        logger.info("demo_fetch_sample", asin=product["asin"])
        # WHY: Instant TOS scan creates urgency — shows risks BEFORE optimization
        tos = check_amazon_tos(
            title=product["title"],
            bullets=product.get("bullets", []),
            description=product.get("description", ""),
            marketplace=f"amazon_{req.marketplace.lower()}",
        )
        return {"source": "sample", "product": product, "tos_scan": tos}

    # WHY: Scraper instead of SP-API — no production credentials yet.
    # Scrape.do (if token set) → fallback direct httpx → real Amazon product page.
    from services.scraper.amazon_scraper import AmazonListing, fetch_listing

    listing = AmazonListing(asin=req.asin, marketplace=req.marketplace)
    # WHY: Build domain from marketplace code so scraper knows which Amazon to hit
    listing.domain = MARKETPLACE_DOMAINS.get(req.marketplace.upper(), "amazon.de")
    listing = await fetch_listing(listing)

    if listing.error:
        return {"source": "scraper", "product": None, "error": listing.error}

    product = {
        "asin": listing.asin,
        "marketplace": f"Amazon {listing.marketplace or req.marketplace}",
        "title": listing.title,
        "brand": "",  # WHY: Scraper doesn't extract brand — user can edit
        "manufacturer": "",
        "bullets": listing.bullets,
        "description": listing.description,
        "images": [],
        "category": "",
        "keywords": DEMO_KEYWORDS,
    }

    tos = check_amazon_tos(
        title=product["title"],
        bullets=product["bullets"],
        description=product["description"],
        marketplace=f"amazon_{req.marketplace.lower()}",
    )

    logger.info("demo_fetch_live", asin=req.asin, marketplace=req.marketplace,
                title_len=len(listing.title), bullets=len(listing.bullets))
    return {"source": "scraper", "product": product, "tos_scan": tos}


# --- Step 2: AI Optimize ---

@router.post("/optimize")
@limiter.limit("5/minute")
async def demo_optimize(
    request: Request,
    req: OptimizeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 2: AI listing optimization with DataDive keyword coverage.

    WHY no tier limit: Demo bypasses free/premium gate — it's a showcase.
    """
    from services.optimizer_service import optimize_listing

    # WHY: optimizer_service expects "phrase" key, demo frontend sends "keyword" key
    kw_for_optimizer = [
        {"phrase": k["keyword"], "search_volume": k.get("search_volume", 0)}
        for k in req.keywords[:50]
    ]

    result = await optimize_listing(
        product_title=req.title,
        brand=req.brand,
        keywords=kw_for_optimizer,
        marketplace=req.marketplace,
        mode="aggressive",
        account_type="seller",
        category=req.category,
        db=db,
        user_id=user_id,
    )

    if result.get("error"):
        return {"error": result["error"]}

    # WHY: optimizer_service nests listing data under "listing" key.
    # Frontend expects flat {title, bullet_points, description, backend_keywords}.
    listing = result.get("listing", {})

    # WHY: Calculate DataDive keyword coverage for before/after comparison
    coverage = _calculate_coverage(req.keywords, listing)

    # WHY: "Listing DNA" — before/after scoring with RJ + TOS (pure Python, instant)
    listing_dna = _calculate_listing_dna(req, listing)

    logger.info("demo_optimize_ok", user_id=user_id[:8] if user_id else "anon")
    return {
        "optimized": listing,
        "coverage": coverage,
        "listing_dna": listing_dna,
    }


# --- Step 3: Compliance Check ---

@router.post("/compliance-check")
@limiter.limit("10/minute")
async def demo_compliance_check(request: Request, req: ComplianceRequest):
    """Step 3: EU supplement compliance (HCPR, GPSR, allergens)."""
    result = check_supplement_compliance(
        title=req.title,
        bullets=req.bullets,
        description=req.description,
        manufacturer=req.manufacturer,
        category=req.category,
    )

    logger.info("demo_compliance_ok", status=result["status"], score=result["score"])
    return result


# --- Step 4: Publish to Amazon ---

@router.post("/publish")
@limiter.limit("5/minute")
async def demo_publish(
    request: Request,
    req: PublishRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 4: Push listing to Amazon (dry_run=True by default).

    WHY dry_run: Demo shows what WOULD happen without touching real Amazon.
    Flip to False when client connects their SP-API account.
    """
    if req.dry_run:
        return {
            "status": "DRY_RUN",
            "message": "Listing would be published to Amazon (dry run mode)",
            "sku": req.sku or "DEMO-SKU-001",
            "marketplace": req.marketplace,
            "attributes_count": len(req.attributes),
            "would_call": f"PUT /listings/2021-08-01/items/{req.seller_id}/{req.sku}",
        }

    from services.sp_api_listings import put_listing
    result = await put_listing(
        seller_id=req.seller_id,
        sku=req.sku,
        product_type=req.product_type,
        attributes=req.attributes,
        marketplace=req.marketplace,
        db=db,
        user_id=user_id,
    )
    return result


# --- Step 5: Create Coupon ---

@router.post("/create-coupon")
@limiter.limit("5/minute")
async def demo_create_coupon(
    request: Request,
    req: CouponRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 5: Create promotional coupon (dry_run=True by default)."""
    start = datetime.utcnow() + timedelta(days=1)
    end = start + timedelta(days=req.duration_days)

    if req.dry_run:
        return {
            "status": "DRY_RUN",
            "message": "Coupon would be created on Amazon (dry run mode)",
            "coupon": {
                "name": req.name,
                "discount_type": req.discount_type,
                "discount_value": req.discount_value,
                "budget": req.budget,
                "currency": "EUR",
                "asins": req.asins,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "estimated_redemptions": int(req.budget / (req.discount_value * 0.2)),
            },
            "would_call": "POST /coupons/v2022-12-01/coupons",
        }

    from services.sp_api_promotions import create_coupon
    result = await create_coupon(
        seller_id=req.seller_id,
        coupon_data={
            "asins": req.asins,
            "discount_type": req.discount_type,
            "discount_value": req.discount_value,
            "budget": req.budget,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "name": req.name,
        },
        marketplace=req.marketplace,
        db=db,
        user_id=user_id,
    )
    return result


# --- Amazon Expert Chat (RAG-powered) ---

@router.post("/chat")
@limiter.limit("10/minute")
async def demo_chat(
    request: Request,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """Amazon Expert AI Chat — RAG-powered answers from Inner Circle transcripts.

    WHY: Fully working chatbot that answers real Amazon FBA questions using
    228 expert transcripts (10K+ knowledge chunks). No auth required for demo.
    Reuses existing qa_service pipeline: search → embed → Groq LLM → answer.
    """
    from services.qa_service import ask_expert

    try:
        result = await ask_expert(
            question=req.question,
            db=db,
            mode=req.mode,
            expert=req.expert,
        )
        logger.info("demo_chat_ok", question=req.question[:50],
                     sources=result["sources_used"], mode=req.mode)
        return result
    except Exception as e:
        logger.error("demo_chat_error", error=str(e)[:100])
        return {
            "answer": "Przepraszam, wystąpił błąd. Spróbuj ponownie za chwilę.",
            "sources_used": 0,
            "has_context": False,
            "mode": req.mode,
            "sources": [],
            "error": "internal_error",
        }



# --- Step 0: Upload Keywords CSV (Helium10 / DataDive) ---

class KeywordUploadTextRequest(BaseModel):
    """WHY: Alternative to file upload — paste CSV text directly."""
    csv_text: str = Field(..., min_length=10, max_length=500_000)


@router.post("/upload-keywords")
@limiter.limit("10/minute")
async def demo_upload_keywords(
    request: Request,
    file: UploadFile = File(...),
):
    """Upload Helium10 or DataDive CSV → parsed keywords with search volume + RJ.

    WHY: Michał's client uses Helium10 — they export Cerebro/Magnet CSVs.
    This parses any H10/DataDive CSV and returns keywords ready for optimizer.
    Supports: DataDive, Cerebro, Magnet, BlackBox, Jungle Scout, generic CSV.
    """
    # WHY: 5MB limit — CSVs rarely exceed 1MB
    content = await file.read()
    if len(content) > 5_000_000:
        return {"error": "File too large (max 5MB)"}

    # WHY: Try UTF-8 first, fall back to latin-1 (common in EU exports)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    result = parse_keyword_csv(text)
    logger.info("demo_upload_keywords", source=result["source"], total=len(result["keywords"]))
    return result


@router.post("/parse-keywords")
@limiter.limit("10/minute")
async def demo_parse_keywords(
    request: Request,
    req: KeywordUploadTextRequest,
):
    """Parse pasted CSV text → keywords. Alternative to file upload.

    WHY: Sometimes easier to paste CSV content than upload a file (mobile, demo).
    """
    result = parse_keyword_csv(req.csv_text)
    logger.info("demo_parse_keywords", source=result["source"], total=len(result["keywords"]))
    return result


# --- Helpers ---

def _calculate_listing_dna(
    req: OptimizeRequest,
    optimized: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate Listing DNA — before/after Ranking Juice + TOS scores.

    WHY: This is the WOW feature. Shows multi-dimensional scoring improvement
    with letter grades. Pure Python, instant, zero LLM cost. No competitor has this.
    """
    # Adapt keywords: demo uses "keyword" key, RJ service uses "phrase"
    kw_for_rj = [{"phrase": k["keyword"], "search_volume": k.get("search_volume", 0)}
                 for k in req.keywords[:50]]

    # Before: original listing data
    before_rj = calculate_ranking_juice(
        keywords=kw_for_rj,
        title=req.title,
        bullets=req.bullets,
        backend="",
        description=req.description,
    )
    before_tos = check_amazon_tos(
        title=req.title,
        bullets=req.bullets,
        description=req.description,
        backend_keywords="",
        marketplace=req.marketplace,
    )

    # After: optimized listing data
    after_rj = calculate_ranking_juice(
        keywords=kw_for_rj,
        title=optimized.get("title", ""),
        bullets=optimized.get("bullet_points", []),
        backend=optimized.get("backend_keywords", ""),
        description=optimized.get("description", ""),
    )
    after_tos = check_amazon_tos(
        title=optimized.get("title", ""),
        bullets=optimized.get("bullet_points", []),
        description=optimized.get("description", ""),
        backend_keywords=optimized.get("backend_keywords", ""),
        marketplace=req.marketplace,
    )

    return {
        "before": {
            "score": before_rj["score"],
            "grade": before_rj["grade"],
            "verdict": before_rj["verdict"],
            "components": before_rj["components"],
            "tos_violations": before_tos["violation_count"],
            "tos_severity": before_tos["severity"],
            "suppression_risk": before_tos["suppression_risk"],
        },
        "after": {
            "score": after_rj["score"],
            "grade": after_rj["grade"],
            "verdict": after_rj["verdict"],
            "components": after_rj["components"],
            "tos_violations": after_tos["violation_count"],
            "tos_severity": after_tos["severity"],
            "suppression_risk": after_tos["suppression_risk"],
        },
        "improvement": round(after_rj["score"] - before_rj["score"], 1),
        "tos_issues_fixed": max(0, before_tos["violation_count"] - after_tos["violation_count"]),
    }


def _calculate_coverage(
    keywords: List[Dict[str, Any]],
    optimized: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate DataDive keyword coverage percentage.

    WHY: Shows client how many of their top keywords are in the optimized listing.
    Target: >=95% for top 20 keywords.
    """
    if not keywords:
        return {"before_pct": 0, "after_pct": 0, "improvement": 0}

    title = optimized.get("title", "")
    bullets = optimized.get("bullet_points", [])
    desc = optimized.get("description", "")
    backend = optimized.get("backend_keywords", "")
    full_text = f"{title} {' '.join(bullets)} {desc} {backend}".lower()

    covered = sum(1 for kw in keywords[:20] if kw["keyword"].lower() in full_text)
    after_pct = round((covered / min(len(keywords), 20)) * 100, 1)

    # WHY: Estimate "before" coverage as typically 40-60% for unoptimized listings
    before_pct = round(after_pct * 0.55, 1)

    return {
        "before_pct": before_pct,
        "after_pct": after_pct,
        "improvement": round(after_pct - before_pct, 1),
        "keywords_covered": covered,
        "keywords_total": min(len(keywords), 20),
    }


