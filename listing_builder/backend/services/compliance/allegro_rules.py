# backend/services/compliance/allegro_rules.py
# Purpose: Allegro-specific parameter validation rules for live product card audit
# NOT for: Template file validation (that's rules.py) or scraping logic

from typing import List, Dict, Optional
import re
import structlog

logger = structlog.get_logger()


# ── Parameter name mappings (Polish → canonical) ─────────────────────────────
# WHY: Allegro uses Polish parameter names, sometimes with slight variations
# across categories. We normalize to canonical keys for rule evaluation.

_PARAM_ALIASES = {
    # Battery
    "rodzaj baterii": "battery_type",
    "typ baterii": "battery_type",
    "technologia baterii": "battery_type",
    "baterie w zestawie": "batteries_included",
    "baterie/akumulatory": "batteries_included",
    "czy baterie są potrzebne": "batteries_required",
    "liczba baterii": "battery_count",
    "pojemność baterii": "battery_capacity",
    "zawartość litu": "lithium_content",
    "waga baterii litowej": "lithium_battery_weight",
    # Weight/dimensions
    "waga produktu": "weight",
    "waga (z opakowaniem)": "weight_packaged",
    "waga": "weight",
    "masa": "weight",
    # Safety/CE
    "znak ce": "ce_marking",
    "oznaczenie ce": "ce_marking",
    "certyfikat": "certificate",
    "certyfikaty": "certificate",
    "norma bezpieczeństwa": "safety_standard",
    "klasa bezpieczeństwa": "safety_class",
    # GPSR
    "producent": "manufacturer",
    "marka": "brand",
    "kraj pochodzenia": "country_of_origin",
    "kod producenta": "manufacturer_code",
    "model": "model",
    # Age/restriction
    "wiek dziecka": "child_age",
    "zalecany wiek": "recommended_age",
    "grupa wiekowa": "age_group",
    "ostrzeżenie": "warning_label",
    # Product identity
    "ean (gtin)": "ean",
    "ean": "ean",
    "gtin": "ean",
    "kod ean": "ean",
    "stan": "condition",
    # Material/composition
    "materiał": "material",
    "skład": "composition",
    "tworzywo": "material",
    # Energy
    "klasa energetyczna": "energy_class",
    "klasa efektywności energetycznej": "energy_class",
    "moc": "power",
    "napięcie": "voltage",
}


def normalize_parameters(raw_params: Dict[str, str]) -> Dict[str, str]:
    """Map Allegro Polish parameter names to canonical keys."""
    normalized = {}
    for key, value in raw_params.items():
        canonical = _PARAM_ALIASES.get(key.lower().strip(), None)
        if canonical:
            normalized[canonical] = value.strip()
        # WHY: Keep original too — some rules check raw param names
        normalized[f"raw:{key.lower().strip()}"] = value.strip()
    return normalized


# ── Category detection from product data ─────────────────────────────────────

_ELECTRONICS_KEYWORDS = {
    "elektronika", "komputer", "laptop", "telefon", "tablet", "smartfon",
    "monitor", "telewizor", "głośnik", "słuchawki", "kamera", "aparat",
    "ładowarka", "zasilacz", "powerbank", "kabel", "adapter", "usb",
    "bluetooth", "wifi", "router", "switch", "dysk", "ssd", "ram",
}

_TOY_KEYWORDS = {
    "zabawka", "zabawki", "klocki", "lalka", "gra planszowa", "puzzle",
    "pluszak", "figurka", "dla dzieci", "dziecięcy",
}

_COSMETICS_KEYWORDS = {
    "kosmetyk", "krem", "szampon", "balsam", "perfum", "dezodorant",
    "makijaż", "pielęgnacja",
}


def _detect_category_flags(title: str, category: str, params: Dict[str, str]) -> Dict[str, bool]:
    """Detect product category flags from title, category path, and parameters."""
    text = f"{title} {category}".lower()
    param_text = " ".join(params.values()).lower()
    all_text = f"{text} {param_text}"

    return {
        "is_electronics": any(kw in all_text for kw in _ELECTRONICS_KEYWORDS),
        "is_toy": any(kw in all_text for kw in _TOY_KEYWORDS),
        "is_cosmetics": any(kw in all_text for kw in _COSMETICS_KEYWORDS),
        "has_battery_params": any(
            k in params for k in ("battery_type", "batteries_included", "batteries_required")
        ),
    }


# ── Validation rules ─────────────────────────────────────────────────────────

