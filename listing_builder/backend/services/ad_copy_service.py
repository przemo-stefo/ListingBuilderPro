# backend/services/ad_copy_service.py
# Purpose: Generate Facebook/Meta ad copy variations using RAG knowledge from ad creative courses
# NOT for: Listing optimization (that's optimizer_service.py) or general Q&A (qa_service.py)

from __future__ import annotations

import asyncio
import json
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import _get_search_rows, _expand_query, _get_embedding_if_needed, _format_chunks_with_sources
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"

# WHY: These categories match Barry Hott, Ecom Talent, Fraser Cottrell, and copywriting courses
AD_CATEGORIES = ["ad_creative", "creative_strategy", "copywriting", "marketing_psychology"]


def _build_ad_prompt(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    context: str,
    platform: str,
) -> str:
    """Build system prompt with RAG knowledge and ad generation instructions."""
    features_block = "\n".join(f"- {f}" for f in product_features)

    audience_block = ""
    if target_audience:
        audience_block = f"\nTARGET AUDIENCE: {target_audience}\n"

    # WHY: Detect language from product info — if Polish input, answer in Polish
    lang_rule = (
        "Answer in the SAME LANGUAGE as the product title and features above. "
        "If they are in Polish, write ads in Polish. If in English, write in English."
    )

    return f"""You are an expert {platform} ad copywriter trained on courses from Barry Hott, Ecom Talent, and Fraser Cottrell. Generate ad copy using the expert knowledge below.

EXPERT KNOWLEDGE (from ad creative courses):
{context}

PRODUCT: {product_title}
FEATURES:
{features_block}
{audience_block}
PLATFORM: {platform}

Generate exactly 3 ad variations in JSON format. Each variation has a different approach:
1. "hook" — Pattern interrupt / curiosity hook (Barry Hott style)
2. "story" — Story-based / founder narrative (Fraser Cottrell style)
3. "benefit" — Direct benefit / social proof (Ecom Talent style)

Each variation MUST contain:
- "type": one of "hook", "story", "benefit"
- "headline": max 40 characters
- "primary_text": max 125 characters
- "description": max 30 characters

{lang_rule}

Return ONLY valid JSON array, no markdown, no explanation:
[{{"type":"hook","headline":"...","primary_text":"...","description":"..."}}, ...]"""


async def _search_ad_knowledge(
    db: Session, query: str
) -> tuple[str, list[str]]:
    """Search knowledge base with ad-specific categories.

    WHY: We target ad_creative/creative_strategy/copywriting/marketing_psychology
    specifically — these contain Barry Hott, Ecom Talent, and Cottrell courses.
    Falls back to all categories if no results found.
    """
    search_query = await _expand_query(query)
    query_embedding = await _get_embedding_if_needed(search_query)

    rows = await _get_search_rows(db, search_query, AD_CATEGORIES, 8, query_embedding)

    # WHY: Fallback to broader search if ad-specific categories return nothing
    if not rows:
        rows = await _get_search_rows(db, search_query, None, 8, query_embedding)

    if not rows:
        return "", []

    return _format_chunks_with_sources(rows)


async def generate_ad_copy(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    db: Session,
    platform: str = "facebook",
) -> Dict:
    """Generate 3 ad copy variations using Groq LLM with RAG context from ad courses."""
    search_query = f"{product_title} {' '.join(product_features[:3])}"
    context, source_names = await _search_ad_knowledge(db, search_query)

    logger.info(
        "ad_copy_generate",
        product=product_title[:60],
        platform=platform,
        context_len=len(context),
        sources=len(source_names),
    )

    prompt = _build_ad_prompt(product_title, product_features, target_audience, context, platform)

    # WHY: Low temperature (0.7) for creative but coherent ad copy
    def _call_with_rotation():
        keys = settings.groq_api_keys
        last_error = None
        for i, key in enumerate(keys):
            try:
                client = Groq(api_key=key)
                return client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800,
                )
            except Exception as e:
                last_error = e
                if "429" in str(e) or "rate_limit" in str(e):
                    logger.warning("ad_copy_groq_rate_limit", key_index=i)
                    continue
                raise
        raise last_error

    response = await asyncio.to_thread(_call_with_rotation)
    raw_answer = response.choices[0].message.content.strip()

    # WHY: Parse JSON from LLM response — strip markdown fences if present
    clean = raw_answer.strip("`").removeprefix("json").strip()
    try:
        variations = json.loads(clean)
    except json.JSONDecodeError:
        logger.error("ad_copy_json_parse_failed", raw=raw_answer[:200])
        variations = [{"type": "error", "headline": "Generation failed", "primary_text": raw_answer[:125], "description": "Retry"}]

    return {
        "variations": variations,
        "sources_used": len(source_names),
        "sources": source_names[:10],
        "platform": platform,
    }
