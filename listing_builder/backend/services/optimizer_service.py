# backend/services/optimizer_service.py
# Purpose: Listing optimization orchestrator — n8n-first with direct Groq fallback
# NOT for: LLM calls (optimizer_llm.py), scoring (optimizer_scoring.py), config (marketplace_config.py)

from __future__ import annotations

import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from services.knowledge_service import search_knowledge_batch
from services.learning_service import store_successful_listing, get_past_successes
from services.n8n_orchestrator_service import call_n8n_optimizer, build_n8n_payload
from services.trace_service import new_trace, span, finalize_trace
from services.keyword_placement_service import (
    prepare_keywords_with_fallback, get_bullet_count, get_bullet_limit, extract_root_words,
)
from services.groq_client import sanitize_llm_input
from services.backend_packing_service import pack_backend_keywords
from services.marketplace_config import get_limits, detect_language
from services.listing_post_processing import strip_promo_words, bold_keywords_in_html, truncate_title
from services.optimizer_llm import run_direct_groq
from services.optimizer_scoring import score_listing
from config import settings
import structlog

logger = structlog.get_logger()


async def _fetch_knowledge(
    db: Session | None, product_title: str, tier1_phrases: List[str],
    marketplace: str, audience_context: str,
) -> tuple:
    """Fetch RAG context and past successes from DB."""
    title_ctx = bullets_ctx = desc_ctx = ""
    past_successes = []

    if db:
        search_query = f"{product_title} {' '.join(tier1_phrases[:5])}"
        knowledge = await search_knowledge_batch(db, search_query)
        title_ctx = knowledge.get("title", "")
        bullets_ctx = knowledge.get("bullets", "")
        desc_ctx = knowledge.get("description", "")
        past_successes = get_past_successes(db, marketplace)

    # WHY: Audience research gives buyer language — prepend so LLM uses real customer phrases
    if audience_context:
        block = f"AUDIENCE RESEARCH (use buyer language from this):\n{audience_context[:2000]}\n\n"
        title_ctx = block + title_ctx
        bullets_ctx = block + bullets_ctx
        desc_ctx = block + desc_ctx

    return title_ctx, bullets_ctx, desc_ctx, past_successes


def _post_process(
    title: str, bullets: List[str], desc: str,
    backend_suggestions: str, marketplace: str,
    tier1_phrases: List[str], tier2_phrases: List[str], limits: dict,
) -> tuple:
    """Strip promo words, bold Allegro keywords, truncate title."""
    title = strip_promo_words(title)
    bullets = [strip_promo_words(b) for b in bullets]
    desc = strip_promo_words(desc)
    backend_suggestions = strip_promo_words(backend_suggestions)

    if "allegro" in marketplace:
        desc = bold_keywords_in_html(desc, tier1_phrases + tier2_phrases[:10])

    title = truncate_title(title, limits["title"])
    return title, bullets, desc, backend_suggestions


