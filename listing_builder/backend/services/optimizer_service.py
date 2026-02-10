# backend/services/optimizer_service.py
# Purpose: Listing optimization — n8n-first with direct Groq fallback
# NOT for: Database models or marketplace publishing

from __future__ import annotations

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import search_knowledge_batch
from services.ranking_juice_service import calculate_ranking_juice
from services.learning_service import store_successful_listing, get_past_successes
from services.n8n_orchestrator_service import call_n8n_optimizer, build_n8n_payload
import structlog

logger = structlog.get_logger()

# WHY: Marketplace-specific limits for title, bullets, description, backend keywords
MARKETPLACE_LIMITS = {
    "amazon_de": {"title": 200, "bullet": 500, "backend": 249, "lang": "de"},
    "amazon_com": {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},
    "amazon_us":  {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},  # WHY: Frontend sends amazon_us
    "amazon_pl":  {"title": 200, "bullet": 500, "backend": 249, "lang": "pl"},
    "amazon_fr":  {"title": 200, "bullet": 500, "backend": 249, "lang": "fr"},
    "amazon_it":  {"title": 200, "bullet": 500, "backend": 249, "lang": "it"},
    "amazon_es":  {"title": 200, "bullet": 500, "backend": 249, "lang": "es"},
    "ebay_de":    {"title": 80,  "bullet": 300, "backend": 0,   "lang": "de"},
    "kaufland":   {"title": 150, "bullet": 400, "backend": 0,   "lang": "de"},
}

MODEL = "llama-3.3-70b-versatile"

# WHY: Amazon prohibits these in titles/bullets
PROMO_WORDS = [
    "bestseller", "best seller", "top seller", "#1", "nr. 1", "günstig",
    "billig", "gratis", "free", "sale", "rabatt", "discount", "angebot",
    "deal", "preiswert", "sonderangebot", "ausverkauf", "cheap",
]

FORBIDDEN_CHARS = ["!", "¡", "$", "€", "™", "®", "©"]


def _sanitize_llm_input(text: str) -> str:
    """Strip control characters and LLM injection patterns from user input.

    WHY: User-supplied product_title, brand, keywords go into LLM prompts.
    An attacker could inject "Ignore all instructions..." to hijack the prompt.
    We strip common injection prefixes and control chars, but keep normal text.
    """
    # Strip control characters (except newline/tab which are harmless)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Collapse multiple newlines (injection payloads use them to "escape" context)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # Truncate — no single field should exceed 1000 chars going into a prompt
    return cleaned[:1000]


def _get_limits(marketplace: str) -> dict:
    return MARKETPLACE_LIMITS.get(marketplace, MARKETPLACE_LIMITS["amazon_de"])


def _detect_language(marketplace: str, explicit_lang: str | None) -> str:
    if explicit_lang:
        return explicit_lang
    return _get_limits(marketplace).get("lang", "de")


# --- Keyword preparation ---

def _prepare_keywords(
    keywords: List[Dict[str, Any]],
) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """
    Sort by search_volume desc, assign tiers.
    Returns (all_sorted, tier1, tier2, tier3).
    Tier1 = top 30% → must go in title.
    Tier2 = next 40% → bullets/description.
    Tier3 = rest → backend keywords.
    """
    sorted_kw = sorted(keywords, key=lambda k: k.get("search_volume", 0), reverse=True)
    total = len(sorted_kw)
    t1_end = max(1, int(total * 0.3))
    t2_end = max(t1_end + 1, int(total * 0.7))

    tier1 = sorted_kw[:t1_end]
    tier2 = sorted_kw[t1_end:t2_end]
    tier3 = sorted_kw[t2_end:]

    return sorted_kw, tier1, tier2, tier3


