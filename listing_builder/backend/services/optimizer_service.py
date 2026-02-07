# backend/services/optimizer_service.py
# Purpose: Direct Groq-powered listing optimization (replaces n8n proxy)
# NOT for: Database operations or marketplace publishing

from __future__ import annotations

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from groq import Groq
from config import settings
import structlog

logger = structlog.get_logger()

# WHY: Marketplace-specific limits for title, bullets, description, backend keywords
MARKETPLACE_LIMITS = {
    "amazon_de": {"title": 200, "bullet": 500, "backend": 249, "lang": "de"},
    "amazon_com": {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},
    "amazon_fr": {"title": 200, "bullet": 500, "backend": 249, "lang": "fr"},
    "amazon_it": {"title": 200, "bullet": 500, "backend": 249, "lang": "it"},
    "amazon_es": {"title": 200, "bullet": 500, "backend": 249, "lang": "es"},
    "ebay_de":   {"title": 80,  "bullet": 300, "backend": 0,   "lang": "de"},
    "kaufland":  {"title": 150, "bullet": 400, "backend": 0,   "lang": "de"},
}

MODEL = "llama-3.3-70b-versatile"

# WHY: Amazon prohibits these in titles/bullets
PROMO_WORDS = [
    "bestseller", "best seller", "top seller", "#1", "nr. 1", "günstig",
    "billig", "gratis", "free", "sale", "rabatt", "discount", "angebot",
    "deal", "preiswert", "sonderangebot", "ausverkauf", "cheap",
]

FORBIDDEN_CHARS = ["!", "¡", "$", "€", "™", "®", "©"]


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
    """
    if max_bytes <= 0:
        return ""

    listing_lower = listing_text.lower()
    packed: List[str] = []
    current_bytes = 0

    for kw in keywords:
        phrase = kw["phrase"].strip()
        # WHY: Skip if every word already appears in title/bullets/description
        phrase_words = phrase.lower().split()
        if all(w in listing_lower for w in phrase_words):
            continue

        phrase_bytes = len(phrase.encode("utf-8"))
        separator_bytes = 1 if packed else 0
        if current_bytes + separator_bytes + phrase_bytes <= max_bytes:
            packed.append(phrase)
            current_bytes += separator_bytes + phrase_bytes

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

    # Promo words
    full_text = (title + " " + " ".join(bullets)).lower()
    for pw in PROMO_WORDS:
        if pw in full_text:
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
    tier1_phrases: List[str], lang: str, max_chars: int
) -> str:
    kw_list = ", ".join(tier1_phrases[:10])
    return f"""You are an expert Amazon listing optimizer.

Product: {product_title}
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
    lang: str, max_chars: int
) -> str:
    kw_list = ", ".join(tier2_phrases[:15])
    return f"""You are an expert Amazon listing optimizer.

Product: {product_title}
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
    lang: str
) -> str:
    kw_list = ", ".join(remaining_phrases[:10])
    return f"""You are an expert Amazon listing optimizer.

Product: {product_title}
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
    """Synchronous Groq call — will be wrapped in asyncio.to_thread()."""
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# --- Main entry point ---

async def optimize_listing(
    product_title: str,
    brand: str,
    keywords: List[Dict[str, Any]],
    marketplace: str = "amazon_de",
    mode: str = "aggressive",
    product_line: str = "",
    language: str | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Run full listing optimization: keyword prep → 3 LLM calls → packing → scoring.
    Returns dict matching OptimizerResponse shape.
    """
    limits = _get_limits(marketplace)
    lang = _detect_language(marketplace, language)

    # 1. Keyword preparation
    all_kw, tier1, tier2, tier3 = _prepare_keywords(keywords)
    tier1_phrases = [k["phrase"] for k in tier1]
    tier2_phrases = [k["phrase"] for k in tier2]
    tier3_phrases = [k["phrase"] for k in tier3]
    root_words = _extract_root_words(all_kw)

    logger.info(
        "optimizer_start",
        product=product_title[:50],
        keywords=len(all_kw),
        tiers=f"{len(tier1)}/{len(tier2)}/{len(tier3)}",
    )

    # 2. Three Groq LLM calls (title first, then bullets + description in parallel)
    title_prompt = _build_title_prompt(
        product_title, brand, product_line, tier1_phrases, lang, limits["title"]
    )
    title_text = await asyncio.to_thread(_call_groq, title_prompt, 0.4, 250)

    # WHY: bullets and description are independent — run in parallel
    bullets_prompt = _build_bullets_prompt(
        product_title, brand, tier2_phrases, lang, limits["bullet"]
    )
    desc_prompt = _build_description_prompt(
        product_title, brand, tier3_phrases + tier2_phrases[-5:], lang
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

    logger.info(
        "optimizer_done",
        coverage=coverage_pct,
        compliance=compliance["status"],
        backend_bytes=backend_bytes,
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
    }
