# backend/services/media_gen_worker.py
# Purpose: Background worker for media generation (video + images)
# NOT for: API routes or DB model definitions

import json
from datetime import datetime, timezone
from typing import Optional
import structlog

from database import SessionLocal
from models.jobs import JobStatus
from models.media_generation import MediaGeneration
from utils.json_extract import extract_json as _extract_json

logger = structlog.get_logger()


def run_image_generation(gen_id: int):
    """Background task: generate A+ Content images via LLM + Pillow/Gemini.

    WHY: Extracted from image_routes.py synchronous flow into background worker.
    Reuses existing services — no logic duplication.
    """
    db = SessionLocal()
    try:
        gen = db.query(MediaGeneration).filter(MediaGeneration.id == gen_id).first()
        if not gen:
            logger.error("media_gen_not_found", gen_id=gen_id)
            return

        gen.status = JobStatus.RUNNING
        db.commit()

        params = gen.input_params
        logger.info("media_gen_worker_start", gen_id=gen_id, product=params.get("product_name", "")[:50])

        # Step 0: RAG — fetch best training examples for few-shot injection
        from services.aplus_rag import fetch_examples
        rag_examples = []
        try:
            raw = fetch_examples(params.get("category", ""), params.get("language", "pl"), limit=3, db=db)
            rag_examples = [e["content_data"] for e in raw]
            example_ids = [e["id"] for e in raw]
        except Exception as e:
            logger.warning("media_gen_rag_skip", gen_id=gen_id, error=str(e))
            example_ids = []

        # Step 1: Build content prompt
        from services.image_service import build_image_content_prompt, render_all_images, IMAGE_TYPES

        prompt = build_image_content_prompt(
            product_name=params["product_name"],
            brand=params["brand"],
            bullets=params.get("bullet_points", []),
            description=params.get("description", ""),
            category=params.get("category", ""),
            lang=params.get("language", "pl"),
            examples=rag_examples,
        )

        # Step 2: Call LLM + parse JSON (retry once on parse error)
        provider = params.get("llm_provider") or "groq"
        content_data = None
        for attempt in range(2):
            used_provider = provider if attempt == 0 else "groq"
            text = _call_llm_sync(used_provider, prompt, params.get("llm_api_key"))
            logger.info("media_gen_llm_response", gen_id=gen_id, attempt=attempt, provider=used_provider, response_len=len(text), first_100=text[:100])
            try:
                content_data = _extract_json(text)
                break
            except json.JSONDecodeError as je:
                logger.warning("media_gen_json_retry", gen_id=gen_id, attempt=attempt, error=str(je)[:200])
                if attempt == 1:
                    raise
        assert content_data is not None

        # Step 4: Render images
        from config import settings as app_settings
        images = render_all_images(
            params["product_name"],
            params["brand"],
            content_data,
            params.get("theme", "dark_premium"),
            app_settings.gemini_image_api_key,
        )

        if not images:
            raise RuntimeError("Nie udalo sie wygenerowac zadnych grafik.")

        ordered_types = [t for t in IMAGE_TYPES if t in images]

        gen.result_data = {
            "images": images,
            "image_types": ordered_types,
            "llm_provider": provider,
            "example_ids": example_ids,
        }
        gen.status = JobStatus.COMPLETED
        gen.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("media_gen_worker_done", gen_id=gen_id, count=len(images))

    except Exception as e:
        logger.error("media_gen_worker_failed", gen_id=gen_id, error=str(e))
        try:
            db.rollback()
            gen = db.query(MediaGeneration).filter(MediaGeneration.id == gen_id).first()
            if gen:
                gen.status = JobStatus.FAILED
                gen.error_message = str(e)[:500]
                gen.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as inner:
            logger.error("media_gen_worker_status_update_failed", gen_id=gen_id, error=str(inner))
    finally:
        db.close()


def run_video_generation(gen_id: int):
    """Background task: generate TikTok 9:16 video via MoviePy templates."""
    db = SessionLocal()
    try:
        gen = db.query(MediaGeneration).filter(MediaGeneration.id == gen_id).first()
        if not gen:
            return

        gen.status = JobStatus.RUNNING
        db.commit()

        params = gen.input_params
        logger.info("media_gen_video_start", gen_id=gen_id, template=params.get("template"))

        from services.video_render import render_video

        result = render_video(
            template=params.get("template", "product_highlight"),
            product_name=params.get("product_name", "Produkt"),
            brand=params.get("brand", "Marka"),
            features=params.get("features", params.get("bullet_points", [])),
            theme=params.get("theme", "dark_premium"),
            image_url=params.get("image_url"),
            original_price=params.get("original_price"),
            sale_price=params.get("sale_price"),
        )

        gen.result_data = result
        gen.status = JobStatus.COMPLETED
        gen.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("media_gen_video_done", gen_id=gen_id)

    except Exception as e:
        logger.error("media_gen_video_failed", gen_id=gen_id, error=str(e))
        try:
            db.rollback()
            gen = db.query(MediaGeneration).filter(MediaGeneration.id == gen_id).first()
            if gen:
                gen.status = JobStatus.FAILED
                gen.error_message = str(e)[:500]
                gen.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as inner:
            logger.error("media_gen_video_status_update_failed", gen_id=gen_id, error=str(inner))
    finally:
        db.close()


def _call_llm_sync(provider: str, prompt: str, api_key: Optional[str] = None) -> str:
    """Call LLM synchronously with fallback to Groq."""
    from services.llm_providers import PROVIDERS, call_llm
    from services.groq_client import call_groq

    try:
        if provider == "beast":
            from config import settings as app_settings
            if not app_settings.beast_ollama_url:
                raise ValueError("Beast nie skonfigurowany")
            text, _ = call_llm("beast", "ollama", None, prompt, 0.4, 4000)
        elif provider == "groq":
            text, _ = call_groq(prompt, 0.4, 4000)
        elif provider in PROVIDERS:
            if not api_key:
                raise ValueError("Klucz API wymagany")
            text, _ = call_llm(provider, api_key, None, prompt, 0.4, 4000)
        else:
            raise ValueError(f"Nieznany provider: {provider}")
    except Exception as e:
        if provider != "groq":
            logger.warning("media_gen_llm_fallback", original=provider, error=str(e))
            text, _ = call_groq(prompt, 0.4, 4000)
        else:
            raise
    return text
