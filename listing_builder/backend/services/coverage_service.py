# backend/services/coverage_service.py
# Purpose: Multi-tier keyword coverage calculator — per-placement breakdown with 95% target
# NOT for: Keyword placement decisions (that's keyword_placement_service.py)

from __future__ import annotations

from typing import List, Dict, Any, Tuple

# WHY: DataDive target is 95% — listings below this leave money on the table
COVERAGE_TARGET = 95.0


def _coverage_for_text(
    keywords: List[Dict[str, Any]], text: str,
) -> Tuple[float, int, int]:
    """
    Calculate what % of keywords have >= 70% of their words in the text.
    Returns (pct, covered_count, total_count).
    """
    if not keywords:
        return 0.0, 0, 0

    text_lower = text.lower()
    covered = 0
    for kw in keywords:
        words = kw["phrase"].lower().split()
        if not words:
            continue
        matches = sum(1 for w in words if w in text_lower)
        if matches / len(words) >= 0.7:
            covered += 1

    total = len(keywords)
    pct = round((covered / total) * 100, 1) if total > 0 else 0.0
    return pct, covered, total


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

    overall_pct, overall_covered, overall_total = _coverage_for_text(keywords, full_text)
    title_pct, _, _ = _coverage_for_text(keywords, title)
    bullets_pct, _, _ = _coverage_for_text(keywords, bullets_text)
    backend_pct, _, _ = _coverage_for_text(keywords, backend)
    desc_pct, _, _ = _coverage_for_text(keywords, description)

    # WHY: Find keywords not covered anywhere in the listing
    missing = _find_missing(keywords, full_text)

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


def _find_missing(
    keywords: List[Dict[str, Any]], text: str,
) -> List[str]:
    """Keywords where < 70% of words appear in the full listing."""
    text_lower = text.lower()
    missing = []
    for kw in keywords:
        words = kw["phrase"].lower().split()
        if not words:
            continue
        matches = sum(1 for w in words if w in text_lower)
        if matches / len(words) < 0.7:
            missing.append(kw["phrase"])
    return missing
