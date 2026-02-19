# backend/services/optimizer_llm.py
# Purpose: Direct Groq LLM calls for listing optimization (title, bullets, desc, backend)
# NOT for: n8n orchestration, scoring, or post-processing

from __future__ import annotations

import asyncio
import re
from typing import List
from services.trace_service import span, record_llm_usage
from services.prompt_builders import (
    build_title_prompt, build_bullets_prompt,
    build_description_prompt, build_backend_prompt,
)
from services.groq_client import call_groq
from services.llm_providers import call_llm
import structlog

logger = structlog.get_logger()


async def run_direct_groq(
    trace: dict,
    product_title: str, brand: str, product_line: str,
    tier1_phrases: List[str], tier2_phrases: List[str], tier3_phrases: List[str],
    all_kw: List[dict],
    lang: str, limits: dict, bullet_count: int, bullet_char_limit: int,
    title_context: str, bullets_context: str, desc_context: str,
    marketplace: str,
    provider_config: dict | None = None,
) -> tuple:
    """Run 4 parallel LLM calls (title, bullets, description, backend suggestions).

    Returns (title_text, bullet_lines, desc_text, backend_suggestions).
    WHY: provider_config lets callers switch to Gemini/OpenAI while keeping Groq as default.
    """
    # WHY: Closure so we swap one call site instead of 4. Groq uses its own key rotation.
    if provider_config and provider_config.get("provider") != "groq":
        p = provider_config

        def call_fn(prompt, temp, max_tok):
            return call_llm(p["provider"], p["api_key"], p.get("model"), prompt, temp, max_tok)
    else:
        call_fn = call_groq

    title_prompt = build_title_prompt(
        product_title, brand, product_line, tier1_phrases, lang, limits["title"],
        expert_context=title_context,
    )

    with span(trace, "llm_title") as s:
        title_text, title_usage = await asyncio.to_thread(call_fn, title_prompt, 0.4, 250)
        if title_usage:
            record_llm_usage(s, title_usage)

    # WHY: bullets, description, and backend suggestions are independent — run all 3 in parallel
    bullets_prompt = build_bullets_prompt(
        product_title, brand, tier2_phrases, lang, bullet_char_limit,
        expert_context=bullets_context, bullet_count=bullet_count,
    )
    desc_prompt = build_description_prompt(
        product_title, brand, tier3_phrases + tier2_phrases[-5:], lang,
        expert_context=desc_context, marketplace=marketplace,
    )
    backend_prompt = build_backend_prompt(
        product_title, brand, title_text, all_kw, lang, limits["backend"],
    )

    # WHY: return_exceptions so optional backend call can fail without killing essential calls
    with span(trace, "llm_bullets_desc") as s:
        results = await asyncio.gather(
            asyncio.to_thread(call_fn, bullets_prompt, 0.5, 800),
            asyncio.to_thread(call_fn, desc_prompt, 0.5, 600),
            asyncio.to_thread(call_fn, backend_prompt, 0.3, 200),
            return_exceptions=True,
        )
        if isinstance(results[0], Exception):
            raise results[0]
        if isinstance(results[1], Exception):
            raise results[1]

        bullets_raw, b_usage = results[0]
        desc_text, d_usage = results[1]

        if isinstance(results[2], Exception):
            logger.warning("backend_llm_failed", error=str(results[2]))
            backend_suggestions = ""
        else:
            backend_suggestions, bk_usage = results[2]
            if bk_usage:
                record_llm_usage(s, bk_usage, accumulate=True)

        if b_usage:
            record_llm_usage(s, b_usage)
        if d_usage:
            record_llm_usage(s, d_usage, accumulate=True)

    # Parse bullets — one per line, strip numbering artifacts
    bullet_lines = [
        re.sub(r"^[\d\.\-\*\•]+\s*", "", line).strip()
        for line in bullets_raw.split("\n")
        if line.strip() and len(line.strip()) > 10
    ][:bullet_count]

    return title_text, bullet_lines, desc_text, backend_suggestions
