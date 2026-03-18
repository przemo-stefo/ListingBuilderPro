# backend/api/validator_routes.py
# Purpose: Product Validator API endpoints — analyze, history, delete
# NOT for: LLM logic (validator_service.py) or data fetching (validator_data_sources.py)

from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Literal
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from api.dependencies import get_user_id
from services.validator_service import analyze_product
from models.validator import ValidationRun

logger = structlog.get_logger()

# WHY: 5/min prevents Groq/Beast token burn from abuse
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/validator", tags=["validator"])


# WHY: Whitelist prevents garbage/injection in marketplace field reaching LLM prompt + DB
VALID_MARKETPLACES = ("amazon", "allegro", "both")


class ValidatorRequest(BaseModel):
    product_input: str = Field(..., min_length=1, max_length=500)
    marketplace: Literal["amazon", "allegro", "both"] = "amazon"


class ValidatorDimension(BaseModel):
    name: str
    score: int
    comment: str


class ValidatorResponse(BaseModel):
    id: int
    product_input: str
    input_type: str
    marketplace: str
    score: int
    verdict: str
    explanation: str
    dimensions: list[ValidatorDimension]
    provider_used: str
    latency_ms: int
    created_at: str | None


class ValidatorHistoryItem(BaseModel):
    id: int
    product_input: str
    marketplace: str
    score: int
    verdict: str
    explanation: str
    created_at: str | None


class ValidatorHistoryResponse(BaseModel):
    items: list[ValidatorHistoryItem]
    total: int


@router.post("/analyze", response_model=ValidatorResponse)
@limiter.limit("5/minute")
async def analyze(
    request: Request,
    body: ValidatorRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Analyze product potential using AI + market data."""
    client_ip = request.client.host if request.client else None

    try:
        result = await analyze_product(
            product_input=body.product_input,
            marketplace=body.marketplace,
            user_id=user_id,
            client_ip=client_ip,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("validator_analyze_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analiza nie powiodła się")


@router.get("/history", response_model=ValidatorHistoryResponse)
@limiter.limit("10/minute")
async def get_history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Get user's validation history (paginated)."""
    # WHY: Cap at 50 to prevent oversized payloads
    limit = min(limit, 50)

    total = db.query(ValidationRun).filter(ValidationRun.user_id == user_id).count()
    runs = (
        db.query(ValidationRun)
        .filter(ValidationRun.user_id == user_id)
        .order_by(ValidationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        ValidatorHistoryItem(
            id=r.id,
            product_input=r.product_input,
            marketplace=r.marketplace,
            score=r.score,
            verdict=r.verdict,
            explanation=r.explanation,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in runs
    ]

    return ValidatorHistoryResponse(items=items, total=total)


@router.delete("/history/{run_id}")
@limiter.limit("10/minute")
async def delete_history(
    request: Request,
    run_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Delete a validation run. IDOR protection: filters by user_id + id."""
    run = (
        db.query(ValidationRun)
        .filter(ValidationRun.id == run_id, ValidationRun.user_id == user_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono")

    db.delete(run)
    db.commit()
    return {"detail": "Usunięto"}