async def optimize_listing(
    product_title: str,
    brand: str,
    keywords: List[Dict[str, Any]],
    marketplace: str = "amazon_de",
    mode: str = "aggressive",
    product_line: str = "",
    language: str | None = None,
    db: Session | None = None,
    audience_context: str = "",
    account_type: str = "seller",
    category: str = "",
    provider_config: dict | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run full listing optimization: keyword prep, LLM calls, packing, scoring."""
    trace = new_trace("optimize_listing")
    limits = get_limits(marketplace)
    lang = detect_language(marketplace, language)

    # WHY: Sanitize user inputs before they enter LLM prompts (injection prevention)
    product_title = sanitize_llm_input(product_title)
    brand = sanitize_llm_input(brand)
    product_line = sanitize_llm_input(product_line)
    for kw in keywords:
        kw["phrase"] = sanitize_llm_input(kw["phrase"])

    bullet_count = get_bullet_count(account_type)
    bullet_char_limit = get_bullet_limit(category) if category else limits["bullet"]

    # 1. Keyword preparation
    with span(trace, "keyword_prep"):
        all_kw, tier1, tier2, tier3 = prepare_keywords_with_fallback(keywords, account_type)
        tier1_phrases = [k["phrase"] for k in tier1]
        tier2_phrases = [k["phrase"] for k in tier2]
        tier3_phrases = [k["phrase"] for k in tier3]
        root_words = extract_root_words(all_kw)

    # 2. RAG knowledge
    with span(trace, "rag_search"):
        title_ctx, bullets_ctx, desc_ctx, past_successes = await _fetch_knowledge(
            db, product_title, tier1_phrases, marketplace, audience_context,
        )

    logger.info(
        "optimizer_start", product=product_title[:50],
        keywords=len(all_kw), tiers=f"{len(tier1)}/{len(tier2)}/{len(tier3)}",
    )

    # 3. n8n-first, fallback to direct LLM
    optimization_source = "direct"
    used_provider = (provider_config or {}).get("provider", "groq")
    # WHY: Track original provider when fallback happens — frontend shows warning to user
    fallback_from = None
    backend_suggestions = ""

    if settings.n8n_webhook_url:
        payload = build_n8n_payload(
            brand=brand, product_title=product_title, keywords=all_kw,
            marketplace=marketplace, mode=mode, language=lang,
            expert_context={"title": title_ctx, "bullets": bullets_ctx, "description": desc_ctx},
            past_successes=past_successes,
        )
        n8n_result = await call_n8n_optimizer(payload)
        if n8n_result:
            optimization_source = "n8n"
            title_text = n8n_result.get("title", "")
            bullet_lines = n8n_result.get("bullet_points", [])
            desc_text = n8n_result.get("description", "")

    if optimization_source == "direct":
        # WHY: If non-Groq provider fails (bad key, quota), fall back to Groq silently
        try:
            title_text, bullet_lines, desc_text, backend_suggestions = await run_direct_groq(
                trace, product_title, brand, product_line,
                tier1_phrases, tier2_phrases, tier3_phrases, all_kw,
                lang, limits, bullet_count, bullet_char_limit,
                title_ctx, bullets_ctx, desc_ctx, marketplace,
                provider_config=provider_config,
            )
        except Exception as provider_err:
            if used_provider != "groq":
                logger.warning("provider_fallback_to_groq", provider=used_provider, error=str(provider_err))
                fallback_from = used_provider
                title_text, bullet_lines, desc_text, backend_suggestions = await run_direct_groq(
                    trace, product_title, brand, product_line,
                    tier1_phrases, tier2_phrases, tier3_phrases, all_kw,
                    lang, limits, bullet_count, bullet_char_limit,
                    title_ctx, bullets_ctx, desc_ctx, marketplace,
                )
                used_provider = "groq"
            else:
                raise

    # 4. Post-process
    title_text, bullet_lines, desc_text, backend_suggestions = _post_process(
        title_text, bullet_lines, desc_text, backend_suggestions,
        marketplace, tier1_phrases, tier2_phrases, limits,
    )

    # 5. Backend packing + scoring
    with span(trace, "scoring"):
        full_listing = title_text + " " + " ".join(bullet_lines) + " " + desc_text
        backend_kw = pack_backend_keywords(all_kw, full_listing, limits["backend"], backend_suggestions)
        scores = score_listing(all_kw, tier1, title_text, bullet_lines, desc_text, backend_kw, brand, limits)

    # 6. Self-learning
    listing_history_id = None
    if db:
        try:
            listing_history_id = store_successful_listing(
                db,
                listing_data={
                    "brand": brand, "marketplace": marketplace, "product_title": product_title,
                    "title": title_text, "bullets": json.dumps(bullet_lines),
                    "description": desc_text, "backend_keywords": backend_kw,
                    "keyword_count": len(all_kw),
                },
                ranking_juice_data=scores["rj"],
            )
        except Exception as e:
            logger.warning("self_learning_save_failed", error=str(e))

    trace_data = finalize_trace(trace)
    logger.info(
        "optimizer_done", coverage=scores["coverage_pct"],
        compliance=scores["compliance"]["status"], rj=scores["rj"]["score"],
        source=optimization_source,
    )

    return {
        "status": "success",
        "marketplace": marketplace, "brand": brand, "mode": mode, "language": lang,
        "listing": {
            "title": title_text, "bullet_points": bullet_lines,
            "description": desc_text, "backend_keywords": backend_kw,
        },
        "scores": {
            "coverage_pct": scores["coverage_pct"], "coverage_mode": scores["coverage_mode"],
            "exact_matches_in_title": scores["exact_matches"], "title_coverage_pct": scores["title_cov"],
            "backend_utilization_pct": scores["backend_util"], "backend_byte_size": scores["backend_bytes"],
            "compliance_status": scores["compliance"]["status"],
        },
        "compliance": scores["compliance"],
        "keyword_intel": {
            "total_analyzed": len(all_kw), "tier1_title": len(tier1),
            "tier2_bullets": len(tier2), "tier3_backend": len(tier3),
            "missing_keywords": scores["missing"][:20], "root_words": root_words,
        },
        "ranking_juice": scores["rj"],
        "llm_provider": used_provider,
        "llm_fallback_from": fallback_from,
        "optimization_source": optimization_source,
        "listing_history_id": listing_history_id,
        "trace": trace_data,
        "coverage_breakdown": scores["coverage_breakdown"].get("breakdown", {}),
        "coverage_target": scores["coverage_breakdown"].get("target_pct", 95.0),
        "meets_coverage_target": scores["coverage_breakdown"].get("meets_target", False),
        "ppc_recommendations": scores["ppc"],
        "account_type": account_type,
    }