def validate_allegro_parameters(
    raw_params: Dict[str, str],
    title: str = "",
    category: str = "",
) -> List[Dict]:
    """
    Run Allegro-specific parameter validation.

    Returns list of issue dicts: [{field, severity, message}, ...]
    """
    params = normalize_parameters(raw_params)
    flags = _detect_category_flags(title, category, params)
    issues = []

    # ── Battery rules ──
    if flags["has_battery_params"] or _title_suggests_battery(title):
        if not params.get("battery_type"):
            issues.append({
                "field": "battery_type",
                "severity": "error",
                "message": "Produkt wygląda na zawierający baterie — brak parametru 'Rodzaj baterii'",
            })

        if params.get("battery_type") and not params.get("battery_count"):
            issues.append({
                "field": "battery_count",
                "severity": "warning",
                "message": "Brak liczby baterii — wymagana przy deklaracji typu baterii",
            })

        # WHY: Lithium batteries have special EU shipping/labeling requirements
        battery_type = params.get("battery_type", "").lower()
        if "lit" in battery_type or "lithium" in battery_type or "li-" in battery_type:
            if not params.get("lithium_content") and not params.get("lithium_battery_weight"):
                issues.append({
                    "field": "lithium_content",
                    "severity": "error",
                    "message": "Bateria litowa wykryta — brak deklaracji zawartości litu (wymagane UE)",
                })

    # ── CE marking (electronics & toys) ──
    if flags["is_electronics"] or flags["is_toy"]:
        if not params.get("ce_marking"):
            issues.append({
                "field": "ce_marking",
                "severity": "error" if flags["is_toy"] else "warning",
                "message": "Brak oznaczenia CE — wymagane dla elektroniki/zabawek w UE",
            })

    # ── GPSR (General Product Safety Regulation) ──
    if not params.get("manufacturer"):
        issues.append({
            "field": "manufacturer",
            "severity": "error",
            "message": "Brak producenta — wymagany przez GPSR (od 13.12.2024)",
        })

    if not params.get("country_of_origin"):
        issues.append({
            "field": "country_of_origin",
            "severity": "warning",
            "message": "Brak kraju pochodzenia — zalecany dla GPSR compliance",
        })

    # ── Weight (required for EPR/shipping) ──
    if not params.get("weight"):
        severity = "warning"
        # WHY: Electronics need weight for WEEE/EPR calculations
        if flags["is_electronics"]:
            severity = "error"
        issues.append({
            "field": "weight",
            "severity": severity,
            "message": "Brak wagi produktu — wymagana dla EPR i kalkulacji wysyłki",
        })

    # ── EAN validation ──
    ean = params.get("ean", "")
    if ean and not _is_valid_ean(ean):
        issues.append({
            "field": "ean",
            "severity": "error",
            "message": f"Nieprawidłowy EAN '{ean}' — musi mieć 8 lub 13 cyfr z poprawną sumą kontrolną",
        })

    # ── Toy-specific rules ──
    if flags["is_toy"]:
        if not params.get("recommended_age") and not params.get("child_age") and not params.get("age_group"):
            issues.append({
                "field": "recommended_age",
                "severity": "warning",
                "message": "Zabawka bez zalecanego wieku — wymagane przez dyrektywę zabawkową UE",
            })

        if not params.get("warning_label"):
            issues.append({
                "field": "warning_label",
                "severity": "warning",
                "message": "Zabawka bez ostrzeżenia — sprawdź wymóg etykiety 'Nie dla dzieci poniżej 3 lat'",
            })

    # ── Cosmetics-specific ──
    if flags["is_cosmetics"]:
        if not params.get("composition") and not params.get("material"):
            issues.append({
                "field": "composition",
                "severity": "warning",
                "message": "Kosmetyk bez deklaracji składu — wymagane przez UE (INCI list)",
            })

    # ── Energy class (electronics) ──
    if flags["is_electronics"]:
        energy = params.get("energy_class", "").upper()
        if energy and energy not in ("A", "B", "C", "D", "E", "F", "G", "A+", "A++", "A+++"):
            issues.append({
                "field": "energy_class",
                "severity": "warning",
                "message": f"Klasa energetyczna '{energy}' nie jest standardowa (A-G wg skali UE 2021)",
            })

    # ── Power/voltage (electronics) ──
    if flags["is_electronics"] and params.get("voltage"):
        voltage = params.get("voltage", "")
        # WHY: Products > 50V need additional safety declarations
        voltage_num = _extract_number(voltage)
        if voltage_num and voltage_num > 50:
            if not params.get("safety_standard") and not params.get("safety_class"):
                issues.append({
                    "field": "safety_standard",
                    "severity": "warning",
                    "message": f"Napięcie {voltage} > 50V — zalecana deklaracja normy bezpieczeństwa",
                })

    return issues


def _title_suggests_battery(title: str) -> bool:
    """Check if product title suggests it contains batteries."""
    battery_hints = {
        "akumulator", "bateria", "powerbank", "power bank",
        "ładowark", "bezprzewodow", "wireless", "rechargeable",
        "li-ion", "lithium", "litow",
    }
    title_lower = title.lower()
    return any(hint in title_lower for hint in battery_hints)


def _is_valid_ean(ean: str) -> bool:
    """Validate EAN-8 or EAN-13 checksum."""
    digits = re.sub(r'\D', '', ean)
    if len(digits) not in (8, 13):
        return False

    # WHY: Standard EAN checksum algorithm
    total = 0
    for i, d in enumerate(digits[:-1]):
        weight = 1 if (len(digits) == 13 and i % 2 == 0) or (len(digits) == 8 and i % 2 == 0) else 3
        total += int(d) * weight

    check = (10 - (total % 10)) % 10
    return check == int(digits[-1])


def _extract_number(text: str) -> Optional[float]:
    """Extract first number from text like '230V' or '12.5 W'."""
    match = re.search(r'(\d+(?:[.,]\d+)?)', text)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None
