# backend/services/amazon_tos_checker.py
# Purpose: Amazon TOS compliance checker — detects listing suppression risks
# NOT for: LLM scoring or keyword placement — purely rule-based validation

from __future__ import annotations

import re
from typing import List, Dict, Any

# WHY: Amazon auto-suppresses listings with these promotional phrases (2025+ enforcement)
PROMO_PHRASES = [
    "best seller", "bestseller", "best selling", "top seller", "top rated",
    "best deal", "best price", "#1", "nr 1", "no. 1", "number one",
    "hot item", "sale", "discount", "free shipping", "free gift",
    "on sale", "limited time", "special offer", "huge sale", "close-out",
    "deal", "cheap", "cheapest", "buy now", "shop now", "don't miss out",
    "guaranteed", "money back", "risk-free", "award winning", "proven",
    "100% natural", "100% effective", "100% quality", "premium quality",
    "highest quality", "buy with confidence", "unlike other brands",
    "perfect", "ultimate", "amazing", "incredible", "unbeatable",
    "fooled", "lush", "angebot", "sonderangebot", "ausverkauf",
    "günstig", "billig", "gratis", "rabatt", "preiswert",
]

# WHY: Health/medical claims trigger FDA review → immediate suppression
HEALTH_CLAIMS = [
    "cure", "cures", "treat", "treats", "treatment", "heal", "healing",
    "remedy", "remedies", "medication", "diagnose", "prevent", "prevents",
    "mitigate", "weight loss", "fat burning", "appetite suppressant",
    "boosts metabolism", "reduces cholesterol", "aids digestion",
    "detox", "detoxify", "detoxification", "reduce anxiety",
    "insomnia", "increases energy", "joint pain", "heartburn",
    "inflammation", "arthritis", "immune booster",
]

# WHY: Pesticide/antimicrobial claims require EPA registration → suppression
PESTICIDE_CLAIMS = [
    "antibacterial", "anti-bacterial", "antimicrobial", "anti-microbial",
    "antifungal", "fungicide", "sanitize", "sanitizes", "disinfect",
    "kills bacteria", "kills viruses", "kills germs", "mold resistant",
    "mildew resistant", "repels insects", "antiseptic",
]

# WHY: Drug-related keywords → immediate takedown, possible account ban
DRUG_KEYWORDS = [
    "cbd", "cannabinoid", "thc", "full spectrum hemp", "marijuana",
    "kratom", "psilocybin", "ephedrine", "ketamine",
]

# WHY: Eco claims without certification = suppression (Amazon Green Claims policy)
ECO_CLAIMS = [
    "eco-friendly", "eco friendly", "biodegradable", "compostable",
    "environmentally friendly", "carbon neutral", "carbon-reducing",
    "decomposable", "degradable",
]

# WHY: These special characters are prohibited in Amazon titles
FORBIDDEN_TITLE_CHARS = set("!$?_{}^~#<>|*;\\\"¡€™®©")

# WHY: Amazon suppresses listings with any external references
EXTERNAL_PATTERNS = [
    (r"https?://\S+", "URL found"),
    (r"www\.\S+", "URL found"),
    (r"\b[\w.-]+@[\w.-]+\.\w+\b", "Email address found"),
    (r"\+?\d[\d\s-]{8,}", "Phone number found"),
]


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
        return {"violations": [], "severity": "PASS", "suppression_risk": False}

    violations: List[Dict[str, str]] = []

    # --- TITLE CHECKS ---
    _check_title_format(title, violations)

    # --- CONTENT CHECKS (title + bullets + description) ---
    full_visible = f"{title} {' '.join(bullets)} {description}"
    _check_prohibited_claims(full_visible, violations)
    _check_external_references(full_visible, violations)

    # --- BACKEND KEYWORDS CHECKS ---
    if backend_keywords:
        _check_backend_keywords(backend_keywords, violations)

    # --- SEVERITY ---
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
    for w in re.findall(r"[a-zA-ZäöüßÄÖÜąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", title.lower()):
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
    """Check for promotional, health, pesticide, drug, eco claims."""
    text_lower = text.lower()

    # Promotional phrases
    for phrase in PROMO_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            violations.append({
                "rule": "promo_phrase",
                "severity": "SUPPRESSION",
                "message": f"Zabroniona fraza promocyjna: '{phrase}'",
                "field": "content",
            })

    # Health claims
    for claim in HEALTH_CLAIMS:
        if re.search(rf"\b{re.escape(claim)}\b", text_lower):
            violations.append({
                "rule": "health_claim",
                "severity": "SUPPRESSION",
                "message": f"Roszczenie zdrowotne (FDA): '{claim}'",
                "field": "content",
            })

    # Pesticide claims
    for claim in PESTICIDE_CLAIMS:
        if re.search(rf"\b{re.escape(claim)}\b", text_lower):
            violations.append({
                "rule": "pesticide_claim",
                "severity": "SUPPRESSION",
                "message": f"Roszczenie pestycydowe (EPA): '{claim}'",
                "field": "content",
            })

    # Drug keywords
    for kw in DRUG_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            violations.append({
                "rule": "drug_keyword",
                "severity": "SUPPRESSION",
                "message": f"Słowo kluczowe narkotykowe: '{kw}'",
                "field": "content",
            })

    # Eco claims without certification
    for claim in ECO_CLAIMS:
        if re.search(rf"\b{re.escape(claim)}\b", text_lower):
            violations.append({
                "rule": "eco_claim",
                "severity": "WARNING",
                "message": f"Roszczenie ekologiczne bez certyfikatu: '{claim}'",
                "field": "content",
            })


def _check_external_references(text: str, violations: List[Dict]) -> None:
    """Check for URLs, emails, phone numbers — all prohibited."""
    for pattern, description in EXTERNAL_PATTERNS:
        if re.search(pattern, text):
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
    if re.search(r"\bB0[A-Z0-9]{8}\b", keywords.upper()):
        violations.append({
            "rule": "backend_asin",
            "severity": "SUPPRESSION",
            "message": "ASIN konkurencji w backend keywords — ryzyko zawieszenia konta",
            "field": "backend_keywords",
        })

    # WHY: Subjective claims waste bytes and can trigger review
    subjective = ["best", "amazing", "perfect", "cheapest", "top-rated", "new", "on sale"]
    kw_lower = keywords.lower()
    for word in subjective:
        if re.search(rf"\b{re.escape(word)}\b", kw_lower):
            violations.append({
                "rule": "backend_subjective",
                "severity": "WARNING",
                "message": f"Subiektywne słowo w backend keywords: '{word}' — marnuje bajty",
                "field": "backend_keywords",
            })
