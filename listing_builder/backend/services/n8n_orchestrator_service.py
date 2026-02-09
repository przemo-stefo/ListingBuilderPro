# backend/services/n8n_orchestrator_service.py
# Purpose: Call n8n webhook for LLM orchestration, parse response
# NOT for: Ranking Juice, self-learning, or direct Groq calls

import httpx
import json
from typing import Dict, Optional, List
from config import settings
import structlog

logger = structlog.get_logger()


async def call_n8n_optimizer(payload: Dict, timeout: float = 30.0) -> Optional[Dict]:
    """
    POST to n8n webhook. Returns parsed listing response or None on failure.

    WHY: n8n handles prompt building + Groq call. FastAPI handles everything else
    (RAG, Ranking Juice, quality gating, storage). This keeps n8n stateless.
    """
    webhook_url = settings.n8n_webhook_url
    if not webhook_url:
        logger.debug("n8n_skipped", reason="no webhook URL configured")
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Secret": settings.n8n_webhook_secret,
                },
            )

        if response.status_code != 200:
            logger.warning(
                "n8n_error",
                status=response.status_code,
                body=response.text[:200],
            )
            return None

        data = response.json()

        # WHY: Validate that n8n returned the expected listing structure
        if not _validate_n8n_response(data):
            logger.warning("n8n_invalid_response", keys=list(data.keys()))
            return None

        logger.info("n8n_success")
        return data

    except httpx.TimeoutException:
        logger.warning("n8n_timeout", timeout=timeout)
        return None
    except Exception as e:
        logger.warning("n8n_exception", error=str(e))
        return None


def _validate_n8n_response(data: Dict) -> bool:
    """Check n8n returned a valid listing with title + bullets + description."""
    if not isinstance(data, dict):
        return False
    # WHY: n8n must return at least these fields for a valid listing
    required = ["title", "bullet_points", "description"]
    return all(key in data for key in required)


def build_n8n_payload(
    brand: str,
    product_title: str,
    keywords: List[Dict],
    marketplace: str,
    mode: str,
    language: str,
    expert_context: Dict[str, str],
    past_successes: List[Dict],
) -> Dict:
    """
    Build the payload sent to n8n webhook.

    WHY: Centralizes payload construction so optimizer_service stays clean.
    """
    return {
        "brand": brand,
        "product_title": product_title,
        "keywords": [
            {"phrase": kw["phrase"], "search_volume": kw.get("search_volume", 0)}
            for kw in keywords[:100]  # WHY: Cap at 100 to keep payload reasonable
        ],
        "marketplace": marketplace,
        "mode": mode,
        "language": language,
        "expert_context": expert_context,
        "past_successes": [
            {
                "title": s.get("title", ""),
                "bullets": s.get("bullets", []),
                "ranking_juice": s.get("ranking_juice", 0),
            }
            for s in past_successes[:3]
        ],
    }
