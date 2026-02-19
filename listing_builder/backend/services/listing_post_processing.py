# backend/services/listing_post_processing.py
# Purpose: Post-processing of LLM output — promo word stripping, compliance, Allegro bolding
# NOT for: LLM calls, keyword placement, or coverage calculation

from __future__ import annotations

import re
from typing import List, Dict, Any

# WHY: Amazon prohibits these in titles/bullets — LLM sometimes ignores the instruction
PROMO_WORDS = [
    "bestseller", "best seller", "top seller", "#1", "nr. 1", "günstig",
    "billig", "gratis", "free", "sale", "rabatt", "discount", "angebot",
    "deal", "preiswert", "sonderangebot", "ausverkauf", "cheap",
]

FORBIDDEN_CHARS = ["!", "¡", "$", "€", "™", "®", "©"]


def strip_promo_words(text: str) -> str:
    """Remove promotional words from LLM output, clean up leftover whitespace."""
    result = text
    for pw in PROMO_WORDS:
        # WHY: word-boundary match to avoid stripping partial words (e.g. "deal" from "ideal")
        result = re.sub(rf"\b{re.escape(pw)}\b", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r"\s,", ",", result)
    return result.strip()


def bold_keywords_in_html(html: str, keywords: List[str]) -> str:
    """Wrap first occurrence of each keyword in <b> tags if not already bolded.

    WHY: Allegro buyers scan descriptions — bolded keywords let them spot
    key product features at a glance (Bartek's "game changer" insight).
    """
    result = html
    for phrase in keywords[:15]:
        if not phrase or len(phrase) < 2:
            continue
        # WHY: Skip if this phrase is already inside a <b> tag
        if re.search(rf"<b>[^<]*{re.escape(phrase)}[^<]*</b>", result, re.IGNORECASE):
            continue
        # WHY: Match phrase only in text content (not inside HTML tags)
        pattern = rf"(?<![<\w/])({re.escape(phrase)})(?![^<]*>)"
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            original = match.group(0)
            result = result[:match.start()] + f"<b>{original}</b>" + result[match.end():]
    return result


def check_compliance(
    title: str, bullets: List[str], description: str, brand: str, limits: dict,
) -> Dict[str, Any]:
    """Validate listing against marketplace rules — returns status, errors, warnings."""
    errors = []
    warnings = []

    if len(title) > limits["title"]:
        errors.append(f"Title exceeds {limits['title']} chars ({len(title)})")

    for i, b in enumerate(bullets):
        if len(b) > limits["bullet"]:
            errors.append(f"Bullet {i+1} exceeds {limits['bullet']} chars ({len(b)})")

    # WHY: Brand should be near the start of title for Amazon A10 algorithm
    if brand and brand.lower() not in title[:50].lower():
        warnings.append("Brand not found in first 50 chars of title")

    # WHY: Use word-boundary regex to avoid false positives (e.g. "deal" inside "ideal")
    full_text = (title + " " + " ".join(bullets)).lower()
    for pw in PROMO_WORDS:
        if re.search(rf"\b{re.escape(pw)}\b", full_text):
            errors.append(f"Promotional word found: '{pw}'")

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


def truncate_title(title: str, max_chars: int) -> str:
    """Truncate title at last word boundary if over limit.

    WHY: LLM often generates titles 5-15 chars over limit — cutting mid-word
    looks unprofessional. We cut at the last space that keeps 80%+ of the limit.
    """
    if len(title) <= max_chars:
        return title
    truncated = title[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        return truncated[:last_space]
    return truncated
