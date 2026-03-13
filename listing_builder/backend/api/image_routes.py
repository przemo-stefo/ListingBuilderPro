# backend/api/image_routes.py
# Purpose: API endpoints for AI-generated product infographics (A+ Content)
# NOT for: Product photo management or file uploads

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
import json
import structlog

from database import SessionLocal
from services.image_core import VALID_THEMES
from services.image_service import build_image_content_prompt, render_all_images, IMAGE_TYPES
from services.llm_providers import PROVIDERS, call_llm
from services.groq_client import call_groq
from services.aplus_rag import fetch_examples, record_feedback, save_user_example
from utils.json_extract import extract_json as _extract_json
from api.dependencies import require_user_id

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageGenerateRequest(BaseModel):
    """Request payload for generating product infographics."""
    product_name: str = Field(..., min_length=3, max_length=500)
    brand: str = Field(..., min_length=1, max_length=200)
    bullet_points: List[str] = Field(default_factory=list, max_length=10)
    description: str = Field(default="", max_length=5000)
    category: str = Field(default="", max_length=200)
    language: str = Field(default="pl", max_length=10)
    theme: str = Field(default="dark_premium", max_length=30)
    # WHY: Same provider system as optimizer — Beast is free/unlimited, ideal for image gen
    llm_provider: Optional[str] = Field(default=None, max_length=20)
    llm_api_key: Optional[str] = Field(default=None, max_length=200)


class ImageGenerateResponse(BaseModel):
    """Response with base64-encoded PNG images."""
    status: str
    images: Dict[str, str]  # WHY: {image_type: base64_png} — frontend renders as <img src="data:image/png;base64,...">
    image_types: List[str]  # WHY: Ordered list for frontend display
    llm_provider: str
    example_ids: List[int] = Field(default_factory=list)  # WHY: RAG — frontend sends back with feedback
    content_data: Optional[Dict] = None  # WHY: Structural JSON for feedback loop — frontend sends back on accept


class ImageFeedbackRequest(BaseModel):
    """User feedback on generated A+ Content — feeds RAG quality scores."""
    # WHY: Cap at 10 IDs — prevents abuse with large IN queries
    example_ids: List[int] = Field(default_factory=list, max_length=10)
    accepted: bool
    gen_id: Optional[int] = None
    # WHY: If accepted, save the generated content as new training example
    product_name: Optional[str] = Field(default=None, max_length=500)
    brand: Optional[str] = Field(default=None, max_length=200)
    category: Optional[str] = Field(default=None, max_length=200)
    language: Optional[str] = Field(default=None, max_length=10)
    content_data: Optional[Dict] = None