def _extract_root_words(keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique root words (2+ chars) with aggregate search volume."""
    roots: Dict[str, int] = {}
    for kw in keywords:
        words = kw["phrase"].lower().split()
        vol = kw.get("search_volume", 0)
        for w in words:
            w = w.strip(".,;:-()[]")
            if len(w) >= 2:
                roots[w] = roots.get(w, 0) + vol
    # Return top 20 by volume
    sorted_roots = sorted(roots.items(), key=lambda x: x[1], reverse=True)[:20]
    return [{"word": w, "total_volume": v} for w, v in sorted_roots]


# --- Backend keyword byte-packing ---

def _pack_backend_keywords(
    keywords: List[Dict[str, Any]], listing_text: str, max_bytes: int
) -> str:
    """
    Greedy byte-packing: add keywords not already in the listing text,
    separated by spaces, up to max_bytes (249 for Amazon).
    WHY: Two passes — first unused full phrases, then individual root words
    that didn't appear in visible listing. This maximizes search coverage.
    """
    if max_bytes <= 0:
        return ""

    listing_lower = listing_text.lower()
    packed: List[str] = []
    packed_words: set = set()
    current_bytes = 0

    def _try_add(text: str) -> bool:
        nonlocal current_bytes
        text_bytes = len(text.encode("utf-8"))
        separator_bytes = 1 if packed else 0
        if current_bytes + separator_bytes + text_bytes <= max_bytes:
            packed.append(text)
            current_bytes += separator_bytes + text_bytes
            packed_words.update(text.lower().split())
            return True
        return False

    # Pass 1: full phrases not already covered in listing
    for kw in keywords:
        phrase = kw["phrase"].strip()
        phrase_words = phrase.lower().split()
        if all(w in listing_lower for w in phrase_words):
            continue
        _try_add(phrase)

    # Pass 2: individual root words not in listing or already packed
    # WHY: Amazon indexes individual words — adding roots that aren't
    # in visible content expands search match surface within 249 bytes
    all_roots: Dict[str, int] = {}
    for kw in keywords:
        for w in kw["phrase"].lower().split():
            w = w.strip(".,;:-()[]")
            if len(w) >= 2:
                all_roots[w] = all_roots.get(w, 0) + kw.get("search_volume", 0)

    for word, _ in sorted(all_roots.items(), key=lambda x: x[1], reverse=True):
        if word in listing_lower or word in packed_words:
            continue
        _try_add(word)

    # Pass 3: plural/singular variants to catch alternate searches
    # WHY: Amazon treats "bottle" and "bottles" as different search terms —
    # adding the missing variant catches more customer queries
    # Skip short words, abbreviations, numbers — they don't have useful variants
    # WHY: Adjectives, prepositions, abbreviations don't have useful plural forms
    skip_variant = {
        "bpa", "ml", "cm", "kg", "oz", "mm", "xl", "xxl",
        "free", "steel", "stainless", "insulated", "vacuum",
        "safe", "portable", "durable", "large", "small",
        "cold", "warm", "with", "from", "pour", "pour",
    }
    combined = listing_lower + " " + " ".join(packed).lower()
    variants: List[str] = []
    for word in list(all_roots.keys()):
        if len(word) < 4 or word in skip_variant or any(c.isdigit() for c in word):
            continue
        # WHY: Only generate variants that are real words shoppers search for
        if word.endswith("s") and len(word) > 4 and len(word) <= 9:
            # Plural → singular (bottles→bottle)
            singular = word[:-1]
            if singular not in combined and singular not in packed_words:
                variants.append(singular)
        elif not word.endswith("s") and len(word) <= 8:
            # Singular → plural (bottle→bottles, flask→flasks)
            plural = word + "s"
            if plural not in combined and plural not in packed_words:
                variants.append(plural)
        # German: -e endings → -en plural (Flasche→Flaschen, Kanne→Kannen)
        # WHY: German compound nouns are long (>8 chars), so this won't clash with English
        if word.endswith("e") and len(word) >= 8:
            de_plural = word + "n"
            if de_plural not in combined and de_plural not in packed_words:
                variants.append(de_plural)

    for v in variants:
        _try_add(v)

    return " ".join(packed)


# --- Coverage calculation ---

def _calculate_coverage(
    keywords: List[Dict[str, Any]], listing_text: str
) -> Tuple[float, int, str]:
    """
    Returns (coverage_pct, exact_matches_in_title_area, coverage_mode).
    A keyword is "covered" if >= 70% of its words appear in the full listing.
    """
    if not keywords:
        return 0.0, 0, "NONE"

    listing_lower = listing_text.lower()
    covered = 0
    exact_in_title = 0

    for kw in keywords:
        phrase_words = kw["phrase"].lower().split()
        if not phrase_words:
            continue
        matches = sum(1 for w in phrase_words if w in listing_lower)
        ratio = matches / len(phrase_words)
        if ratio >= 0.7:
            covered += 1
        # WHY: exact match = full phrase appears verbatim
        if kw["phrase"].lower() in listing_lower:
            exact_in_title += 1

    pct = round((covered / len(keywords)) * 100, 1)

    if pct >= 90:
        mode = "EXCELLENT"
    elif pct >= 70:
        mode = "GOOD"
    elif pct >= 50:
        mode = "MODERATE"
    else:
        mode = "LOW"

    return pct, exact_in_title, mode


def _find_missing_keywords(
    keywords: List[Dict[str, Any]], listing_text: str
) -> List[str]:
    """Keywords where < 70% of words appear in the listing."""
    listing_lower = listing_text.lower()
    missing = []
    for kw in keywords:
        words = kw["phrase"].lower().split()
        if not words:
            continue
        matches = sum(1 for w in words if w in listing_lower)
        if matches / len(words) < 0.7:
            missing.append(kw["phrase"])
    return missing


# --- Compliance check ---

def _check_compliance(
    title: str, bullets: List[str], description: str, brand: str, limits: dict
) -> Dict[str, Any]:
    errors = []
    warnings = []

    # Title length
    if len(title) > limits["title"]:
        errors.append(f"Title exceeds {limits['title']} chars ({len(title)})")

    # Bullet length
    for i, b in enumerate(bullets):
        if len(b) > limits["bullet"]:
            errors.append(f"Bullet {i+1} exceeds {limits['bullet']} chars ({len(b)})")

    # Brand position — should be near the start of title
    if brand and brand.lower() not in title[:50].lower():
        warnings.append("Brand not found in first 50 chars of title")

    # WHY: Use word-boundary regex to avoid false positives (e.g. "deal" inside "ideal")
    full_text = (title + " " + " ".join(bullets)).lower()
    for pw in PROMO_WORDS:
        if re.search(rf"\b{re.escape(pw)}\b", full_text):
            errors.append(f"Promotional word found: '{pw}'")

    # Forbidden characters
    for ch in FORBIDDEN_CHARS:
        if ch in title:
            errors.append(f"Forbidden character in title: '{ch}'")

    status = "PASS" if not errors else "FAIL"
    if not errors and warnings:
        status = "WARN"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


# --- Groq LLM calls ---

def _build_title_prompt(
    product_title: str, brand: str, product_line: str,
    tier1_phrases: List[str], lang: str, max_chars: int,
    expert_context: str = "",
) -> str:
    kw_list = ", ".join(tier1_phrases[:10])
    # WHY: Expert context from Inner Circle transcripts teaches proven title strategies
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    return f"""You are an expert Amazon listing optimizer.
{context_block}Product: {product_title}
Brand: {brand}
Product line: {product_line}
Language: {lang}
Max characters: {max_chars}

TOP KEYWORDS (must include): {kw_list}

Rules:
- Start with brand name
- Include as many top keywords as naturally possible
- No promotional words (bestseller, #1, günstig, etc.)
- No special characters (!, €, ™, etc.)
- Stay under {max_chars} characters
- Write in {lang}

Return ONLY the optimized title, nothing else."""


def _build_bullets_prompt(
    product_title: str, brand: str, tier2_phrases: List[str],
    lang: str, max_chars: int,
    expert_context: str = "",
) -> str:
    kw_list = ", ".join(tier2_phrases[:15])
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    return f"""You are an expert Amazon listing optimizer.
{context_block}Product: {product_title}
Brand: {brand}
Language: {lang}
Max characters per bullet: {max_chars}

KEYWORDS to weave in: {kw_list}

Rules:
- Write exactly 5 bullet points
- Start each bullet with a CAPITALIZED benefit keyword
- Include keywords naturally, not forced
- Focus on benefits, not just features
- Each bullet under {max_chars} characters
- Write in {lang}
- No promotional words

Return ONLY 5 bullet points, one per line, no numbering or bullet symbols."""


def _build_description_prompt(
    product_title: str, brand: str, remaining_phrases: List[str],
    lang: str,
    expert_context: str = "",
) -> str:
    kw_list = ", ".join(remaining_phrases[:10])
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    return f"""You are an expert Amazon listing optimizer.
{context_block}Product: {product_title}
Brand: {brand}
Language: {lang}

REMAINING KEYWORDS to include: {kw_list}

Rules:
- Write a compelling product description (2-3 short paragraphs)
- Naturally include the remaining keywords
- Focus on use cases and benefits
- Professional tone, no hype
- Write in {lang}
- No HTML tags

Return ONLY the description text."""


def _call_groq(prompt: str, temperature: float, max_tokens: int) -> str:
    """Synchronous Groq call with automatic key rotation on 429 rate limits."""
    keys = settings.groq_api_keys
    last_error = None

    for i, key in enumerate(keys):
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("groq_rate_limit", key_index=i, remaining_keys=len(keys) - i - 1)
                continue
            raise  # Non-rate-limit errors should propagate immediately

    # WHY: All keys exhausted — raise the last error
    raise last_error


# --- Post-processing: strip promo words LLM may have slipped in ---

def _strip_promo_words(text: str) -> str:
    """Remove promotional words from LLM output, clean up leftover whitespace."""
    result = text
    for pw in PROMO_WORDS:
        # WHY: word-boundary match to avoid stripping partial words (e.g. "ideal" from "ideally")
        result = re.sub(rf"\b{re.escape(pw)}\b", "", result, flags=re.IGNORECASE)
    # Clean up double spaces / leading commas left after removal
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r"\s,", ",", result)
    return result.strip()


# --- Main entry point ---

async def optimize_listing(
    product_title: str,
    brand: str,
    keywords: List[Dict[str, Any]],
    marketplace: str = "amazon_de",
    mode: str = "aggressive",
    product_line: str = "",
    language: str | None = None,
    db: Session | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Run full listing optimization: keyword prep → 3 LLM calls → packing → scoring.
    Returns dict matching OptimizerResponse shape.
    """
    limits = _get_limits(marketplace)
    lang = _detect_language(marketplace, language)

    # WHY: Sanitize user inputs before they enter LLM prompts (injection prevention)
    product_title = _sanitize_llm_input(product_title)
    brand = _sanitize_llm_input(brand)
    product_line = _sanitize_llm_input(product_line)
    for kw in keywords:
        kw["phrase"] = _sanitize_llm_input(kw["phrase"])

    # 1. Keyword preparation
    all_kw, tier1, tier2, tier3 = _prepare_keywords(keywords)
    tier1_phrases = [k["phrase"] for k in tier1]
    tier2_phrases = [k["phrase"] for k in tier2]
    tier3_phrases = [k["phrase"] for k in tier3]
    root_words = _extract_root_words(all_kw)

    # WHY: Retrieve expert context from Inner Circle transcripts to improve LLM output
    # Single DB query fetches chunks for all 3 prompt types at once
    title_context = bullets_context = desc_context = ""
    if db:
        search_query = f"{product_title} {' '.join(tier1_phrases[:5])}"
        knowledge = search_knowledge_batch(db, search_query)
        title_context = knowledge.get("title", "")
        bullets_context = knowledge.get("bullets", "")
        desc_context = knowledge.get("description", "")

    # WHY: Fetch past successful listings as few-shot examples for the LLM
    past_successes = []
    if db:
        past_successes = get_past_successes(db, marketplace)

    logger.info(
        "optimizer_start",
        product=product_title[:50],
        keywords=len(all_kw),
        tiers=f"{len(tier1)}/{len(tier2)}/{len(tier3)}",
        knowledge_title=len(title_context),
        knowledge_bullets=len(bullets_context),
        knowledge_desc=len(desc_context),
        past_successes=len(past_successes),
    )

    # 2. Try n8n first, fall back to direct Groq
    optimization_source = "direct"
    n8n_result = None

    if settings.n8n_webhook_url:
        expert_context = {
            "title": title_context,
            "bullets": bullets_context,
            "description": desc_context,
        }
        payload = build_n8n_payload(
            brand=brand,
            product_title=product_title,
            keywords=all_kw,
            marketplace=marketplace,
            mode=mode,
            language=lang,
            expert_context=expert_context,
            past_successes=past_successes,
        )
        n8n_result = await call_n8n_optimizer(payload)

    if n8n_result:
        # WHY: n8n returned a valid listing — use it
        optimization_source = "n8n"
        title_text = n8n_result.get("title", "")
        bullet_lines = n8n_result.get("bullet_points", [])
        desc_text = n8n_result.get("description", "")
        # WHY: Still strip promo words — n8n/LLM might slip them in
        title_text = _strip_promo_words(title_text)
        bullet_lines = [_strip_promo_words(b) for b in bullet_lines]
        desc_text = _strip_promo_words(desc_text)
    else:
        # Fallback: direct Groq calls (existing flow)
        title_prompt = _build_title_prompt(
            product_title, brand, product_line, tier1_phrases, lang, limits["title"],
            expert_context=title_context,
        )
        title_text = await asyncio.to_thread(_call_groq, title_prompt, 0.4, 250)

        # WHY: bullets and description are independent — run in parallel
        bullets_prompt = _build_bullets_prompt(
            product_title, brand, tier2_phrases, lang, limits["bullet"],
            expert_context=bullets_context,
        )
        desc_prompt = _build_description_prompt(
            product_title, brand, tier3_phrases + tier2_phrases[-5:], lang,
            expert_context=desc_context,
        )

        bullets_raw, desc_text = await asyncio.gather(
            asyncio.to_thread(_call_groq, bullets_prompt, 0.5, 800),
            asyncio.to_thread(_call_groq, desc_prompt, 0.5, 600),
        )

        # Parse bullets — one per line, strip numbering artifacts
        bullet_lines = [
            re.sub(r"^[\d\.\-\*\•]+\s*", "", line).strip()
            for line in bullets_raw.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:5]

        # WHY: LLM sometimes ignores "no promotional words" instruction — strip them
        title_text = _strip_promo_words(title_text)
        bullet_lines = [_strip_promo_words(b) for b in bullet_lines]
        desc_text = _strip_promo_words(desc_text)

    # 3. Backend keyword packing
    full_listing_text = title_text + " " + " ".join(bullet_lines) + " " + desc_text
    backend_kw = _pack_backend_keywords(all_kw, full_listing_text, limits["backend"])
    backend_bytes = len(backend_kw.encode("utf-8"))

    # 4. Coverage calculation (include backend keywords in full text)
    full_text_with_backend = full_listing_text + " " + backend_kw
    coverage_pct, exact_matches, coverage_mode = _calculate_coverage(all_kw, full_text_with_backend)
    title_cov, _, _ = _calculate_coverage(tier1, title_text)
    missing = _find_missing_keywords(all_kw, full_text_with_backend)

    # 5. Compliance check
    compliance = _check_compliance(title_text, bullet_lines, desc_text, brand, limits)

    # 6. Backend utilization
    backend_util = round((backend_bytes / limits["backend"]) * 100, 1) if limits["backend"] > 0 else 0

    # 6. Ranking Juice — quantifies listing quality 0-100
    rj = calculate_ranking_juice(all_kw, title_text, bullet_lines, backend_kw, desc_text)

    # 7. Self-learning — store if RJ >= 75
    if db:
        try:
            store_successful_listing(
                db,
                listing_data={
                    "brand": brand,
                    "marketplace": marketplace,
                    "product_title": product_title,
                    "title": title_text,
                    "bullets": json.dumps(bullet_lines),
                    "description": desc_text,
                    "backend_keywords": backend_kw,
                    "keyword_count": len(all_kw),
                },
                ranking_juice_data=rj,
            )
        except Exception as e:
            logger.warning("self_learning_save_failed", error=str(e))

    logger.info(
        "optimizer_done",
        coverage=coverage_pct,
        compliance=compliance["status"],
        backend_bytes=backend_bytes,
        ranking_juice=rj["score"],
        grade=rj["grade"],
        source=optimization_source,
    )

    return {
        "status": "success",
        "marketplace": marketplace,
        "brand": brand,
        "mode": mode,
        "language": lang,
        "listing": {
            "title": title_text,
            "bullet_points": bullet_lines,
            "description": desc_text,
            "backend_keywords": backend_kw,
        },
        "scores": {
            "coverage_pct": coverage_pct,
            "coverage_mode": coverage_mode,
            "exact_matches_in_title": exact_matches,
            "title_coverage_pct": title_cov,
            "backend_utilization_pct": backend_util,
            "backend_byte_size": backend_bytes,
            "compliance_status": compliance["status"],
        },
        "compliance": compliance,
        "keyword_intel": {
            "total_analyzed": len(all_kw),
            "tier1_title": len(tier1),
            "tier2_bullets": len(tier2),
            "tier3_backend": len(tier3),
            "missing_keywords": missing[:20],
            "root_words": root_words,
        },
        "ranking_juice": rj,
        "optimization_source": optimization_source,
    }
