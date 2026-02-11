# backend/services/embedding_service.py
# Purpose: Generate embeddings via Cloudflare Workers AI (free, uses existing CF account)
# NOT for: Search logic (that's knowledge_service.py)

from __future__ import annotations

import time
import httpx
import structlog
from config import settings

logger = structlog.get_logger()

# WHY: bge-small-en-v1.5 on Cloudflare Workers AI — 384 dims, free tier, no extra signup
EMBEDDING_MODEL = "@cf/baai/bge-small-en-v1.5"
EMBEDDING_DIM = 384
CF_API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{settings.cf_account_id}/ai/run/{EMBEDDING_MODEL}"
)


def _cf_headers() -> dict[str, str]:
    """Build Cloudflare auth headers."""
    return {
        "X-Auth-Email": settings.cf_auth_email,
        "X-Auth-Key": settings.cf_api_key,
        "Content-Type": "application/json",
    }


async def get_embedding(text: str) -> list[float] | None:
    """Get embedding for a single text string. Returns None on failure.

    WHY: Retry once on 500 — CF Workers AI has occasional transient errors.
    """
    if not settings.cf_account_id:
        return None

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    CF_API_URL, headers=_cf_headers(), json={"text": [text]},
                )
                if resp.status_code == 500 and attempt == 0:
                    continue
                resp.raise_for_status()
                data = resp.json()
                if data.get("success"):
                    return data["result"]["data"][0]
                return None
        except Exception as e:
            if attempt == 0:
                continue
            logger.warning("embedding_error", error=str(e), text_preview=text[:60])
            return None


def get_embeddings_batch_sync(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of texts. Synchronous for ingestion scripts.

    WHY: Retry once on transient 500 errors from CF Workers AI.
    """
    for attempt in range(2):
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                CF_API_URL, headers=_cf_headers(), json={"text": texts},
            )
            if resp.status_code == 500 and attempt == 0:
                time.sleep(1)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise RuntimeError(f"CF AI error: {data.get('errors', [])}")
            return data["result"]["data"]
