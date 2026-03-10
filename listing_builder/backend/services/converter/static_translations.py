# backend/services/converter/static_translations.py
# Purpose: Zero-cost static translation lookups (PL→DE) and HTML utilities
# NOT for: AI-powered translation (ai_translator.py) or field mapping (field_mapping.py)

import re
from typing import Optional
from html.parser import HTMLParser

from services.converter.field_mapping import (
    COLOR_PL_TO_DE,
    MATERIAL_PL_TO_DE,
    GENDER_ALLEGRO_TO_MARKETPLACE,
    CONDITION_ALLEGRO_TO_EBAY,
)


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags, keep text content."""

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return " ".join(self.text_parts).strip()


def strip_html(html: str) -> str:
    """Remove HTML tags, return plain text."""
    if not html:
        return ""
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()
    return re.sub(r'\s+', ' ', text).strip()


def translate_color(color_pl: str) -> Optional[str]:
    """Translate Polish color to German using lookup table.
    Returns None if not found (caller should use AI fallback).
    """
    if not color_pl:
        return None
    return COLOR_PL_TO_DE.get(color_pl.lower().strip())


def translate_material(material_pl: str) -> Optional[str]:
    """Translate Polish material to German using lookup table."""
    if not material_pl:
        return None
    return MATERIAL_PL_TO_DE.get(material_pl.lower().strip())


def translate_gender(gender_pl: str, marketplace: str) -> Optional[str]:
    """Translate Polish gender to marketplace-specific value."""
    if not gender_pl:
        return None
    mapping = GENDER_ALLEGRO_TO_MARKETPLACE.get(gender_pl)
    if mapping:
        return mapping.get(marketplace)
    return None


def translate_condition(condition_pl: str) -> Optional[int]:
    """Translate Allegro condition to eBay Condition ID."""
    if not condition_pl:
        return None
    return CONDITION_ALLEGRO_TO_EBAY.get(condition_pl)
