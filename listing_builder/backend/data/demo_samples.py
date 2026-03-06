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
    "asin": "B09EXAMPL1",
    "marketplace": "DE",
    # WHY realistic TOS issues: Title too short for optimal indexing, but no violations.
    # Bullets contain real violations that Amazon's 2025 scanner WOULD catch.
    "title": "BIO Spirulina Tabletten 500mg - 600 Presslinge - Hochdosiert - Premium Qualität - Vegan",
    "brand": "NaturPlus",
    "manufacturer": "NaturPlus GmbH, Musterstr. 12, 10115 Berlin, DE",
    "bullets": [
        "BIO-QUALITÄT: 100% reine Bio-Spirulina aus kontrolliertem Anbau, DE-ÖKO-001 zertifiziert, premium quality guaranteed",
        "HOCHDOSIERT: 500mg pro Tablette, 600 Presslinge für 4 Monate Vorrat, best price",
        "IMMUNE BOOSTER: Natürliche Quelle von Eisen, Protein und Vitamin B12 für Ihr Immunsystem",
        "DETOX & VEGAN: Spirulina detox Wirkung, ohne Zusatzstoffe, ohne Magnesiumstearat",
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


# WHY: Competitor listing with INTENTIONAL TOS + EU compliance violations.
# Used in Competitor Compliance Radar demo — shows what Amazon would flag.
DEMO_COMPETITOR: Dict[str, Any] = {
    "asin": "B09COMPET1",
    "marketplace": "DE",
    "title": "Spirulina Tabletten 500mg - DETOX & IMMUNE BOOSTER - Natürliche Entgiftung - Gewichtsverlust - 300 Stück!!!",
    "brand": "VitaBoost24",
    "manufacturer": "",  # WHY: Missing = GPSR FAIL
    "bullets": [
        "IMMUNE BOOSTER: Stärkt das Immunsystem und beugt Krankheiten vor — best price guaranteed!!!",
        "DETOX WIRKUNG: Entgiftet den Körper von Schwermetallen und Toxinen, natürliche Reinigung",
        "GEWICHTSVERLUST: Spirulina hilft beim Abnehmen, garantierter Gewichtsverlust in 30 Tagen",
        "HEILT MÜDIGKEIT: Spirulina heilt chronische Müdigkeit und steigert die Energie um 300%",
        "ANTI-AGING: Verjüngt die Haut, stoppt Haarausfall, cures all skin problems",
    ],
    "description": (
        "VitaBoost24 Spirulina — das BESTE Supplement auf dem Markt! "
        "Unser Produkt HEILT Müdigkeit, STÄRKT das Immunsystem und ENTGIFTET Ihren Körper. "
        "Klinisch getestete Formel für garantierten Gewichtsverlust. "
        "Kontaktieren Sie uns: info@vitaboost24.de oder +49 123 456789. "
        "Besuchen Sie www.vitaboost24.de für mehr Angebote!"
    ),
    "images": [],
    "category": "Health & Household",
    "price": "14.99",
    "currency": "EUR",
}


def get_demo_competitor() -> Dict[str, Any]:
    """Return competitor listing with intentional violations for demo scanning."""
    return DEMO_COMPETITOR


# WHY: Sample competitors for Competitor-Inspired Generator demo mode.
# Realistic Spirulina supplement listings from Amazon DE.
DEMO_INSPIRE_COMPETITORS: List[Dict[str, Any]] = [
    {
        "asin": "B0DBZF2DK4",
        "title": "Spirulina Bio Tabletten 500mg - 600 Stück (10 Monate) - Spirulina Presslinge Hochdosiert mit Phycocyanin",
        "bullets": [
            "BIO SPIRULINA TABLETTEN - 600 Tabletten reines Bio Spirulina für volle 10 Monate Versorgung",
            "HOCHDOSIERT - Jede Tablette enthält 500mg Bio Spirulina platensis Pulver",
            "REICH AN PHYCOCYANIN - Natürliches blaues Pigment mit hoher Bioverfügbarkeit",
            "BIO ZERTIFIZIERT - DE-ÖKO-006 kontrolliert, ohne Zusatzstoffe, vegan, glutenfrei",
            "LABORGEPRÜFT - Auf Schwermetalle, Pestizide und Mikrobiologie in Deutschland getestet",
        ],
        "description": "Premium Bio Spirulina in Tablettenform. 600 Tabletten für eine 10-monatige Versorgung.",
    },
    {
        "asin": "B0CTZ2FSVK",
        "title": "Spirulina Pulver Bio 500g - Rohkostqualität - Spirulina Platensis - Vegan Superfood",
        "bullets": [
            "BIO SPIRULINA PULVER - 500g feinstes Spirulina platensis in Rohkostqualität",
            "NÄHRSTOFFREICH - Natürliche Quelle von Eisen, Vitamin B12, Protein und Chlorophyll",
            "VIELSEITIG - Perfekt für Smoothies, Bowls, Säfte und als Nahrungsergänzung",
            "OHNE ZUSÄTZE - 100% reines Bio Spirulina, keine Füllstoffe, vegan und glutenfrei",
            "NACHHALTIG ANGEBAUT - Aus kontrolliert biologischem Anbau, schonend getrocknet",
        ],
        "description": "Reines Bio Spirulina Pulver aus kontrolliert biologischem Anbau für den täglichen Nährstoff-Boost.",
    },
    {
        "asin": "B01M30G72K",
        "title": "Sevenhills Wholefoods Spirulina Pulver Bio 500g - Soil Association zertifiziert",
        "bullets": [
            "BIOLOGISCH ZERTIFIZIERT - Von der Soil Association als biologisch zertifiziert",
            "HOHER PROTEINGEHALT - Bis zu 65% pflanzliches Protein pro Portion",
            "100% REIN - Ohne Zusatzstoffe, Konservierungsmittel oder Füllstoffe",
            "REICH AN EISEN - Natürliche Eisenquelle für die tägliche Versorgung",
            "WIEDERVERSCHLIESSBAR - Frischhaltebeutel für optimale Lagerung",
        ],
        "description": "Bio Spirulina Pulver von Sevenhills Wholefoods. Premium Qualität mit Soil Association Zertifizierung.",
    },
]


def get_demo_inspire_competitors() -> List[Dict[str, Any]]:
    """Return sample competitors for Competitor-Inspired Generator demo."""
    return DEMO_INSPIRE_COMPETITORS
