# backend/api/media_gen_routes.py
# Purpose: API endpoints for background media generation + history + feedback
# NOT for: Generation logic (services/media_gen_worker.py) or model defs

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from models.jobs import JobStatus
from models.media_generation import MediaGeneration
from api.dependencies import require_user_id
from services.media_gen_worker import run_image_generation, run_video_generation

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/media-gen", tags=["media-gen"])


class StartImageRequest(BaseModel):
    media_type: str = Field(..., pattern="^(video|images)$")
    product_name: Optional[str] = Field(default=None, max_length=500)
    brand: Optional[str] = Field(default=None, max_length=200)
    bullet_points: List[str] = Field(default_factory=list)
    description: str = Field(default="")
    theme: str = Field(default="dark_premium", pattern="^(dark_premium|light|amazon_white)$")
    llm_provider: Optional[str] = Field(default=None, pattern="^(beast|groq|openai|anthropic)$")
    # Video generation params (TikTok 9:16 templates)
    template: str = Field(default="product_highlight", pattern="^(product_highlight|feature_breakdown|sale_promo)$")
    features: List[str] = Field(default_factory=list)
    image_url: Optional[str] = Field(default=None, max_length=2000)
    original_price: Optional[str] = Field(default=None, max_length=50)
    sale_price: Optional[str] = Field(default=None, max_length=50)


class JobStatusResponse(BaseModel):
    id: int
    status: str
    media_type: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=2000)


@router.post("/start")
@limiter.limit("5/minute")
async def start_generation(
    request: Request,
    body: StartImageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Start background media generation. Returns job ID immediately."""
    # WHY: Both video and images require product_name + brand
    if not body.product_name or len(body.product_name.strip()) < 3:
        raise HTTPException(400, "Nazwa produktu wymagana (min 3 znaki)")
    if not body.brand or len(body.brand.strip()) < 1:
        raise HTTPException(400, "Marka wymagana")

    gen = MediaGeneration(
        user_id=user_id,
        media_type=body.media_type,
        status=JobStatus.PENDING,
        input_params=body.model_dump(exclude_none=True),
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)

    logger.info("media_gen_queued", gen_id=gen.id, media_type=body.media_type, user=user_id)

    if body.media_type == "images":
        background_tasks.add_task(run_image_generation, gen.id)
    else:
        background_tasks.add_task(run_video_generation, gen.id)

    return {"id": gen.id, "status": "pending"}


@router.get("/status/{gen_id}")
async def get_status(
    gen_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Poll generation status. Lightweight — no result_data."""
    gen = db.query(MediaGeneration).filter(
        MediaGeneration.id == gen_id,
        MediaGeneration.user_id == user_id,
    ).first()
    if not gen:
        raise HTTPException(404, "Generacja nie znaleziona")

    return {
        "id": gen.id,
        "status": gen.status.value if gen.status else "pending",
        "media_type": gen.media_type,
        "created_at": gen.created_at.isoformat() if gen.created_at else None,
        "completed_at": gen.completed_at.isoformat() if gen.completed_at else None,
        "error_message": gen.error_message,
    }


@router.get("/result/{gen_id}")
async def get_result(
    gen_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get full result data (base64 images/video). Only when completed."""
    gen = db.query(MediaGeneration).filter(
        MediaGeneration.id == gen_id,
        MediaGeneration.user_id == user_id,
    ).first()
    if not gen:
        raise HTTPException(404, "Generacja nie znaleziona")
    if gen.status != JobStatus.COMPLETED:
        raise HTTPException(400, "Generacja jeszcze niezakonczona")

    return {"id": gen.id, "result_data": gen.result_data}


@router.get("/history")
async def get_history(
    page: int = Query(default=1, ge=1, le=1000),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Paginated history list. Summary only — no base64 data."""
    per_page = 20
    offset = (page - 1) * per_page

    total = db.query(MediaGeneration).filter(
        MediaGeneration.user_id == user_id,
    ).count()

    items = db.query(MediaGeneration).filter(
        MediaGeneration.user_id == user_id,
    ).order_by(MediaGeneration.created_at.desc()).offset(offset).limit(per_page).all()

    return {
        "items": [_to_summary(g) for g in items],
        "total": total,
        "page": page,
    }


@router.get("/active")
async def get_active_jobs(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get all pending/running jobs for notification badge."""
    jobs = db.query(MediaGeneration).filter(
        MediaGeneration.user_id == user_id,
        MediaGeneration.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
    ).all()

    return {"jobs": [{"id": j.id, "status": j.status.value, "media_type": j.media_type} for j in jobs]}


@router.get("/templates")
async def get_templates():
    """Return available video templates metadata."""
    from services.video_render import AVAILABLE_TEMPLATES
    return {"templates": AVAILABLE_TEMPLATES}


@router.patch("/{gen_id}/feedback")
async def save_feedback(
    gen_id: int,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Save user feedback on a generation for future learning."""
    gen = db.query(MediaGeneration).filter(
        MediaGeneration.id == gen_id,
        MediaGeneration.user_id == user_id,
    ).first()
    if not gen:
        raise HTTPException(404, "Generacja nie znaleziona")

    gen.feedback = body.feedback
    db.commit()

    logger.info("media_gen_feedback_saved", gen_id=gen_id, feedback_len=len(body.feedback))
    return {"status": "ok"}


@router.delete("/{gen_id}")
async def delete_generation(
    gen_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Delete a generation from history."""
    gen = db.query(MediaGeneration).filter(
        MediaGeneration.id == gen_id,
        MediaGeneration.user_id == user_id,
    ).first()
    if not gen:
        raise HTTPException(404, "Generacja nie znaleziona")

    db.delete(gen)
    db.commit()
    return {"status": "ok"}


def _to_summary(gen: MediaGeneration) -> dict:
    """Convert generation to summary dict (no base64 data)."""
    params = gen.input_params or {}
    return {
        "id": gen.id,
        "media_type": gen.media_type,
        "status": gen.status.value if gen.status else "pending",
        "product_name": params.get("product_name", ""),
        "brand": params.get("brand", ""),
        "theme": params.get("theme", ""),
        "template": params.get("template", ""),
        "created_at": gen.created_at.isoformat() if gen.created_at else None,
        "completed_at": gen.completed_at.isoformat() if gen.completed_at else None,
        "error_message": gen.error_message,
        "feedback": gen.feedback,
        "image_count": len((gen.result_data or {}).get("image_types", [])) if gen.media_type == "images" else None,
    }
