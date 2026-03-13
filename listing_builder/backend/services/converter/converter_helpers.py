# backend/services/converter/converter_helpers.py
# Purpose: Shared data types and value parsers used by all marketplace converters
# NOT for: Business logic, AI calls, or marketplace-specific field mapping

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from services.scraper.allegro_scraper import AllegroProduct


@dataclass
class ConvertedProduct:
    """Product data mapped and translated for a specific marketplace."""

    source_url: str = ""
    source_id: str = ""
    marketplace: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ── Value parsers ─────────────────────────────────────────────────────────

def parse_weight(weight_str: str) -> str:
    """Parse Allegro weight format ('0,500 kg', '500 g') to decimal kg."""
    if not weight_str:
        return ""
    weight_str = weight_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(kg|g)', weight_str)
    if not match:
        return weight_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "g":
        value = value / 1000
    return f"{value:.3f}"


def parse_dimension_mm(dim_str: str) -> str:
    """Parse Allegro dimension to millimeters (Kaufland format)."""
    if not dim_str:
        return ""
    dim_str = dim_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(mm|cm|m)', dim_str)
    if not match:
        return dim_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "cm":
        value = value * 10
    elif unit == "m":
        value = value * 1000
    return f"{value:.0f}"


def parse_dimension_cm(dim_str: str) -> str:
    """Parse Allegro dimension to centimeters (Amazon format)."""
    if not dim_str:
        return ""
    dim_str = dim_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(mm|cm|m)', dim_str)
    if not match:
        return dim_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "mm":
        value = value / 10
    elif unit == "m":
        value = value * 100
    return f"{value:.1f}"


def convert_pln_to_eur(pln_price: str, rate: float = 0.23) -> str:
    """Convert PLN price to EUR. Default rate ~0.23 (1 PLN ≈ 0.23 EUR)."""
    try:
        value = float(pln_price.replace(",", ".").strip())
        eur = value * rate
        return f"{eur:.2f}"
    except (ValueError, AttributeError):
        return pln_price


def get_param(product: AllegroProduct, *keys: str) -> str:
    """Get parameter value by trying multiple Polish key variants."""
    for key in keys:
        if key in product.parameters:
            return product.parameters[key]
        for pk, pv in product.parameters.items():
            if key.lower() in pk.lower():
                return pv
    return ""
