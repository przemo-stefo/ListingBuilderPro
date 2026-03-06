# backend/data/efsa_claims.py
# Purpose: EFSA-approved health claims database for EU supplement compliance
# NOT for: FDA claims, non-EU markets, or LLM-generated content

from typing import Dict, List, Any, Optional
import re


# WHY: ~50 most common supplement ingredients with their EFSA-approved claims
# Source: EU Register of nutrition and health claims (EC 432/2012)
# Each entry: approved claims (DE + EN) + common forbidden phrasings
EFSA_CLAIMS_DB: Dict[str, Dict[str, Any]] = {
    # --- Vitamins ---
    "vitamin b12": {
        "approved_claims": {
            "de": [
                "trägt zur normalen Funktion des Nervensystems bei",
                "trägt zur normalen psychischen Funktion bei",
                "trägt zu einem normalen Energiestoffwechsel bei",
                "trägt zur normalen Bildung roter Blutkörperchen bei",
                "trägt zur Verringerung von Müdigkeit und Ermüdung bei",
            ],
            "en": [
                "contributes to normal functioning of the nervous system",
                "contributes to normal psychological function",
                "contributes to normal energy-yielding metabolism",
                "contributes to normal red blood cell formation",
                "contributes to the reduction of tiredness and fatigue",
            ],
        },
        "forbidden_patterns": [
            r"boost(?:s|ing)?\s+brain",
            r"heilt?\s+nerven",
            r"steigert?\s+(?:die\s+)?energie",
            r"cures?\s+fatigue",
            r"(?:super|mega)\s*energy",
        ],
    },
    "vitamin c": {
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Funktion des Immunsystems bei",
                "trägt dazu bei, die Zellen vor oxidativem Stress zu schützen",
                "trägt zu einer normalen Kollagenbildung bei",
                "erhöht die Eisenaufnahme",
                "trägt zur Verringerung von Müdigkeit und Ermüdung bei",
            ],
            "en": [
                "contributes to the normal function of the immune system",
                "contributes to the protection of cells from oxidative stress",
                "contributes to normal collagen formation",
                "increases iron absorption",
                "contributes to the reduction of tiredness and fatigue",
            ],
        },
        "forbidden_patterns": [
            r"boost(?:s|ing)?\s+immun",
            r"stärkt?\s+(?:das\s+)?immunsystem",
            r"prevents?\s+(?:colds?|flu|illness)",
            r"verhindert?\s+(?:erkältung|grippe)",
            r"anti[\s-]?aging",
        ],
    },
    "vitamin d": {
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Funktion des Immunsystems bei",
                "trägt zur Erhaltung normaler Knochen bei",
                "trägt zur Erhaltung einer normalen Muskelfunktion bei",
                "trägt zu einer normalen Aufnahme/Verwertung von Calcium und Phosphor bei",
            ],
            "en": [
                "contributes to the normal function of the immune system",
                "contributes to the maintenance of normal bones",
                "contributes to the maintenance of normal muscle function",
                "contributes to normal absorption/utilisation of calcium and phosphorus",
            ],
        },
        "forbidden_patterns": [
            r"prevents?\s+(?:cancer|osteoporosis)",
            r"verhindert?\s+(?:krebs|osteoporose)",
            r"heilt?\s+knochen",
            r"cures?\s+bone",
            r"boost(?:s|ing)?\s+immun",
        ],
    },
    "vitamin e": {
        "approved_claims": {
            "de": [
                "trägt dazu bei, die Zellen vor oxidativem Stress zu schützen",
            ],
            "en": [
                "contributes to the protection of cells from oxidative stress",
            ],
        },
        "forbidden_patterns": [
            r"anti[\s-]?aging",
            r"prevents?\s+(?:cancer|heart)",
            r"verjüng",
        ],
    },
    "vitamin b6": {
        "approved_claims": {
            "de": [
                "trägt zur normalen Funktion des Nervensystems bei",
                "trägt zu einem normalen Eiweiß- und Glykogenstoffwechsel bei",
                "trägt zur Regulierung der Hormontätigkeit bei",
                "trägt zur Verringerung von Müdigkeit und Ermüdung bei",
            ],
            "en": [
                "contributes to normal functioning of the nervous system",
                "contributes to normal protein and glycogen metabolism",
                "contributes to the regulation of hormonal activity",
                "contributes to the reduction of tiredness and fatigue",
            ],
        },
        "forbidden_patterns": [
            r"cures?\s+depression",
            r"heilt?\s+depression",
            r"boost(?:s|ing)?\s+mood",
        ],
    },
    # --- Minerals ---
    "eisen": {
        "aliases": ["iron", "fe"],
        "approved_claims": {
            "de": [
                "trägt zur normalen Bildung von roten Blutkörperchen und Hämoglobin bei",
                "trägt zu einem normalen Sauerstofftransport im Körper bei",
                "trägt zu einer normalen Funktion des Immunsystems bei",
                "trägt zur Verringerung von Müdigkeit und Ermüdung bei",
                "trägt zu einer normalen kognitiven Funktion bei",
            ],
            "en": [
                "contributes to normal formation of red blood cells and haemoglobin",
                "contributes to normal oxygen transport in the body",
                "contributes to the normal function of the immune system",
                "contributes to the reduction of tiredness and fatigue",
                "contributes to normal cognitive function",
            ],
        },
        "forbidden_patterns": [
            r"heilt?\s+(?:anämie|blutarmut)",
            r"cures?\s+(?:anemia|anaemia)",
            r"boost(?:s|ing)?\s+(?:blood|energy)",
        ],
    },
    "zink": {
        "aliases": ["zinc", "zn"],
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Funktion des Immunsystems bei",
                "trägt zur Erhaltung normaler Haut bei",
                "trägt zur Erhaltung normaler Haare bei",
                "trägt zur Erhaltung normaler Nägel bei",
                "trägt dazu bei, die Zellen vor oxidativem Stress zu schützen",
            ],
            "en": [
                "contributes to the normal function of the immune system",
                "contributes to the maintenance of normal skin",
                "contributes to the maintenance of normal hair",
                "contributes to the maintenance of normal nails",
                "contributes to the protection of cells from oxidative stress",
            ],
        },
        "forbidden_patterns": [
            r"boost(?:s|ing)?\s+immun",
            r"stärkt?\s+(?:das\s+)?immunsystem",
            r"heilt?\s+haut",
            r"cures?\s+skin",
            r"anti[\s-]?acne",
        ],
    },
    "magnesium": {
        "approved_claims": {
            "de": [
                "trägt zur Verringerung von Müdigkeit und Ermüdung bei",
                "trägt zu einer normalen Muskelfunktion bei",
                "trägt zur normalen psychischen Funktion bei",
                "trägt zur Erhaltung normaler Knochen bei",
                "trägt zu einem normalen Energiestoffwechsel bei",
            ],
            "en": [
                "contributes to the reduction of tiredness and fatigue",
                "contributes to normal muscle function",
                "contributes to normal psychological function",
                "contributes to the maintenance of normal bones",
                "contributes to normal energy-yielding metabolism",
            ],
        },
        "forbidden_patterns": [
            r"cures?\s+(?:cramps?|insomnia)",
            r"heilt?\s+(?:krämpfe|schlaflosigkeit)",
            r"(?:super|mega)\s*(?:relax|calm)",
        ],
    },
    "selen": {
        "aliases": ["selenium", "se"],
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Funktion des Immunsystems bei",
                "trägt zu einer normalen Schilddrüsenfunktion bei",
                "trägt dazu bei, die Zellen vor oxidativem Stress zu schützen",
                "trägt zur Erhaltung normaler Haare bei",
                "trägt zur Erhaltung normaler Nägel bei",
            ],
            "en": [
                "contributes to the normal function of the immune system",
                "contributes to normal thyroid function",
                "contributes to the protection of cells from oxidative stress",
                "contributes to the maintenance of normal hair",
                "contributes to the maintenance of normal nails",
            ],
        },
        "forbidden_patterns": [
            r"prevents?\s+cancer",
            r"verhindert?\s+krebs",
            r"anti[\s-]?cancer",
        ],
    },
    "calcium": {
        "approved_claims": {
            "de": [
                "trägt zur Erhaltung normaler Knochen bei",
                "trägt zur Erhaltung normaler Zähne bei",
                "trägt zu einer normalen Muskelfunktion bei",
                "wird für die Erhaltung normaler Knochen bei Kindern benötigt",
            ],
            "en": [
                "contributes to the maintenance of normal bones",
                "contributes to the maintenance of normal teeth",
                "contributes to normal muscle function",
                "is needed for the maintenance of normal bones in children",
            ],
        },
        "forbidden_patterns": [
            r"prevents?\s+osteoporosis",
            r"verhindert?\s+osteoporose",
            r"heilt?\s+knochen",
        ],
    },
    "jod": {
        "aliases": ["iodine", "iod"],
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Schilddrüsenfunktion bei",
                "trägt zu einer normalen kognitiven Funktion bei",
                "trägt zu einem normalen Energiestoffwechsel bei",
            ],
            "en": [
                "contributes to normal thyroid function",
                "contributes to normal cognitive function",
                "contributes to normal energy-yielding metabolism",
            ],
        },
        "forbidden_patterns": [
            r"heilt?\s+schilddrüse",
            r"cures?\s+thyroid",
        ],
    },
    # --- Superfoods / Algae ---
    "spirulina": {
        "approved_claims": {
            "de": [
                "Quelle von Protein (60% Proteingehalt)",
                "enthält natürliches Eisen und B-Vitamine",
                "reich an Phycocyanin (natürlicher Farbstoff)",
            ],
            "en": [
                "source of protein (60% protein content)",
                "contains natural iron and B-vitamins",
                "rich in phycocyanin (natural pigment)",
            ],
        },
        "forbidden_patterns": [
            r"detox",
            r"entgift",
            r"immune\s*boost",
            r"stärkt?\s+(?:das\s+)?immunsystem",
            r"anti[\s-]?(?:cancer|krebs)",
            r"heilt?",
            r"cures?",
            r"gewichtsverlust",
            r"weight\s*loss",
            r"abnehmen",
        ],
    },
    "chlorella": {
        "approved_claims": {
            "de": [
                "Quelle von Vitamin B12 und Eisen",
                "enthält natürliches Chlorophyll",
                "reich an pflanzlichem Protein",
            ],
            "en": [
                "source of vitamin B12 and iron",
                "contains natural chlorophyll",
                "rich in plant protein",
            ],
        },
        "forbidden_patterns": [
            r"detox",
            r"entgift",
            r"heavy\s*metal",
            r"schwermetall",
            r"bindet?\s+(?:gifte?|toxine?)",
        ],
    },
    # --- Omega / Fatty Acids ---
    "omega 3": {
        "aliases": ["omega-3", "dha", "epa", "fischöl", "fish oil"],
        "approved_claims": {
            "de": [
                "DHA trägt zur Erhaltung einer normalen Gehirnfunktion bei",
                "DHA trägt zur Erhaltung normaler Sehkraft bei",
                "EPA und DHA tragen zu einer normalen Herzfunktion bei",
            ],
            "en": [
                "DHA contributes to the maintenance of normal brain function",
                "DHA contributes to the maintenance of normal vision",
                "EPA and DHA contribute to the normal function of the heart",
            ],
        },
        "forbidden_patterns": [
            r"prevents?\s+(?:heart|alzheimer)",
            r"verhindert?\s+(?:herz|alzheimer)",
            r"heilt?\s+(?:herz|gehirn)",
            r"cures?\s+(?:heart|brain)",
        ],
    },
    # --- Amino Acids ---
    "l-arginin": {
        "aliases": ["l-arginine", "arginin", "arginine"],
        "approved_claims": {
            "de": [
                "Aminosäure, die am Harnstoffzyklus beteiligt ist",
            ],
            "en": [
                "amino acid involved in the urea cycle",
            ],
        },
        "forbidden_patterns": [
            r"(?:erektions|potenz)",
            r"(?:erectile|potency)",
            r"boost(?:s|ing)?\s+(?:testosterone|libido)",
        ],
    },
    # --- Probiotics ---
    "probiotika": {
        "aliases": ["probiotics", "lactobacillus", "bifidobacterium"],
        "approved_claims": {
            "de": [
                "Lebende Bakterienkulturen (keine zugelassenen Health Claims)",
            ],
            "en": [
                "Live bacterial cultures (no approved health claims)",
            ],
        },
        "forbidden_patterns": [
            r"heilt?\s+darm",
            r"cures?\s+(?:gut|digest)",
            r"boost(?:s|ing)?\s+immun",
            r"stärkt?\s+(?:das\s+)?immunsystem",
        ],
    },
    # --- Plant Extracts ---
    "kurkuma": {
        "aliases": ["turmeric", "curcumin", "curcuma"],
        "approved_claims": {
            "de": [
                "Keine zugelassenen EFSA Health Claims für Kurkuma",
            ],
            "en": [
                "No approved EFSA health claims for turmeric",
            ],
        },
        "forbidden_patterns": [
            r"anti[\s-]?inflam",
            r"entzündungshemmend",
            r"heilt?\s+(?:gelenk|arthritis)",
            r"cures?\s+(?:joint|arthritis|pain)",
        ],
    },
    "ashwagandha": {
        "aliases": ["withania somnifera"],
        "approved_claims": {
            "de": [
                "Keine zugelassenen EFSA Health Claims für Ashwagandha",
            ],
            "en": [
                "No approved EFSA health claims for ashwagandha",
            ],
        },
        "forbidden_patterns": [
            r"(?:anti[\s-]?stress|stressabbau)",
            r"(?:reduces?|lowers?)\s+(?:cortisol|stress)",
            r"(?:senkt?|reduziert?)\s+(?:cortisol|stress)",
            r"boost(?:s|ing)?\s+testosterone",
        ],
    },
    "ginkgo": {
        "aliases": ["ginkgo biloba"],
        "approved_claims": {
            "de": [
                "Keine zugelassenen EFSA Health Claims für Ginkgo",
            ],
            "en": [
                "No approved EFSA health claims for ginkgo",
            ],
        },
        "forbidden_patterns": [
            r"(?:verbessert?|steigert?)\s+(?:gedächtnis|konzentration)",
            r"(?:improves?|boosts?)\s+(?:memory|concentration|brain)",
            r"anti[\s-]?(?:demenz|alzheimer|dementia)",
        ],
    },
    # --- Fiber / Digestive ---
    "ballaststoffe": {
        "aliases": ["fiber", "fibre", "psyllium", "flohsamen", "inulin"],
        "approved_claims": {
            "de": [
                "trägt zu einer normalen Darmfunktion bei (Flohsamen)",
                "trägt zur Aufrechterhaltung eines normalen Cholesterinspiegels bei (Beta-Glucan)",
            ],
            "en": [
                "contributes to normal bowel function (psyllium)",
                "contributes to the maintenance of normal blood cholesterol levels (beta-glucan)",
            ],
        },
        "forbidden_patterns": [
            r"(?:reinigt?|cleanse)",
            r"detox",
            r"(?:senkt?|reduziert?)\s+cholesterin\s+(?:drastisch|sofort)",
        ],
    },
    # --- Collagen ---
    "kollagen": {
        "aliases": ["collagen"],
        "approved_claims": {
            "de": [
                "Vitamin C trägt zu einer normalen Kollagenbildung bei (nur mit Vitamin C)",
            ],
            "en": [
                "Vitamin C contributes to normal collagen formation (only with Vitamin C)",
            ],
        },
        "forbidden_patterns": [
            r"anti[\s-]?aging",
            r"(?:verjüng|rejuvenat)",
            r"(?:falten|wrinkle)",
        ],
    },
    # --- Common Additions ---
    "biotin": {
        "aliases": ["vitamin b7", "vitamin h"],
        "approved_claims": {
            "de": [
                "trägt zur Erhaltung normaler Haare bei",
                "trägt zur Erhaltung normaler Haut bei",
                "trägt zu einem normalen Energiestoffwechsel bei",
            ],
            "en": [
                "contributes to the maintenance of normal hair",
                "contributes to the maintenance of normal skin",
                "contributes to normal energy-yielding metabolism",
            ],
        },
        "forbidden_patterns": [
            r"(?:haarwachstum|hair\s*growth)",
            r"(?:stops?|prevents?)\s+hair\s*loss",
            r"(?:stoppt?|verhindert?)\s+haarausfall",
        ],
    },
    "folsäure": {
        "aliases": ["folic acid", "folate", "vitamin b9"],
        "approved_claims": {
            "de": [
                "trägt zum Wachstum des mütterlichen Gewebes während der Schwangerschaft bei",
                "trägt zur normalen Blutbildung bei",
                "trägt zu einer normalen Funktion des Immunsystems bei",
            ],
            "en": [
                "contributes to maternal tissue growth during pregnancy",
                "contributes to normal blood formation",
                "contributes to the normal function of the immune system",
            ],
        },
        "forbidden_patterns": [
            r"prevents?\s+(?:birth\s*defects?|miscarriage)",
            r"verhindert?\s+(?:fehlgeburt|missbildung)",
        ],
    },
    "coenzym q10": {
        "aliases": ["coq10", "ubiquinol", "ubiquinone"],
        "approved_claims": {
            "de": [
                "Keine zugelassenen EFSA Health Claims für Coenzym Q10",
            ],
            "en": [
                "No approved EFSA health claims for Coenzyme Q10",
            ],
        },
        "forbidden_patterns": [
            r"anti[\s-]?aging",
            r"(?:verjüng|rejuvenat)",
            r"(?:steigert?|boosts?)\s+energie",
            r"(?:heart|herz)\s*(?:health|gesund)",
        ],
    },
    "protein": {
        "aliases": ["eiweiß", "whey", "casein"],
        "approved_claims": {
            "de": [
                "Proteine tragen zu einer Zunahme an Muskelmasse bei",
                "Proteine tragen zur Erhaltung von Muskelmasse bei",
                "Proteine tragen zur Erhaltung normaler Knochen bei",
            ],
            "en": [
                "protein contributes to a growth in muscle mass",
                "protein contributes to the maintenance of muscle mass",
                "protein contributes to the maintenance of normal bones",
            ],
        },
        "forbidden_patterns": [
            r"(?:garantiert?|guaranteed?)\s+(?:muskelaufbau|muscle\s*(?:gain|growth))",
            r"(?:steroid|anaboli)",
        ],
    },
}


