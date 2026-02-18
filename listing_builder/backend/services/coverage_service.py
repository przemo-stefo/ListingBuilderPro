# backend/services/coverage_service.py
# Purpose: Multi-tier keyword coverage calculator — per-placement breakdown with 95% target
# NOT for: Keyword placement decisions (that's keyword_placement_service.py)

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple, Set
import structlog

logger = structlog.get_logger()

# WHY: DataDive target is 95% — listings below this leave money on the table
COVERAGE_TARGET = 95.0


def _extract_words(text: str) -> Set[str]:
    """Extract unique words from text using word boundaries.

    WHY: Simple `w in text` is substring matching — "cap" matches "capsule".
    Using regex word extraction gives us a proper word set for O(1) lookup.
    """
    # WHY: Include digits — keywords often contain numbers ("750ml", "1 liter")
    return set(re.findall(r"[a-zA-Z0-9äöüßÄÖÜąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", text.lower()))


def _keyword_covered(phrase: str, word_set: Set[str]) -> bool:
    """Check if >= 70% of a keyword's words appear in the word set."""
    words = phrase.lower().split()
    if not words:
        return False
    matches = sum(1 for w in words if w in word_set)
    return matches / len(words) >= 0.7


def _coverage_for_word_set(
    keywords: List[Dict[str, Any]], word_set: Set[str],
) -> Tuple[float, int, int]:
    """Calculate coverage against a precomputed word set.

    WHY: Avoids recomputing _extract_words when we already have the word set.
    Returns (pct, covered_count, total_count).
    """
    if not keywords:
        return 0.0, 0, 0
    covered = sum(1 for kw in keywords if _keyword_covered(kw["phrase"], word_set))
    total = len(keywords)
    pct = round((covered / total) * 100, 1) if total > 0 else 0.0
    return pct, covered, total


def _coverage_for_text(
    keywords: List[Dict[str, Any]], text: str,
) -> Tuple[float, int, int]:
    """Convenience wrapper — extracts words then delegates to _coverage_for_word_set."""
    return _coverage_for_word_set(keywords, _extract_words(text))


def count_exact_matches(keywords: List[Dict[str, Any]], text: str) -> int:
    """Count keywords whose full phrase appears verbatim in text.

    WHY: Exact phrase matches are stronger ranking signals than partial word matches.
    Used by optimizer_service for the 'exact_matches_in_title' score.
    """
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw["phrase"].lower() in text_lower)


def _grade(pct: float) -> str:
    """Coverage grade label."""
    if pct >= 95:
        return "EXCELLENT"
    if pct >= 85:
        return "GOOD"
    if pct >= 70:
        return "MODERATE"
    return "LOW"


def calculate_multi_tier_coverage(
    keywords: List[Dict[str, Any]],
    title: str,
    bullets: List[str],
    backend: str,
    description: str,
) -> Dict[str, Any]:
    """
    Calculate per-placement and overall coverage.
    WHY: Knowing WHERE keywords are missing lets sellers fix specific sections
    instead of blindly re-optimizing the entire listing.
    """
    bullets_text = " ".join(bullets)
    full_text = f"{title} {bullets_text} {description} {backend}"

    # WHY: Precompute all word sets once — avoids 5x redundant regex extraction
    full_ws = _extract_words(full_text)
    title_ws = _extract_words(title)
    bullets_ws = _extract_words(bullets_text)
    backend_ws = _extract_words(backend)
    desc_ws = _extract_words(description)

    overall_pct, overall_covered, overall_total = _coverage_for_word_set(keywords, full_ws)
    title_pct, _, _ = _coverage_for_word_set(keywords, title_ws)
    bullets_pct, _, _ = _coverage_for_word_set(keywords, bullets_ws)
    backend_pct, _, _ = _coverage_for_word_set(keywords, backend_ws)
    desc_pct, _, _ = _coverage_for_word_set(keywords, desc_ws)

    # WHY: Find keywords not covered anywhere — reuses precomputed full_ws
    missing = [
        kw["phrase"] for kw in keywords
        if not _keyword_covered(kw["phrase"], full_ws)
    ]

    logger.debug(
        "coverage_calculated",
        overall_pct=overall_pct,
        title_pct=title_pct,
        bullets_pct=bullets_pct,
        missing_count=len(missing),
    )

    return {
        "overall_pct": overall_pct,
        "overall_grade": _grade(overall_pct),
        "overall_covered": overall_covered,
        "overall_total": overall_total,
        "target_pct": COVERAGE_TARGET,
        "meets_target": overall_pct >= COVERAGE_TARGET,
        "breakdown": {
            "title_pct": title_pct,
            "bullets_pct": bullets_pct,
            "backend_pct": backend_pct,
            "description_pct": desc_pct,
        },
        "missing_keywords": missing[:20],
    }
