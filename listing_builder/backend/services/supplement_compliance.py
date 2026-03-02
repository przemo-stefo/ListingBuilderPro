# backend/services/supplement_compliance.py
# Purpose: EU compliance checker for supplement listings (HCPR, GPSR, allergens)
# NOT for: General Compliance Guard (XLSM validation) or non-supplement products

import re
import structlog
from typing import Dict, List, Any

logger = structlog.get_logger()

# WHY: EC 1924/2006 forbids health claims without EFSA authorization
# These phrases trigger WARNING or FAIL depending on context
FORBIDDEN_HEALTH_CLAIMS = {
    # German
    "heilt", "heilung", "behandelt", "therapie", "verhindert krankheit",
    "krebshemmend", "anti-krebs", "senkt blutdruck", "senkt cholesterin",
    "stärkt immunsystem", "bekämpft viren", "tötet bakterien",
    "schützt vor krebs", "heilt diabetes", "anti-aging wirkung",
    "entgiftet den körper", "verbrennt fett", "gewichtsverlust garantiert",
    # English
    "cures", "treats disease", "prevents illness", "anti-cancer",
    "lowers blood pressure", "kills bacteria", "fights viruses",
    "boosts immunity", "detoxifies body", "burns fat guaranteed",
    "guaranteed weight loss", "heals", "therapeutic effect",
    # Polish
    "leczy", "zapobiega chorobom", "zwalcza wirusy", "obniża ciśnienie",
    "gwarantowana utrata wagi", "oczyszcza organizm z toksyn",
}

# WHY: EU FIC 1169/2011 — 14 mandatory allergen declarations
EU_ALLERGENS = [
    "gluten", "weizen", "wheat", "crustaceans", "krebstiere",
    "eier", "eggs", "fisch", "fish", "erdnüsse", "peanuts",
    "soja", "soy", "milch", "milk", "laktose", "lactose",
    "schalenfrüchte", "nuts", "sellerie", "celery",
    "senf", "mustard", "sesam", "sesame", "sulfite", "schwefeldioxid",
    "lupinen", "lupin", "weichtiere", "molluscs",
]

# WHY: Dosage claims that need EFSA substantiation
DOSAGE_CLAIM_PATTERNS = [
    r"\d+\s*mg.*(?:pro tag|daily|täglich)",
    r"(?:empfohlene|recommended).*(?:dosis|dose|dosierung)",
    r"(?:hochdosiert|high[- ]?dose)",
]


def check_supplement_compliance(
    title: str,
    bullets: List[str],
    description: str,
    manufacturer: str = "",
    category: str = "",
) -> Dict[str, Any]:
    """Run EU supplement compliance checks on listing content.

    Returns: {status, issues, score, checks_run}
    """
    issues: List[Dict[str, str]] = []
    full_text = f"{title} {' '.join(bullets)} {description}".lower()

    # --- Check 1: EC 1924/2006 — Forbidden health claims ---
    for claim in FORBIDDEN_HEALTH_CLAIMS:
        if claim in full_text:
            # WHY: Determine which field contains the claim for actionable feedback
            field = "title" if claim in title.lower() else (
                "bullets" if any(claim in b.lower() for b in bullets) else "description"
            )
            issues.append({
                "field": field,
                "severity": "FAIL",
                "message": f"Forbidden health claim: '{claim}'",
                "regulation": "EC 1924/2006 (Health Claims Regulation)",
            })

    # --- Check 2: GPSR — Manufacturer info ---
    if not manufacturer or len(manufacturer) < 10:
        issues.append({
            "field": "manufacturer",
            "severity": "FAIL",
            "message": "Missing manufacturer info (name, address, country required)",
            "regulation": "EU GPSR (General Product Safety Regulation)",
        })
    else:
        # WHY: GPSR requires full address with country code
        has_country = bool(re.search(r"\b[A-Z]{2}\b", manufacturer))
        if not has_country:
            issues.append({
                "field": "manufacturer",
                "severity": "WARNING",
                "message": "Manufacturer info missing country code (e.g., DE, PL)",
                "regulation": "EU GPSR (General Product Safety Regulation)",
            })

    # --- Check 3: EU FIC 1169/2011 — Allergen declaration ---
    mentions_allergen = any(a in full_text for a in EU_ALLERGENS)
    has_allergen_statement = any(
        phrase in full_text
        for phrase in ["allergen", "enthält keine", "frei von", "allergen-free", "bez alergenów"]
    )
    if not mentions_allergen and not has_allergen_statement:
        issues.append({
            "field": "description",
            "severity": "WARNING",
            "message": "No allergen declaration found — supplements should declare allergen status",
            "regulation": "EU FIC 1169/2011 (Food Information to Consumers)",
        })

    # --- Check 4: Dosage claims needing substantiation ---
    for pattern in DOSAGE_CLAIM_PATTERNS:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for match in matches:
            issues.append({
                "field": "description",
                "severity": "WARNING",
                "message": f"Dosage claim may require EFSA substantiation: '{match}'",
                "regulation": "EC 1924/2006 Art. 13",
            })

    # --- Check 5: Title length (Amazon max 200 chars) ---
    if len(title) > 200:
        issues.append({
            "field": "title",
            "severity": "FAIL",
            "message": f"Title exceeds Amazon 200 char limit ({len(title)} chars)",
            "regulation": "Amazon Listing Policy",
        })

    # --- Calculate score ---
    fail_count = sum(1 for i in issues if i["severity"] == "FAIL")
    warn_count = sum(1 for i in issues if i["severity"] == "WARNING")
    score = max(0, 100 - (fail_count * 20) - (warn_count * 5))

    status = "FAIL" if fail_count > 0 else ("WARNING" if warn_count > 0 else "PASS")

    logger.info("supplement_compliance_check",
                status=status, score=score, fails=fail_count, warnings=warn_count)

    return {
        "status": status,
        "score": score,
        "issues": issues,
        "checks_run": 5,
        "summary": {
            "fail_count": fail_count,
            "warning_count": warn_count,
            "pass_count": 5 - fail_count - min(warn_count, 5 - fail_count),
        },
    }
