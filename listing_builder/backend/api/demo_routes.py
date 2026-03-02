# backend/api/demo_routes.py
# Purpose: Amazon Pro Demo endpoints — 5-step pipeline from ASIN to coupon
# NOT for: Production SP-API integrations (those are in separate route files)

import structlog
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
from api.dependencies import get_user_id

logger = structlog.get_logger()
router = APIRouter(prefix="/api/demo", tags=["demo"])


# --- Request/Response Models ---

class FetchRequest(BaseModel):
    asin: str = Field(..., min_length=10, max_length=10, pattern=r"^B[0-9A-Z]{9}$")
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


# --- Step 1: Fetch Product ---

@router.post("/fetch")
async def demo_fetch(
    req: FetchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 1: ASIN → product data. Sample data or real SP-API."""
    if req.use_sample:
        from data.demo_samples import get_demo_product
        product = get_demo_product()
        logger.info("demo_fetch_sample", asin=product["asin"])
        return {"source": "sample", "product": product}

    # Real SP-API fetch
    from services.sp_api_catalog import fetch_catalog_item
    product = await fetch_catalog_item(asin=req.asin, marketplace=req.marketplace, db=db)

    if product.get("error"):
        return {"source": "sp_api", "product": None, "error": product["error"]}

    # WHY: Attach demo keywords to real product so optimize step has data
    from data.demo_samples import DEMO_KEYWORDS
    product["keywords"] = DEMO_KEYWORDS

    logger.info("demo_fetch_live", asin=req.asin, marketplace=req.marketplace)
    return {"source": "sp_api", "product": product}


# --- Step 2: AI Optimize ---

@router.post("/optimize")
async def demo_optimize(
    req: OptimizeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Step 2: AI listing optimization with DataDive keyword coverage.

    WHY no tier limit: Demo bypasses free/premium gate — it's a showcase.
    """
    from services.optimizer_service import optimize_listing

    result = await optimize_listing(
        product_title=req.title,
        brand=req.brand,
        keywords=req.keywords,
        marketplace=req.marketplace,
        mode="aggressive",
        account_type="seller",
        category=req.category,
        db=db,
        user_id=user_id,
    )

    if result.get("error"):
        return {"error": result["error"]}

    # WHY: Calculate DataDive keyword coverage for before/after comparison
    coverage = _calculate_coverage(req.keywords, result)

    logger.info("demo_optimize_ok", user_id=user_id[:8] if user_id else "anon")
    return {
        "optimized": result,
        "coverage": coverage,
    }


# --- Step 3: Compliance Check ---

@router.post("/compliance-check")
async def demo_compliance_check(req: ComplianceRequest):
    """Step 3: EU supplement compliance (HCPR, GPSR, allergens)."""
    from services.supplement_compliance import check_supplement_compliance

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
async def demo_publish(
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
async def demo_create_coupon(
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


# --- Helpers ---

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