@router.post("/generate", response_model=ImageGenerateResponse)
@limiter.limit("5/minute")
async def generate_images(
    request: Request,
    body: ImageGenerateRequest,
    user_id: str = Depends(require_user_id),
):
    """Generate Amazon A+ Content infographics for a product.

    WHY: 2-step process:
    1. LLM analyzes product data → generates structured content (features, comparisons, specs)
    2. Pillow renders content into professional PNG infographics

    Beast (qwen3:235b) is ideal here — no rate limits, high quality, zero cost.
    Falls back to Groq if Beast unavailable.
    """
    # WHY: Reject unknown themes early — prevents silent fallback to dark_premium
    if body.theme not in VALID_THEMES:
        raise HTTPException(status_code=400, detail=f"Nieznany motyw. Dozwolone: {', '.join(VALID_THEMES)}")

    logger.info("image_gen_start", product=body.product_name[:50], provider=body.llm_provider)

    # Step 0: RAG — fetch best training examples for few-shot injection
    db = SessionLocal()
    example_ids = []
    rag_examples = []
    try:
        raw_examples = fetch_examples(body.category, body.language, limit=3, db=db)
        example_ids = [e["id"] for e in raw_examples]
        rag_examples = [e["content_data"] for e in raw_examples]
        logger.info("image_gen_rag", count=len(rag_examples), ids=example_ids)
    except Exception as e:
        logger.warning("image_gen_rag_skip", error=str(e))
    finally:
        db.close()

    # Step 1: Build content prompt
    prompt = build_image_content_prompt(
        product_name=body.product_name,
        brand=body.brand,
        bullets=body.bullet_points,
        description=body.description,
        category=body.category,
        lang=body.language,
        examples=rag_examples,
    )

    # Step 2: Call LLM to generate structured content
    provider = body.llm_provider or "groq"
    try:
        if provider == "beast":
            from config import settings as app_settings
            if not app_settings.beast_ollama_url:
                raise ValueError("Beast nie skonfigurowany")
            text, _ = await asyncio.to_thread(
                call_llm, "beast", "ollama", None, prompt, 0.4, 4000,
            )
        elif provider == "groq":
            text, _ = await asyncio.to_thread(call_groq, prompt, 0.4, 4000)
        elif provider in PROVIDERS:
            if not body.llm_api_key:
                raise ValueError("Klucz API wymagany")
            text, _ = await asyncio.to_thread(
                call_llm, provider, body.llm_api_key, None, prompt, 0.4, 4000,
            )
        else:
            raise ValueError(f"Nieznany provider: {provider}")
    except Exception as e:
        # WHY: Fallback to Groq if Beast/other provider fails
        if provider != "groq":
            logger.warning("image_gen_provider_fallback", original=provider, error=str(e))
            try:
                text, _ = await asyncio.to_thread(call_groq, prompt, 0.4, 4000)
                provider = "groq"
            except Exception as fallback_err:
                raise HTTPException(status_code=503, detail="AI niedostepne. Sprobuj pozniej.")
        else:
            raise HTTPException(status_code=503, detail="AI niedostepne. Sprobuj pozniej.")

    # Step 3: Parse LLM response as JSON
    try:
        # WHY: Reuse robust parser from media_gen_worker — handles fences, truncation
        content_data = _extract_json(text)
    except json.JSONDecodeError as e:
        logger.error("image_gen_json_parse_failed", error=str(e), text_preview=text[:200])
        raise HTTPException(
            status_code=500,
            detail="AI wygenerowalo nieprawidlowe dane. Sprobuj ponownie.",
        )

    # Step 4: Render images — Gemini (premium) → Pillow (fallback)
    from config import settings as app_settings
    gemini_key = app_settings.gemini_image_api_key
    try:
        images = await asyncio.to_thread(
            render_all_images,
            body.product_name,
            body.brand,
            content_data,
            body.theme,
            gemini_key,
        )
    except Exception as e:
        logger.error("image_gen_render_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Renderowanie grafik nie powiodlo sie.")

    if not images:
        raise HTTPException(status_code=500, detail="Nie udalo sie wygenerowac zadnych grafik.")

    # WHY: Ordered list so frontend shows images in logical order
    ordered_types = [t for t in IMAGE_TYPES if t in images]

    logger.info("image_gen_success", count=len(images), types=ordered_types, provider=provider)

    return ImageGenerateResponse(
        status="ok",
        images=images,
        image_types=ordered_types,
        llm_provider=provider,
        example_ids=example_ids,
        content_data=content_data,
    )


@router.post("/feedback")
async def image_feedback(
    body: ImageFeedbackRequest,
    user_id: str = Depends(require_user_id),
):
    """Record user feedback on A+ Content — updates RAG quality scores.

    WHY: Self-improving loop — accepted content boosts example scores,
    rejected content lowers them. Accepted content becomes new training example.
    """
    db = SessionLocal()
    try:
        if body.example_ids:
            record_feedback(body.example_ids, body.accepted, db)
        # WHY: Save accepted generation as new training example for future RAG
        if body.accepted and body.content_data and body.product_name:
            save_user_example(
                body.product_name, body.brand or "", body.category or "",
                body.language or "pl", body.content_data, db,
            )
        return {"status": "ok"}
    finally:
        db.close()
