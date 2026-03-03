# backend/services/category_prompts.py
# Purpose: Category-specific optimization rules injected into LLM prompts
# NOT for: Generic Amazon rules (those are in prompt_builders.py)

from __future__ import annotations
from typing import Dict

# WHY: Michał Lasocki feedback (2026-03-03) — "SEO AI działa generycznie".
# Category-specific instructions make output dramatically better because
# supplements need compliance language, electronics need specs, etc.

SUPPLEMENT_RULES = {
    "title": """
SUPPLEMENT-SPECIFIC TITLE RULES:
- Include dosage (mg/mcg) and count (Tabletten/Kapseln) — buyers filter by this
- Include form: Tabletten, Kapseln, Pulver, Tropfen, Presslinge
- Include certification: BIO, Vegan, Laborgeprüft, Ohne Zusatzstoffe
- Include supply duration: "X Monate Vorrat" (German buyers love value math)
- NEVER use health claims: "heilt", "cures", "prevents disease", "immune booster"
- NEVER use superlatives: "best", "strongest", "#1", "most effective"
""",
    "bullets": """
SUPPLEMENT-SPECIFIC BULLET RULES:
- Bullet 1: Core product specs (dosage, count, form, supply duration)
- Bullet 2: Key ingredient quality (source, purity, bio-availability)
- Bullet 3: Certifications & testing (lab-tested, BIO, GMP, ISO, DE-ÖKO)
- Bullet 4: What's NOT in it (keine Zusatzstoffe, kein Magnesiumstearat, glutenfrei, laktosefrei)
- Bullet 5: Usage instructions (Einnahmeempfehlung — daily dose, with meal/water)
- COMPLIANCE: Never claim to treat, cure, or prevent any disease (EU EC 1924/2006)
- COMPLIANCE: Never use "clinically proven" without citing the actual study
- Use factual nutrient statements: "enthält 15mg Eisen pro Tagesdosis" (OK)
- AVOID subjective health claims: "stärkt das Immunsystem" (FORBIDDEN without EFSA approval)
""",
    "description": """
SUPPLEMENT-SPECIFIC DESCRIPTION RULES:
- Paragraph 1: What the product IS (ingredient, form, dosage, origin)
- Paragraph 2: Quality & certifications (lab reports, BIO, manufacturing standards)
- Paragraph 3: How to use (daily dose, best time, with food/water, storage)
- Include GPSR manufacturer info (name, address, country) — EU required since 2024
- NEVER make therapeutic claims or reference diseases
- Use permitted nutrient claims from EU Register: "Eisen trägt zur normalen Bildung von roten Blutkörperchen bei" (EFSA approved)
- Allergen declaration: mention if free from major allergens (gluten, lactose, soy, nuts)
""",
    "backend": """
SUPPLEMENT-SPECIFIC BACKEND RULES:
- Include ingredient synonyms (e.g., spirulina = arthrospira platensis = blaualge = microalge)
- Include common misspellings (e.g., "spirullina", "spriulina")
- Include use-case terms (e.g., "nahrungsergänzung sport fitness ernährung gesundheit")
- Include form variants (tabletten kapseln pulver presslinge pillen)
- NEVER include disease names or drug names
""",
}

ELECTRONICS_RULES = {
    "title": """
ELECTRONICS-SPECIFIC TITLE RULES:
- Lead with product type + key specs (e.g., "Bluetooth Kopfhörer 40h Akku ANC")
- Include compatibility info (iPhone, Android, USB-C, Bluetooth 5.3)
- Include key performance numbers (mAh, dB, Hz, Watt)
- Color/size variant at the end: "[Schwarz]" or "- Schwarz"
""",
    "bullets": """
ELECTRONICS-SPECIFIC BULLET RULES:
- Bullet 1: Hero spec (battery life, noise cancellation level, resolution)
- Bullet 2: Connectivity & compatibility (Bluetooth version, supported devices)
- Bullet 3: Build quality & comfort (materials, weight, IPX rating)
- Bullet 4: What's in the box (cable, case, adapters, manual)
- Bullet 5: Warranty & support (manufacturer guarantee, CE marking)
- Use measurable specs: "40 Stunden Akkulaufzeit" NOT "extra langer Akku"
""",
    "description": """
ELECTRONICS-SPECIFIC DESCRIPTION RULES:
- Lead with the problem the product solves, then specs
- Include technical specifications in a structured way
- Mention CE marking and relevant EU directives
- Include compatibility list (devices, OS versions)
""",
    "backend": """
ELECTRONICS-SPECIFIC BACKEND RULES:
- Include model number variants and abbreviations
- Include competitor-neutral category terms (e.g., "over ear headphones bluetooth")
- Include use-case terms (office, sport, travel, gaming)
""",
}

BEAUTY_RULES = {
    "title": """
BEAUTY-SPECIFIC TITLE RULES:
- Include volume/weight (ml, g, oz) and product type
- Include key ingredients (Hyaluronsäure, Vitamin C, Retinol, Niacinamid)
- Include skin type if relevant (trockene Haut, fettige Haut, empfindliche Haut)
- Include "Dermatologisch getestet" if applicable
""",
    "bullets": """
BEAUTY-SPECIFIC BULLET RULES:
- Bullet 1: Key active ingredient + what it does (factual, not miracle claims)
- Bullet 2: Skin type & application area
- Bullet 3: Texture & sensory experience (non-sticky, fast-absorbing)
- Bullet 4: What's NOT in it (parabenfrei, silikonfrei, vegan, tierversuchsfrei)
- Bullet 5: How to use (application instructions, frequency)
- COMPLIANCE: Never claim medical skin treatment (EU Cosmetics Regulation EC 1223/2009)
""",
    "description": """
BEAUTY-SPECIFIC DESCRIPTION RULES:
- Focus on sensory experience and routine integration
- Include full INCI ingredient list mention
- Include storage instructions if relevant
- GPSR manufacturer info required
""",
    "backend": """
BEAUTY-SPECIFIC BACKEND RULES:
- Include ingredient synonyms (e.g., vitamin c = ascorbinsäure = l-ascorbic acid)
- Include skin concern terms (anti-aging, anti-falten, feuchtigkeit, akne)
""",
}

# WHY: Map common Amazon category names to rule sets.
# Matching is case-insensitive substring check — "Health & Household" hits "health"
_CATEGORY_MAP: Dict[str, Dict[str, str]] = {
    "supplement": SUPPLEMENT_RULES,
    "health": SUPPLEMENT_RULES,
    "vitamin": SUPPLEMENT_RULES,
    "dietary": SUPPLEMENT_RULES,
    "nahrungsergänzung": SUPPLEMENT_RULES,
    "electronic": ELECTRONICS_RULES,
    "computer": ELECTRONICS_RULES,
    "headphone": ELECTRONICS_RULES,
    "audio": ELECTRONICS_RULES,
    "beauty": BEAUTY_RULES,
    "skin": BEAUTY_RULES,
    "cosmetic": BEAUTY_RULES,
    "hair": BEAUTY_RULES,
}


def get_category_rules(category: str, section: str) -> str:
    """Get category-specific prompt rules for a section.

    Args:
        category: Product category (e.g. "Health & Household", "supplements")
        section: One of "title", "bullets", "description", "backend"

    Returns:
        Category-specific rules string, or empty string if no match.
    """
    if not category:
        return ""

    cat_lower = category.lower()
    for key, rules in _CATEGORY_MAP.items():
        if key in cat_lower:
            return rules.get(section, "")

    return ""
