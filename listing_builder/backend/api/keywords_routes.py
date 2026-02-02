# backend/api/keywords_routes.py
# Purpose: Mock keywords endpoint — search volume, rank tracking, relevance
# NOT for: Real keyword data (swap to DB when rank-tracker integrations arrive)

from fastapi import APIRouter, Query
from schemas import KeywordsResponse, KeywordItem
from typing import Optional

router = APIRouter(prefix="/api/keywords", tags=["Keywords"])

# In-memory mock data — 15 keywords across 5 marketplaces
MOCK_KEYWORDS: list[dict] = [
    {"id": "kw-001", "keyword": "wireless headphones", "search_volume": 245000, "current_rank": 3, "marketplace": "Amazon", "trend": "up", "relevance_score": 95, "last_updated": "2026-02-01T10:00:00Z"},
    {"id": "kw-002", "keyword": "bluetooth earbuds", "search_volume": 189000, "current_rank": 7, "marketplace": "Amazon", "trend": "up", "relevance_score": 92, "last_updated": "2026-02-01T10:00:00Z"},
    {"id": "kw-003", "keyword": "usb c cable", "search_volume": 320000, "current_rank": 12, "marketplace": "Amazon", "trend": "stable", "relevance_score": 88, "last_updated": "2026-02-01T10:00:00Z"},
    {"id": "kw-004", "keyword": "leather wallet", "search_volume": 98000, "current_rank": 5, "marketplace": "eBay", "trend": "down", "relevance_score": 90, "last_updated": "2026-02-01T08:30:00Z"},
    {"id": "kw-005", "keyword": "mens wallet bifold", "search_volume": 54000, "current_rank": 2, "marketplace": "eBay", "trend": "up", "relevance_score": 85, "last_updated": "2026-02-01T08:30:00Z"},
    {"id": "kw-006", "keyword": "water bottle stainless", "search_volume": 167000, "current_rank": None, "marketplace": "eBay", "trend": "stable", "relevance_score": 78, "last_updated": "2026-02-01T08:30:00Z"},
    {"id": "kw-007", "keyword": "bed sheets queen", "search_volume": 210000, "current_rank": 8, "marketplace": "Walmart", "trend": "up", "relevance_score": 91, "last_updated": "2026-02-01T11:00:00Z"},
    {"id": "kw-008", "keyword": "organic cotton sheets", "search_volume": 87000, "current_rank": 15, "marketplace": "Walmart", "trend": "stable", "relevance_score": 82, "last_updated": "2026-02-01T11:00:00Z"},
    {"id": "kw-009", "keyword": "nonstick frying pan", "search_volume": 143000, "current_rank": 22, "marketplace": "Walmart", "trend": "down", "relevance_score": 75, "last_updated": "2026-02-01T11:00:00Z"},
    {"id": "kw-010", "keyword": "soy candle lavender", "search_volume": 34000, "current_rank": 1, "marketplace": "Shopify", "trend": "up", "relevance_score": 97, "last_updated": "2026-02-01T07:00:00Z"},
    {"id": "kw-011", "keyword": "handmade candles", "search_volume": 78000, "current_rank": 4, "marketplace": "Shopify", "trend": "stable", "relevance_score": 89, "last_updated": "2026-02-01T07:00:00Z"},
    {"id": "kw-012", "keyword": "desk organizer wood", "search_volume": 45000, "current_rank": None, "marketplace": "Shopify", "trend": "down", "relevance_score": 72, "last_updated": "2026-02-01T07:00:00Z"},
    {"id": "kw-013", "keyword": "plecak turystyczny", "search_volume": 28000, "current_rank": 6, "marketplace": "Allegro", "trend": "up", "relevance_score": 94, "last_updated": "2026-02-01T12:00:00Z"},
    {"id": "kw-014", "keyword": "plecak wodoodporny", "search_volume": 15000, "current_rank": 9, "marketplace": "Allegro", "trend": "stable", "relevance_score": 86, "last_updated": "2026-02-01T12:00:00Z"},
    {"id": "kw-015", "keyword": "zestaw narzedzi", "search_volume": 42000, "current_rank": 18, "marketplace": "Allegro", "trend": "down", "relevance_score": 70, "last_updated": "2026-02-01T12:00:00Z"},
]


@router.get("", response_model=KeywordsResponse)
async def get_keywords(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    search: Optional[str] = Query(None, description="Search keyword text"),
):
    """
    List tracked keywords with rank, volume, and relevance data.
    Summary stats are computed from the FULL dataset (before filtering).
    """
    all_items = [KeywordItem(**kw) for kw in MOCK_KEYWORDS]

    # Summary stats from full dataset
    tracked_count = sum(1 for kw in all_items if kw.current_rank is not None)
    top_10_count = sum(1 for kw in all_items if kw.current_rank is not None and kw.current_rank <= 10)
    avg_relevance = round(sum(kw.relevance_score for kw in all_items) / len(all_items), 1)

    # Apply filters for the table view
    filtered = all_items
    if marketplace:
        filtered = [kw for kw in filtered if kw.marketplace == marketplace]
    if search:
        q = search.lower()
        filtered = [kw for kw in filtered if q in kw.keyword.lower()]

    return KeywordsResponse(
        keywords=filtered,
        total=len(filtered),
        tracked_count=tracked_count,
        top_10_count=top_10_count,
        avg_relevance=avg_relevance,
    )
