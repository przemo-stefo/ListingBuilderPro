# backend/services/ranking_juice_service.py
# Purpose: Ranking Juice algorithm — scores listing ranking potential (0-100)
# NOT for: LLM calls, database ops, or marketplace publishing

"""
Ported from AmazonListingMaster/knowledge/ranking_juice.py.
Five weighted components → single 0-100 score + letter grade.

WHY in FastAPI: Runs on BOTH n8n and fallback paths, so it must live in Python.
"""

from typing import List, Dict


def calculate_ranking_juice(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    backend: str,
    description: str = "",
) -> Dict:
    """
    Calculate Ranking Juice score (0-100).

    Formula:
    RJ = (Coverage × 0.35) + (Exact Match × 0.30) + (Search Volume × 0.20)
         + (Backend Efficiency × 0.10) + (Structure × 0.05)
    """
    coverage = _coverage_score(keywords, title, bullets, backend, description)
    exact = _exact_match_score(keywords, title)
    volume = _search_volume_score(keywords, title, bullets)
    backend_eff = _backend_efficiency(backend)
    structure = _structure_score(title, bullets)

    rj = (
        coverage * 0.35
        + exact * 0.30
        + volume * 0.20
        + backend_eff * 0.10
        + structure * 0.05
    )

    if rj >= 90:
        grade, verdict = "A+", "EXCELLENT - Top 5% listing quality"
    elif rj >= 80:
        grade, verdict = "A", "GREAT - Strong ranking potential"
    elif rj >= 70:
        grade, verdict = "B", "GOOD - Above average, room for improvement"
    elif rj >= 60:
        grade, verdict = "C", "AVERAGE - Needs optimization"
    else:
        grade, verdict = "D", "NEEDS WORK - Significant improvements required"

    return {
        "score": round(rj, 1),
        "grade": grade,
        "verdict": verdict,
        "components": {
            "keyword_coverage": round(coverage, 1),
            "exact_match_density": round(exact, 1),
            "search_volume_weighted": round(volume, 1),
            "backend_efficiency": round(backend_eff, 1),
            "structure_quality": round(structure, 1),
        },
        "weights": {
            "keyword_coverage": 0.35,
            "exact_match_density": 0.30,
            "search_volume_weighted": 0.20,
            "backend_efficiency": 0.10,
            "structure_quality": 0.05,
        },
    }


def quick_ranking_juice(
    keywords: List[Dict], title: str, bullets: List[str], backend: str
) -> int:
    """Quick score — just the number."""
    return int(calculate_ranking_juice(keywords, title, bullets, backend)["score"])


# --- Component calculators ---


def _coverage_score(
    keywords: List[Dict], title: str, bullets: List[str], backend: str, description: str
) -> float:
    """Keyword coverage (0-100). 70%+ word overlap = covered. Scored against top 200."""
    if not keywords:
        return 0
    all_text = (title + " " + " ".join(bullets) + " " + backend + " " + description).lower()
    all_words = set(all_text.split())
    top = keywords[:200]
    covered = 0
    for kw in top:
        phrase_words = set(kw["phrase"].lower().split())
        if not phrase_words:
            continue
        matched = sum(1 for w in phrase_words if w in all_words)
        if matched / len(phrase_words) >= 0.7:
            covered += 1
    # WHY: 98% coverage = perfect score
    return min(100, (covered / len(top)) * 100 / 98 * 100)


def _exact_match_score(keywords: List[Dict], title: str) -> float:
    """Exact phrase matches in title (0-100). Target = 8 matches from top 30."""
    title_lower = title.lower()
    exact = sum(1 for kw in keywords[:30] if kw["phrase"].lower() in title_lower)
    return min(100, (exact / 8) * 100)


def _search_volume_score(
    keywords: List[Dict], title: str, bullets: List[str]
) -> float:
    """Search volume weighted by position (0-100). Title=1.5x, bullets=1x, partial=0.3x."""
    title_lower = title.lower()
    bullets_text = " ".join(bullets).lower()
    top50 = keywords[:50]
    total_vol = sum(kw.get("search_volume", 0) for kw in top50)
    if total_vol == 0:
        return 50  # WHY: Default when no search volume data available

    captured = 0
    for kw in top50:
        vol = kw.get("search_volume", 0)
        phrase = kw["phrase"].lower()
        if phrase in title_lower:
            captured += vol * 1.5
        elif phrase in bullets_text:
            captured += vol * 1.0
        else:
            # WHY: Partial overlap still counts (individual words present)
            phrase_words = set(phrase.split())
            if phrase_words & set(title_lower.split()):
                captured += vol * 0.3

    max_possible = total_vol * 1.5
    return min(100, (captured / max_possible) * 100)


def _backend_efficiency(backend: str) -> float:
    """Backend byte utilization (0-100). Optimal = 240-249 bytes."""
    byte_size = len(backend.encode("utf-8"))
    if byte_size > 250:
        return 50  # WHY: Penalty for exceeding limit
    if 240 <= byte_size <= 249:
        return 100
    if 230 <= byte_size < 240:
        return 95
    if 220 <= byte_size < 230:
        return 85
    if byte_size < 220:
        return (byte_size / 240) * 80
    return (byte_size / 250) * 100


def _structure_score(title: str, bullets: List[str]) -> float:
    """Structure quality (0-100). Checks title length, bullet count/length, dash format."""
    score = 100
    title_len = len(title)
    if title_len < 150:
        score -= 15
    elif title_len > 200:
        score -= 10

    if len(bullets) < 5:
        score -= (5 - len(bullets)) * 5

    for bullet in bullets:
        blen = len(bullet)
        if blen < 100:
            score -= 3
        elif blen > 500:
            score -= 2

    # WHY: Dash separators in title help Amazon's EXACT match indexing
    if " - " in title:
        score += 5

    return max(0, min(100, score))
