# backend/api/attribute_routes.py
# Purpose: Auto-Atrybuty API endpoints — category search, params, generate, history
# NOT for: LLM logic (attribute_service.py) or Allegro API calls (allegro_categories.py)

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from api.dependencies import get_user_id
from api.attribute_schemas import (
    CategoryItem, CategorySearchResponse, ParameterOption, CategoryParameter,
    CategoryParametersResponse, AttributeGenerateRequest, AttributeGenerateResponse,
    AttributeHistoryItem, AttributeHistoryResponse,
)
from services.allegro_categories import search_categories, fetch_category_parameters
from services.attribute_service import generate_attributes
from models.attribute_run import AttributeRun

logger = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/attributes", tags=["attributes"])


# --- Endpoints ---

@router.get("/categories", response_model=CategorySearchResponse)
@limiter.limit("10/minute")
async def search_allegro_categories(
    request: Request,
    query: str = Query(..., max_length=500),
    user_id: str = Depends(get_user_id),
) -> CategorySearchResponse:
    """Search Allegro categories matching a product name."""
    if len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query musi mieć minimum 2 znaki")

    categories = await search_categories(query.strip())
    return CategorySearchResponse(
        categories=[CategoryItem(**c) for c in categories],
    )


@router.get("/categories/{category_id}/parameters", response_model=CategoryParametersResponse)
@limiter.limit("10/minute")
async def get_category_parameters(
    request: Request,
    category_id: str,
    user_id: str = Depends(get_user_id),
) -> CategoryParametersResponse:
    """Fetch all parameters for an Allegro category."""
    # WHY: Allegro category IDs are numeric — reject anything else to prevent injection
    if not category_id.isdigit():
        raise HTTPException(status_code=400, detail="Nieprawidłowe ID kategorii")
    params = await fetch_category_parameters(category_id)
    return CategoryParametersResponse(
        parameters=[CategoryParameter(
            id=p["id"],
            name=p["name"],
            type=p["type"],
            required=p["required"],
            unit=p.get("unit"),
            options=[ParameterOption(**o) for o in p.get("options", [])],
        ) for p in params],
        category_id=category_id,
    )


@router.post("/generate", response_model=AttributeGenerateResponse)
@limiter.limit("5/minute")
async def generate_product_attributes(
    request: Request,
    body: AttributeGenerateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> AttributeGenerateResponse:
    """Generate product attributes for a given category using AI."""
    # WHY: Allegro category IDs are numeric — reject non-numeric to prevent injection
    if not body.category_id.isdigit():
        raise HTTPException(status_code=400, detail="Nieprawidłowe ID kategorii")

    client_ip = get_remote_address(request)

    try:
        result = await generate_attributes(
            product_input=body.product_input,
            category_id=body.category_id,
            category_name=body.category_name,
            category_path=body.category_path,
            marketplace=body.marketplace,
            user_id=user_id,
            client_ip=client_ip,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return AttributeGenerateResponse(**result)


@router.get("/history", response_model=AttributeHistoryResponse)
@limiter.limit("10/minute")
async def get_attribute_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> AttributeHistoryResponse:
    """Get paginated attribute generation history for the current user."""
    total = db.query(AttributeRun).filter(AttributeRun.user_id == user_id).count()
    runs = (
        db.query(AttributeRun)
        .filter(AttributeRun.user_id == user_id)
        .order_by(AttributeRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return AttributeHistoryResponse(
        items=[
            AttributeHistoryItem(
                id=r.id,
                product_input=r.product_input,
                marketplace=r.marketplace or "allegro",
                category_name=r.category_name,
                category_path=r.category_path,
                params_count=r.params_count or 0,
                attributes=r.attributes or [],
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in runs
        ],
        total=total,
    )


@router.delete("/history/{run_id}", status_code=204)
@limiter.limit("10/minute")
async def delete_attribute_history(
    request: Request,
    run_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> None:
    """Delete an attribute generation run. IDOR-safe: filters by user_id."""
    run = (
        db.query(AttributeRun)
        .filter(AttributeRun.id == run_id, AttributeRun.user_id == user_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Nie znaleziono")

    db.delete(run)
    db.commit()
