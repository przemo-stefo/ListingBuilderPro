# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/converter/__init__.py
# Purpose: Export converter field mappings for use by conversion service
# NOT for: Conversion logic implementation

from .field_mapping import (
    AMAZON_MAPPING,
    EBAY_MAPPING,
    KAUFLAND_MAPPING,
    ONE_TO_MANY_MAPPINGS,
    FIELDS_WITHOUT_ALLEGRO_SOURCE,
    FIELDS_NEEDING_TRANSLATION,
    COLOR_PL_TO_DE,
    MATERIAL_PL_TO_DE,
    CONDITION_ALLEGRO_TO_EBAY,
    GENDER_ALLEGRO_TO_MARKETPLACE,
    MAPPING_SUMMARY,
)

__all__ = [
    "AMAZON_MAPPING",
    "EBAY_MAPPING",
    "KAUFLAND_MAPPING",
    "ONE_TO_MANY_MAPPINGS",
    "FIELDS_WITHOUT_ALLEGRO_SOURCE",
    "FIELDS_NEEDING_TRANSLATION",
    "COLOR_PL_TO_DE",
    "MATERIAL_PL_TO_DE",
    "CONDITION_ALLEGRO_TO_EBAY",
    "GENDER_ALLEGRO_TO_MARKETPLACE",
    "MAPPING_SUMMARY",
]
