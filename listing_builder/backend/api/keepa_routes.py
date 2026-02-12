# backend/api/keepa_routes.py
# Purpose: Keepa API endpoints — product lookup, batch, Buy Box, token status
# NOT for: Direct Amazon SP-API calls or stored monitoring data (use monitoring_routes)

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.keepa_service import get_product, get_products_batch, get_buybox_history, check_tokens_left

router = APIRouter(prefix="/api/keepa", tags=["Keepa"])


@router.get("/product")
async def lookup_product(
    asin: str = Query(..., description="Amazon ASIN to look up"),
    domain: str = Query("amazon.de", description="Amazon domain (e.g. amazon.de, amazon.com)"),
):
    """Look up a single product: price, Buy Box, rating, stock."""
    result = await get_product(asin, domain)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Product {asin} not found or Keepa API key missing")
    return result


@router.get("/products")
async def lookup_products_batch(
    asins: str = Query(..., description="Comma-separated ASINs (max 100)"),
    domain: str = Query("amazon.de", description="Amazon domain"),
):
    """Batch lookup up to 100 products in one call."""
    asin_list = [a.strip() for a in asins.split(",") if a.strip()]
    if not asin_list:
        raise HTTPException(status_code=400, detail="No ASINs provided")
    if len(asin_list) > 100:
        raise HTTPException(status_code=400, detail="Max 100 ASINs per request")

    results = await get_products_batch(asin_list, domain)
    return {"products": results, "count": len(results)}


@router.get("/buybox")
async def lookup_buybox(
    asin: str = Query(..., description="Amazon ASIN"),
    domain: str = Query("amazon.de", description="Amazon domain"),
):
    """Get Buy Box history and current seller info."""
    result = await get_buybox_history(asin, domain)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Buy Box data not found for {asin}")
    return result


@router.get("/tokens")
async def get_token_status():
    """Check remaining Keepa API tokens (rate limit)."""
    return await check_tokens_left()
