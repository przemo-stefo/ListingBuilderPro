# backend/services/amazon_tos_checker.py
# Purpose: Amazon TOS compliance checker — detects listing suppression risks
# NOT for: LLM scoring, keyword placement, or rule data (that's amazon_tos_rules.py)

from __future__ import annotations

from typing import List, Dict, Any
from services.amazon_tos_rules import (
    FORBIDDEN_TITLE_CHARS, EXTERNAL_PATTERNS, TITLE_WORD_RE,
    PROMO_RE, HEALTH_RE, PESTICIDE_RE, DRUG_RE, ECO_RE,
    BACKEND_SUBJ_RE, ASIN_RE,
)


def check_amazon_tos(
    title: str,
    bullets: List[str],
    description: str,
    backend_keywords: str = "",
    marketplace: str = "amazon",
) -> Dict[str, Any]:
    """Run full Amazon TOS compliance check. Returns violations by severity.

    WHY: Amazon's 2025 AI scanning catches violations that the basic check_compliance() misses.
    This catches suppression-level violations BEFORE the listing goes live.
    """
    if not marketplace.startswith("amazon"):
        return {"violations": [], "severity": "PASS", "suppression_risk": False, "violation_count": 0}

    violations: List[Dict[str, str]] = []

    _check_title_format(title, violations)

    full_visible = f"{title} {' '.join(bullets)} {description}"
    _check_prohibited_claims(full_visible, violations)
    _check_external_references(full_visible, violations)

    if backend_keywords:
        _check_backend_keywords(backend_keywords, violations)

    has_suppression = any(v["severity"] == "SUPPRESSION" for v in violations)
    has_warning = any(v["severity"] == "WARNING" for v in violations)

    if has_suppression:
        severity = "FAIL"
    elif has_warning:
        severity = "WARN"
    else:
        severity = "PASS"

    return {
        "violations": violations,
        "severity": severity,
        "suppression_risk": has_suppression,
        "violation_count": len(violations),
    }


def _check_title_format(title: str, violations: List[Dict]) -> None:
    """Amazon title formatting rules — 2025 enforcement."""
    # WHY: 200 char hard limit — Amazon truncates or suppresses
    if len(title) > 200:
        violations.append({
            "rule": "title_length",
            "severity": "SUPPRESSION",
            "message": f"Tytuł przekracza 200 znaków ({len(title)})",
            "field": "title",
        })

    # WHY: ALL CAPS words trigger auto-correction (Jan 2025 policy)
    words = title.split()
    caps_words = [w for w in words if len(w) > 3 and w == w.upper() and w.isalpha()]
    if caps_words:
        violations.append({
            "rule": "title_all_caps",
            "severity": "SUPPRESSION",
            "message": f"Słowa pisane WIELKIMI LITERAMI: {', '.join(caps_words[:3])}",
            "field": "title",
        })

    # WHY: Same word >2x in title = suppression (Amazon 2025 rule)
    word_counts: Dict[str, int] = {}
    for w in TITLE_WORD_RE.findall(title.lower()):
        if len(w) > 2:
            word_counts[w] = word_counts.get(w, 0) + 1
    for word, count in word_counts.items():
        if count > 2:
            violations.append({
                "rule": "title_word_repetition",
                "severity": "SUPPRESSION",
                "message": f"Słowo '{word}' powtórzone {count}x w tytule (max 2x)",
                "field": "title",
            })

    # WHY: Forbidden special characters → suppression
    found_chars = [ch for ch in title if ch in FORBIDDEN_TITLE_CHARS]
    if found_chars:
        violations.append({
            "rule": "title_forbidden_chars",
            "severity": "SUPPRESSION",
            "message": f"Zabronione znaki w tytule: {' '.join(set(found_chars))}",
            "field": "title",
        })


def _check_prohibited_claims(text: str, violations: List[Dict]) -> None:
    """Check for promotional, health, pesticide, drug, eco claims.

    WHY: Uses pre-compiled single-pattern regexes instead of ~100 individual re.search() calls.
    """
    claim_checks = [
        (PROMO_RE, "promo_phrase", "SUPPRESSION", "Zabroniona fraza promocyjna"),
        (HEALTH_RE, "health_claim", "SUPPRESSION", "Roszczenie zdrowotne (FDA)"),
        (PESTICIDE_RE, "pesticide_claim", "SUPPRESSION", "Roszczenie pestycydowe (EPA)"),
        (DRUG_RE, "drug_keyword", "SUPPRESSION", "Słowo kluczowe narkotykowe"),
        (ECO_RE, "eco_claim", "WARNING", "Roszczenie ekologiczne bez certyfikatu"),
    ]

    for pattern, rule, severity, label in claim_checks:
        for match in pattern.finditer(text):
            violations.append({
                "rule": rule,
                "severity": severity,
                "message": f"{label}: '{match.group()}'",
                "field": "content",
            })


def _check_external_references(text: str, violations: List[Dict]) -> None:
    """Check for URLs, emails, phone numbers — all prohibited."""
    for compiled_re, description in EXTERNAL_PATTERNS:
        if compiled_re.search(text):
            violations.append({
                "rule": "external_reference",
                "severity": "SUPPRESSION",
                "message": f"Zewnętrzna referencja: {description}",
                "field": "content",
            })


def _check_backend_keywords(keywords: str, violations: List[Dict]) -> None:
    """Backend search terms validation — 250 bytes, no ASINs, no competitor brands."""
    # WHY: Exceeding 250 bytes silently de-indexes ALL backend keywords
    byte_count = len(keywords.encode("utf-8"))
    if byte_count > 250:
        violations.append({
            "rule": "backend_byte_limit",
            "severity": "SUPPRESSION",
            "message": f"Backend keywords przekraczają 250 bajtów ({byte_count}B) — CAŁY blok nie będzie indeksowany",
            "field": "backend_keywords",
        })

    # WHY: ASINs in backend = IP violation risk
    if ASIN_RE.search(keywords.upper()):
        violations.append({
            "rule": "backend_asin",
            "severity": "SUPPRESSION",
            "message": "ASIN konkurencji w backend keywords — ryzyko zawieszenia konta",
            "field": "backend_keywords",
        })

    # WHY: Subjective claims waste bytes and can trigger review
    for match in BACKEND_SUBJ_RE.finditer(keywords):
        violations.append({
            "rule": "backend_subjective",
            "severity": "WARNING",
            "message": f"Subiektywne słowo w backend keywords: '{match.group()}' — marnuje bajty",
            "field": "backend_keywords",
        })
