# backend/api/video_routes.py
# Purpose: API endpoints for AI product video generation via ComfyUI
# NOT for: ComfyUI pipeline logic (services/comfyui_service.py) or image fetching (services/product_image_fetcher.py)

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
import structlog

from api.dependencies import require_user_id
from services.comfyui_service import run_comfyui_pipeline, check_comfyui_status, VideoStatusResponse
from services.product_image_fetcher import fetch_product_image
from utils.url_validator import validate_marketplace_url

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/generate")
@limiter.limit("3/minute")
async def generate_video(
    request: Request,
    image: UploadFile = File(...),
    prompt: str = Form(default="product showcase, rotating, studio lighting, white background"),
    user_id: str = Depends(require_user_id),
):
    """Generate AI product video from uploaded image."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Plik musi byc obrazem (PNG/JPG)")

    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Obraz zbyt duzy (max 10MB)")

    logger.info("video_gen_start", user=user_id, size_kb=len(content) // 1024)

    try:
        result = await asyncio.to_thread(
            run_comfyui_pipeline, content, image.filename or "input.png", prompt
        )
    except Exception as e:
        logger.error("video_gen_failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Generowanie wideo nie powiodlo sie: {str(e)}")

    return result


class VideoFromUrlRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)
    prompt: str = Field(default="product showcase, smooth rotation, studio lighting, white background")


@router.post("/generate-from-url")
@limiter.limit("3/minute")
async def generate_video_from_url(
    request: Request,
    body: VideoFromUrlRequest,
    user_id: str = Depends(require_user_id),
):
    """Generate video from a marketplace product URL.

    WHY: Scrapes the main product image (og:image) from the URL,
    then runs the same ComfyUI pipeline as file upload.
    """
    try:
        validated_url = validate_marketplace_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("video_gen_from_url_start", user=user_id, url=validated_url[:100])

    try:
        image_bytes, filename = await asyncio.to_thread(fetch_product_image, validated_url)
    except Exception as e:
        logger.error("video_gen_image_fetch_failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Nie udalo sie pobrac zdjecia produktu: {str(e)}")

    try:
        result = await asyncio.to_thread(run_comfyui_pipeline, image_bytes, filename, body.prompt)
    except Exception as e:
        logger.error("video_gen_failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Generowanie wideo nie powiodlo sie: {str(e)}")

    return result


@router.get("/status/{prompt_id}")
async def video_status(
    prompt_id: str,
    user_id: str = Depends(require_user_id),
):
    """Poll for video generation progress."""
    try:
        status = await asyncio.to_thread(check_comfyui_status, prompt_id)
        return status
    except Exception as e:
        return VideoStatusResponse(status="error", error=str(e))