def lookup_ingredients(
    ingredients: List[str],
    current_bullets: List[str],
) -> List[Dict[str, Any]]:
    """Map ingredients to EFSA-approved claims and check bullets for violations.

    WHY: Pure database lookup, zero LLM cost, instant response.
    Returns per-ingredient: approved claims + forbidden matches in current listing.
    """
    bullets_text = " ".join(current_bullets).lower()
    results = []

    for ingredient_raw in ingredients:
        ingredient = ingredient_raw.strip().lower()
        entry = _find_entry(ingredient)

        if not entry:
            results.append({
                "name": ingredient_raw.strip(),
                "found": False,
                "approved_claims": {"de": [], "en": []},
                "forbidden_in_listing": [],
                "suggestion": f"No EFSA data for '{ingredient_raw.strip()}' — check EU Register manually",
            })
            continue

        # Check current bullets for forbidden patterns
        forbidden_found = []
        for pattern in entry.get("forbidden_patterns", []):
            matches = re.findall(pattern, bullets_text, re.IGNORECASE)
            if matches:
                forbidden_found.append({
                    "pattern": pattern,
                    "matched_text": matches[0],
                })

        suggestion = ""
        if forbidden_found:
            # Suggest first approved DE claim as replacement
            de_claims = entry["approved_claims"].get("de", [])
            if de_claims:
                suggestion = f"Ersetze durch: \"{de_claims[0]}\""
            else:
                suggestion = "Remove forbidden claim — no EFSA-approved alternative available"
        else:
            suggestion = "OK — no forbidden claims detected in current listing"

        results.append({
            "name": ingredient_raw.strip(),
            "found": True,
            "approved_claims": entry["approved_claims"],
            "forbidden_in_listing": forbidden_found,
            "suggestion": suggestion,
        })

    return results


