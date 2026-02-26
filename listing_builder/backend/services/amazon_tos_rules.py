# backend/services/amazon_tos_rules.py
# Purpose: Amazon TOS violation rules — phrase lists, forbidden chars, patterns
# NOT for: Validation logic (that's amazon_tos_checker.py)

import re


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
    (re.compile(r"https?://\S+"), "URL found"),
    (re.compile(r"www\.\S+"), "URL found"),
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"), "Email address found"),
    (re.compile(r"\+?\d[\d\s-]{8,}"), "Phone number found"),
]


def _build_phrase_pattern(phrases: list) -> re.Pattern:
    """Pre-compile a single regex matching any phrase from list (word-boundary)."""
    escaped = [re.escape(p) for p in phrases]
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)


# WHY: Pre-compiled patterns — 1 regex per category instead of ~107 individual re.search() calls
PROMO_RE = _build_phrase_pattern(PROMO_PHRASES)
HEALTH_RE = _build_phrase_pattern(HEALTH_CLAIMS)
PESTICIDE_RE = _build_phrase_pattern(PESTICIDE_CLAIMS)
DRUG_RE = _build_phrase_pattern(DRUG_KEYWORDS)
ECO_RE = _build_phrase_pattern(ECO_CLAIMS)
BACKEND_SUBJ_RE = _build_phrase_pattern(
    ["best", "amazing", "perfect", "cheapest", "top-rated", "new", "on sale"]
)
ASIN_RE = re.compile(r"\bB0[A-Z0-9]{8}\b")

# WHY: Pre-compiled for _check_title_format — Unicode word chars including DE/PL diacritics
TITLE_WORD_RE = re.compile(r"[a-zA-ZäöüßÄÖÜąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+")
