# backend/data/demo_samples.py
# Purpose: Realistic sample data for Amazon Pro Demo (BIO Spirulina DE)
# NOT for: Production catalog data or real SP-API responses

from typing import Dict, List, Any


def _rj(keyword: str, sv: int, rel: float, comp: float) -> Dict[str, Any]:
    """Calculate DataDive Ranking Juice for a keyword.

    Formula: RJ = SV × (0.5 + 0.5×Rel) × (0.5 + 0.5×(1-Comp)) × LengthBoost
    """
    word_count = len(keyword.split())
    length_boost = 1.1 if 2 <= word_count <= 3 else (1.05 if word_count > 3 else 1.0)

    rel_factor = 0.5 + 0.5 * rel
    comp_factor = 0.5 + 0.5 * (1.0 - comp)
    rj = sv * rel_factor * comp_factor * length_boost

    return {
        "keyword": keyword,
        "search_volume": sv,
        "relevance": rel,
        "competition": comp,
        "ranking_juice": round(rj, 0),
        "priority": "HIGH" if rj > 5000 else ("MEDIUM" if rj > 1000 else "LOW"),
    }


# WHY: 20 realistic keywords for BIO Spirulina supplement on Amazon DE
# Source: DataDive methodology — keywords sorted by Ranking Juice (desc)
DEMO_KEYWORDS: List[Dict[str, Any]] = [
    _rj("bio spirulina tabletten", 12000, 0.98, 0.35),
    _rj("spirulina pulver bio", 9500, 0.95, 0.40),
    _rj("spirulina kapseln", 8200, 0.90, 0.45),
    _rj("spirulina bio", 7800, 0.97, 0.50),
    _rj("spirulina tabletten", 6500, 0.92, 0.42),
    _rj("bio spirulina pulver", 5800, 0.96, 0.38),
    _rj("spirulina nahrungsergänzung", 4200, 0.88, 0.30),
    _rj("chlorella spirulina", 3800, 0.82, 0.35),
    _rj("spirulina eisen", 3200, 0.85, 0.28),
    _rj("blaualgen tabletten", 2800, 0.78, 0.25),
    _rj("spirulina protein", 2500, 0.80, 0.32),
    _rj("spirulina vegan", 2200, 0.88, 0.30),
    _rj("superfood tabletten bio", 1900, 0.72, 0.40),
    _rj("spirulina detox", 1700, 0.70, 0.35),
    _rj("algen supplement", 1500, 0.75, 0.28),
    _rj("spirulina immunsystem", 1200, 0.82, 0.25),
    _rj("bio algen kapseln", 1000, 0.74, 0.30),
    _rj("spirulina b12", 950, 0.80, 0.22),
    _rj("spirulina abnehmen", 850, 0.65, 0.40),
    _rj("mikroalgen nahrungsergänzung", 700, 0.70, 0.20),
]


DEMO_PRODUCT: Dict[str, Any] = {
    "asin": "B09EXAMPLE1",
    "marketplace": "DE",
    "title": "BIO Spirulina Tabletten 500mg - 600 Presslinge - Hochdosiert - Vegan",
    "brand": "NaturPlus",
    "manufacturer": "NaturPlus GmbH, Musterstr. 12, 10115 Berlin, DE",
    "bullets": [
        "BIO-QUALITÄT: 100% reine Bio-Spirulina aus kontrolliertem Anbau, DE-ÖKO-001 zertifiziert",
        "HOCHDOSIERT: 500mg pro Tablette, 600 Presslinge für 4 Monate Vorrat",
        "NÄHRSTOFFREICH: Natürliche Quelle von Eisen, Protein und Vitamin B12",
        "VEGAN & REIN: Ohne Zusatzstoffe, ohne Füllstoffe, ohne Magnesiumstearat",
        "MADE IN GERMANY: Hergestellt und laborgeprüft in Deutschland",
    ],
    "description": (
        "NaturPlus BIO Spirulina Tabletten — Ihr täglicher Begleiter für natürliche "
        "Nährstoffversorgung. Unsere hochdosierten 500mg Presslinge enthalten reine "
        "Bio-Spirulina (Arthrospira platensis) aus kontrolliert biologischem Anbau. "
        "Reich an pflanzlichem Protein (60%), Eisen und B-Vitaminen. "
        "600 Tabletten = 4 Monate Vorrat bei 5 Tabletten pro Tag."
    ),
    "images": [
        "https://images-eu.example.com/spirulina-main.jpg",
        "https://images-eu.example.com/spirulina-label.jpg",
        "https://images-eu.example.com/spirulina-tablets.jpg",
    ],
    "category": "Health & Household",
    "price": "19.99",
    "currency": "EUR",
    "error": None,
}


def get_demo_product() -> Dict[str, Any]:
    """Return demo product with pre-calculated DataDive keyword data."""
    return {**DEMO_PRODUCT, "keywords": DEMO_KEYWORDS}