def _find_entry(ingredient: str) -> Optional[Dict[str, Any]]:
    """Find EFSA entry by name or alias."""
    # Direct match
    if ingredient in EFSA_CLAIMS_DB:
        return EFSA_CLAIMS_DB[ingredient]

    # Search aliases
    for key, entry in EFSA_CLAIMS_DB.items():
        aliases = entry.get("aliases", [])
        if ingredient in [a.lower() for a in aliases]:
            return entry
        # Partial match — ingredient contains the key or vice versa
        if key in ingredient or ingredient in key:
            return entry
        for alias in aliases:
            if alias.lower() in ingredient or ingredient in alias.lower():
                return entry

    return None


def auto_detect_ingredients(title: str, bullets: List[str]) -> List[str]:
    """Auto-detect supplement ingredients from title and bullets.

    WHY: Demo should auto-populate ingredients without user input.
    Scans text for known EFSA ingredients.
    """
    text = f"{title} {' '.join(bullets)}".lower()
    found = []

    for key, entry in EFSA_CLAIMS_DB.items():
        names_to_check = [key] + [a.lower() for a in entry.get("aliases", [])]
        for name in names_to_check:
            # WHY: Word boundary check — avoid matching "protein" inside "lipoprotein"
            if re.search(r'\b' + re.escape(name) + r'\b', text):
                # Use the DB key as canonical name
                if key not in found:
                    found.append(key)
                break

    return found
