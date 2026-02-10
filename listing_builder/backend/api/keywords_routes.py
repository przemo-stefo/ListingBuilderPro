# backend/api/keywords_routes.py
# Purpose: CRUD endpoints for tracked keyword rankings and search volumes
# NOT for: Keyword extraction from optimizer (that's in optimizer_service.py)

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from database import get_db
from models.listing import TrackedKeyword
from schemas import KeywordCreate, KeywordItem, KeywordsResponse

router = APIRouter(prefix="/api/keywords", tags=["Keywords"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=KeywordsResponse)
async def get_keywords(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace name"),
    search: Optional[str] = Query(None, description="Search keyword text"),
    db: Session = Depends(get_db),
):
    """
    List tracked keywords with rank, volume, and relevance data.
    Summary stats are computed from the FULL dataset (before filtering).
    """
    all_query = db.query(TrackedKeyword)
    total_count = all_query.count()

    # WHY full-dataset stats: dashboard cards must stay consistent
    tracked_count = all_query.filter(TrackedKeyword.current_rank.isnot(None)).count()
    top_10_count = all_query.filter(
        TrackedKeyword.current_rank.isnot(None),
        TrackedKeyword.current_rank <= 10,
    ).count()

    avg_relevance = 0.0
    if total_count > 0:
        avg_val = db.query(sa_func.avg(TrackedKeyword.relevance_score)).scalar()
        avg_relevance = round(float(avg_val or 0), 1)

    # Apply filters for the table view
    filtered = all_query
    if marketplace:
        filtered = filtered.filter(TrackedKeyword.marketplace == marketplace)
    if search:
        # WHY ilike: case-insensitive partial match
        filtered = filtered.filter(TrackedKeyword.keyword.ilike(f"%{search}%"))

    items = filtered.order_by(TrackedKeyword.last_updated.desc()).all()

    keyword_items = [
        KeywordItem(
            id=str(row.id),
            keyword=row.keyword,
            search_volume=row.search_volume,
            current_rank=row.current_rank,
            marketplace=row.marketplace,
            trend=row.trend,
            relevance_score=row.relevance_score,
            last_updated=row.last_updated.isoformat() if row.last_updated else None,
        )
        for row in items
    ]

    return KeywordsResponse(
        keywords=keyword_items,
        total=len(keyword_items),
        tracked_count=tracked_count,
        top_10_count=top_10_count,
        avg_relevance=avg_relevance,
    )


@router.post("", response_model=KeywordItem, status_code=201)
@limiter.limit("20/minute")
async def create_keyword(
    request: Request,
    body: KeywordCreate,
    db: Session = Depends(get_db),
):
    """Add a keyword to track."""
    existing = (
        db.query(TrackedKeyword)
        .filter(TrackedKeyword.keyword == body.keyword, TrackedKeyword.marketplace == body.marketplace)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Keyword already tracked for this marketplace")

    kw = TrackedKeyword(
        keyword=body.keyword,
        marketplace=body.marketplace,
        search_volume=body.search_volume,
        current_rank=body.current_rank,
        trend=body.trend.value,
        relevance_score=body.relevance_score,
    )
    db.add(kw)
    db.commit()
    db.refresh(kw)

    return KeywordItem(
        id=str(kw.id),
        keyword=kw.keyword,
        search_volume=kw.search_volume,
        current_rank=kw.current_rank,
        marketplace=kw.marketplace,
        trend=kw.trend,
        relevance_score=kw.relevance_score,
        last_updated=kw.last_updated.isoformat() if kw.last_updated else None,
    )


@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """Stop tracking a keyword."""
    kw = db.query(TrackedKeyword).filter(TrackedKeyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")

    db.delete(kw)
    db.commit()
    return {"status": "deleted", "id": keyword_id}
