# backend/services/video_creatify.py
# Purpose: Creatify API client for professional AI video generation
# NOT for: Template-based MoviePy videos (that's video_render.py)

import asyncio
from typing import Optional
import httpx
import structlog

logger = structlog.get_logger()
CREATIFY_BASE = "https://api.creatify.ai/api"


async def generate_url_to_video(
    api_id: str, api_key: str, product_url: str,
    visual_style: str = "modern", script: Optional[str] = None,
) -> dict:
    """Generate video from product URL — Creatify scrapes the page."""
    headers = {"X-API-ID": api_id, "X-API-KEY": api_key, "Content-Type": "application/json"}
    payload: dict = {"url": product_url, "visual_style": visual_style}
    if script:
        payload["script"] = script

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{CREATIFY_BASE}/url_to_videos/", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            raise ValueError(f"Creatify nie zwrocil job ID: {data}")

    result = await _poll_until_done(api_id, api_key, job_id, "url_to_videos")
    return _extract_result(result)


async def generate_product_to_video(
    api_id: str, api_key: str, product_name: str, brand: str,
    description: str = "", image_url: Optional[str] = None,
    visual_style: str = "modern", script: Optional[str] = None,
) -> dict:
    """Generate video from product data — provide image + description."""
    headers = {"X-API-ID": api_id, "X-API-KEY": api_key, "Content-Type": "application/json"}
    payload: dict = {"product_name": product_name, "brand": brand, "visual_style": visual_style}
    if description:
        payload["description"] = description
    if image_url:
        payload["media_url"] = image_url
    if script:
        payload["script"] = script

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{CREATIFY_BASE}/lipsyncs/", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            raise ValueError(f"Creatify nie zwrocil job ID: {data}")

    result = await _poll_until_done(api_id, api_key, job_id, "lipsyncs")
    return _extract_result(result)


async def _poll_until_done(api_id: str, api_key: str, job_id: str, endpoint: str) -> dict:
    """Poll Creatify job every 5s, max 120 attempts (10 min)."""
    headers = {"X-API-ID": api_id, "X-API-KEY": api_key}
    url = f"{CREATIFY_BASE}/{endpoint}/{job_id}/"

    for attempt in range(120):
        await asyncio.sleep(5)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        status = data.get("status", "")
        logger.debug("creatify_poll", job_id=job_id, attempt=attempt, status=status)

        if status == "done":
            return data
        if status in ("failed", "error"):
            raise RuntimeError(f"Creatify job failed: {data.get('error', 'unknown')}")

    raise TimeoutError(f"Creatify job {job_id} timeout po 10 min")


def _extract_result(data: dict) -> dict:
    return {
        "video_url": data.get("output", data.get("video_url", "")),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "duration": data.get("duration"),
        "creatify_job_id": data.get("id", ""),
    }
