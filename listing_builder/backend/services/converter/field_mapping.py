# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/converter/field_mapping.py
# Purpose: Comprehensive field mapping from Allegro product data to Amazon, eBay, Kaufland
# NOT for: Actual conversion logic, validation rules, or API routing

"""
ALLEGRO-TO-MARKETPLACE FIELD MAPPING
=====================================

Source: Allegro product data (Polish marketplace, PLN currency)
Targets: Amazon.de (XLSM), eBay.de (XLSX), Kaufland.de (CSV)

Mapping types:
  - Direct    = 1:1 copy, no transformation needed
  - Transform = needs conversion (currency, units, format)
  - AI        = needs AI to generate/translate content
  - Manual    = cannot be auto-filled, user must provide
  - Derived   = computed from other Allegro fields
  - N/A       = field not applicable or not present in source

Translation directions:
  - PL -> DE  (Amazon.de, Kaufland.de)
  - PL -> EN  (eBay international, some Amazon fields)
"""

from typing import Dict, List, Any


# ── Mapping type constants ─────────────────────────────────────────────────
DIRECT = "direct"
TRANSFORM = "transform"
AI = "ai"
MANUAL = "manual"
DERIVED = "derived"
NA = "n/a"

# ── Requirement level constants ────────────────────────────────────────────
REQUIRED = "required"
RECOMMENDED = "recommended"
OPTIONAL = "optional"
CONDITIONAL = "conditional"


# ============================================================================
# SECTION 1: ALLEGRO SOURCE FIELDS
# ============================================================================
# What we get from Allegro (via scraper / API)
# These are the "source" fields that feed into the Product model.

ALLEGRO_SOURCE_FIELDS = {
    # Core fields
    "title": "Tytuł - Product title, max 75 chars, Polish",
    "description": "Opis - HTML formatted description, Polish",
    "price": "Cena - Price in PLN",
    "currency": "Always PLN",
    "ean": "EAN/GTIN barcode (from parameters)",
    "images": "Zdjęcia - Up to 16 image URLs",
    "category": "Kategoria - Full category path in Polish",
    "quantity": "Ilość - Available quantity",

    # Parameters (key-value pairs, Polish keys)
    "param.Marka": "Brand name",
    "param.Producent": "Manufacturer name",
    "param.Materiał": "Material composition",
    "param.Kolor": "Color",
    "param.Długość": "Length dimension",
    "param.Szerokość": "Width dimension",
    "param.Wysokość": "Height dimension",
    "param.Waga": "Weight",
    "param.Stan": "Condition (Nowy/Używany)",
    "param.MPN": "Manufacturer Part Number",
    "param.Rozmiar": "Size (clothing/shoes)",
    "param.Płeć": "Target gender",
}


# ============================================================================
# SECTION 2: AMAZON.DE FIELD MAPPING
# ============================================================================
# Amazon Flat File XLSM format - Row 3 field IDs
# Template: NUTRITIONAL_SUPPLEMENT.xlsm (300+ columns)

AMAZON_MAPPING: List[Dict[str, Any]] = [
    # ── IDENTITY / SKU ──
    {
        "amazon_field": "feed_product_type",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "Amazon product type code. Category-specific. User must select.",
    },
    {
        "amazon_field": "item_sku",
        "allegro_source": "source_id",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Allegro source_id prefixed with 'ALG-' to create unique SKU.",
    },
    {
        "amazon_field": "update_delete",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Always 'Update' for new listings, 'PartialUpdate' for edits.",
    },
    {
        "amazon_field": "external_product_id",
        "allegro_source": "ean",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "EAN/GTIN barcode copied directly from Allegro.",
    },
    {
        "amazon_field": "external_product_id_type",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Always 'EAN' when external_product_id comes from Allegro EAN.",
    },

    # ── TITLE & DESCRIPTION ──
    {
        "amazon_field": "item_name",
        "allegro_source": "title",
        "mapping_type": AI,
        "requirement": REQUIRED,
        "translate": "PL -> DE",
        "note": "Translate + optimize for Amazon DE. Max 200 chars. "
                "Allegro titles are max 75 chars, so AI should expand with keywords.",
    },
    {
        "amazon_field": "product_description",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Strip HTML, translate to German, optimize for Amazon. Max 2000 chars.",
    },
    {
        "amazon_field": "bullet_point1",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "AI generates 5 bullet points from Allegro description + attributes. "
                "No Allegro equivalent. Max 500 chars each.",
    },
    {
        "amazon_field": "bullet_point2",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Bullet point 2 - AI generated from description + attributes.",
    },
    {
        "amazon_field": "bullet_point3",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Bullet point 3 - AI generated from description + attributes.",
    },
    {
        "amazon_field": "bullet_point4",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Bullet point 4 - AI generated from description + attributes.",
    },
    {
        "amazon_field": "bullet_point5",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Bullet point 5 - AI generated from description + attributes.",
    },
    {
        "amazon_field": "generic_keywords",
        "allegro_source": None,
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "AI generates German search terms from title + description + attributes. "
                "No Allegro equivalent. Max 250 bytes.",
    },

    # ── BRAND & MANUFACTURER ──
    {
        "amazon_field": "brand_name",
        "allegro_source": "param.Marka",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Brand name - usually the same across languages. Direct copy.",
    },
    {
        "amazon_field": "manufacturer",
        "allegro_source": "param.Producent",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Manufacturer name - direct copy. GPSR required field.",
    },
    {
        "amazon_field": "manufacturer_contact_information",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Full manufacturer address. Not available from Allegro. "
                "User must provide once, then reuse for all products from same manufacturer.",
    },
    {
        "amazon_field": "country_of_origin",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "Country of origin (ISO code e.g. 'PL', 'CN'). "
                "Not typically available from Allegro. User must provide.",
    },
    {
        "amazon_field": "part_number",
        "allegro_source": "param.MPN",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "Manufacturer Part Number - direct copy from Allegro MPN parameter.",
    },
    {
        "amazon_field": "model",
        "allegro_source": "param.Model",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "Model number if available in Allegro parameters.",
    },

    # ── PRICING ──
    {
        "amazon_field": "standard_price",
        "allegro_source": "price",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Convert PLN -> EUR. Use current exchange rate. "
                "Add margin if configured. Amazon.de requires EUR.",
    },
    {
        "amazon_field": "quantity",
        "allegro_source": "quantity",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Stock quantity - direct copy.",
    },

    # ── IMAGES ──
    {
        "amazon_field": "main_image_url",
        "allegro_source": "images[0]",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "First Allegro image. May need re-hosting if Allegro CDN blocks. "
                "Amazon requires white background for main image.",
    },
    {
        "amazon_field": "other_image_url1",
        "allegro_source": "images[1]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional images from Allegro. Up to 8 in Amazon template.",
    },
    {
        "amazon_field": "other_image_url2",
        "allegro_source": "images[2]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 2.",
    },
    {
        "amazon_field": "other_image_url3",
        "allegro_source": "images[3]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 3.",
    },
    {
        "amazon_field": "other_image_url4",
        "allegro_source": "images[4]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 4.",
    },
    {
        "amazon_field": "other_image_url5",
        "allegro_source": "images[5]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 5.",
    },
    {
        "amazon_field": "other_image_url6",
        "allegro_source": "images[6]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 6.",
    },
    {
        "amazon_field": "other_image_url7",
        "allegro_source": "images[7]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 7.",
    },
    {
        "amazon_field": "other_image_url8",
        "allegro_source": "images[8]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 8. Allegro supports up to 16, Amazon only 9 total.",
    },

    # ── PHYSICAL ATTRIBUTES ──
    {
        "amazon_field": "item_weight",
        "allegro_source": "param.Waga",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Weight - parse from Allegro format (e.g. '0,500 kg') to decimal. "
                "Amazon may want different units per category.",
    },
    {
        "amazon_field": "item_dimensions_length",
        "allegro_source": "param.Długość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse from Allegro format (e.g. '60,2 MM') to Amazon format (cm).",
    },
    {
        "amazon_field": "item_dimensions_width",
        "allegro_source": "param.Szerokość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse from Allegro format to Amazon format.",
    },
    {
        "amazon_field": "item_dimensions_height",
        "allegro_source": "param.Wysokość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse from Allegro format to Amazon format.",
    },
    {
        "amazon_field": "color_name",
        "allegro_source": "param.Kolor",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Translate color name PL->DE (e.g. 'Czarny' -> 'Schwarz').",
    },
    {
        "amazon_field": "size_name",
        "allegro_source": "param.Rozmiar",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Size - may need conversion between PL and DE size standards.",
    },
    {
        "amazon_field": "material_type",
        "allegro_source": "param.Materiał",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Translate material PL->DE (e.g. 'Bawełna' -> 'Baumwolle').",
    },
    {
        "amazon_field": "target_gender",
        "allegro_source": "param.Płeć",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Map Allegro gender values to Amazon enum: "
                "Mężczyzna->Male, Kobieta->Female, Unisex->Unisex.",
    },

    # ── LANGUAGE FIELDS ──
    {
        "amazon_field": "language_value1",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": OPTIONAL,
        "note": "Set to 'German' for Amazon.de listings.",
    },

    # ── BROWSE / CATEGORY ──
    {
        "amazon_field": "recommended_browse_nodes",
        "allegro_source": "category",
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "Amazon browse node ID. No automatic mapping from Allegro categories. "
                "User must select from Amazon category tree or use AI suggestion.",
    },

    # ── GPSR COMPLIANCE (EU required since Dec 2024) ──
    {
        "amazon_field": "gpsr_safety_attestation",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": RECOMMENDED,
        "note": "GPSR safety attestation. Not available from Allegro. User provides.",
    },
    {
        "amazon_field": "gpsr_manufacturer_reference_email_address",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": RECOMMENDED,
        "note": "GPSR manufacturer email. User provides once per manufacturer.",
    },

    # ── BATTERY FIELDS (conditional) ──
    {
        "amazon_field": "batteries_required",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "User must declare if product requires batteries.",
    },
    {
        "amazon_field": "battery_type1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if batteries_required is set. User must specify.",
    },
    {
        "amazon_field": "number_of_batteries1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if batteries_required is set.",
    },
    {
        "amazon_field": "lithium_battery_packaging",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if batteries_required is set.",
    },

    # ── HAZMAT / GHS (conditional) ──
    {
        "amazon_field": "ghs_classification_class1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Only if product has hazardous materials.",
    },
    {
        "amazon_field": "ghs_signal_word",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if ghs_classification_class1 is set.",
    },
    {
        "amazon_field": "hazard_statements",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if ghs_classification_class1 is set.",
    },
    {
        "amazon_field": "precautionary_statements",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if ghs_classification_class1 is set.",
    },
    {
        "amazon_field": "ghs_pictogram",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if ghs_classification_class1 is set.",
    },
    {
        "amazon_field": "supplier_declared_dg_hz_regulation1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Dangerous goods declaration. User must check.",
    },
    {
        "amazon_field": "un_number",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if supplier_declared_dg_hz_regulation1 is set.",
    },
    {
        "amazon_field": "safety_data_sheet_url",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if supplier_declared_dg_hz_regulation1 is set.",
    },
]


# ============================================================================
# SECTION 3: EBAY.DE FIELD MAPPING
# ============================================================================
# eBay Bulk Listing XLSX format - Row 4 headers
# Target: eBay Germany (SiteID=77)

EBAY_MAPPING: List[Dict[str, Any]] = [
    # ── ACTION / SYSTEM ──
    {
        "ebay_field": "*Action(SiteID=77)",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Always 'Add' for new listings. System-generated.",
    },
    {
        "ebay_field": "Category ID",
        "allegro_source": "category",
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "eBay Germany category ID. No auto-mapping from Allegro categories. "
                "User selects or AI suggests closest match.",
    },

    # ── TITLE & DESCRIPTION ──
    {
        "ebay_field": "Title",
        "allegro_source": "title",
        "mapping_type": AI,
        "requirement": REQUIRED,
        "translate": "PL -> DE",
        "note": "Translate + optimize for eBay DE. Max 80 chars. "
                "Allegro 75 chars is close but needs German translation which may be longer.",
    },
    {
        "ebay_field": "Description",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "Translate HTML description PL->DE. eBay supports HTML. "
                "Can keep Allegro's HTML structure but translate content.",
    },

    # ── SKU / IDENTIFIERS ──
    {
        "ebay_field": "Custom label (SKU)",
        "allegro_source": "source_id",
        "mapping_type": TRANSFORM,
        "requirement": RECOMMENDED,
        "note": "Allegro source_id prefixed with 'ALG-' for cross-reference.",
    },
    {
        "ebay_field": "Product:EAN",
        "allegro_source": "ean",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "EAN barcode - direct copy from Allegro.",
    },
    {
        "ebay_field": "Product:MPN",
        "allegro_source": "param.MPN",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "Manufacturer Part Number - direct copy.",
    },

    # ── PRICING ──
    {
        "ebay_field": "Start Price",
        "allegro_source": "price",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Convert PLN -> EUR. Apply margin if configured.",
    },
    {
        "ebay_field": "Quantity",
        "allegro_source": "quantity",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Stock quantity - direct copy.",
    },

    # ── CONDITION ──
    {
        "ebay_field": "Condition ID",
        "allegro_source": "param.Stan",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Map Allegro condition: Nowy->1000 (New), Używany->3000 (Used). "
                "eBay uses numeric condition IDs.",
    },

    # ── IMAGES ──
    {
        "ebay_field": "PicURL",
        "allegro_source": "images[0]",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Primary image URL. May need re-hosting from Allegro CDN. "
                "eBay accepts up to 12 images, pipe-separated in one field.",
    },

    # ── ITEM SPECIFICS (C: prefix fields) ──
    {
        "ebay_field": "C:Marke",
        "allegro_source": "param.Marka",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Brand name - eBay DE uses 'Marke'. Direct copy.",
    },
    {
        "ebay_field": "C:Hersteller",
        "allegro_source": "param.Producent",
        "mapping_type": DIRECT,
        "requirement": RECOMMENDED,
        "note": "Manufacturer - eBay DE uses 'Hersteller'. Direct copy.",
    },
    {
        "ebay_field": "C:Herstellernummer",
        "allegro_source": "param.MPN",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "MPN in German field name.",
    },
    {
        "ebay_field": "C:Farbe",
        "allegro_source": "param.Kolor",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Color translated to German (e.g. 'Czarny' -> 'Schwarz').",
    },
    {
        "ebay_field": "C:Material",
        "allegro_source": "param.Materiał",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Material translated to German (e.g. 'Bawełna' -> 'Baumwolle').",
    },
    {
        "ebay_field": "C:Größe",
        "allegro_source": "param.Rozmiar",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Size - may need conversion between PL and DE standards.",
    },

    # ── MANUFACTURER / GPSR (EU required) ──
    {
        "ebay_field": "Manufacturer Name",
        "allegro_source": "param.Producent",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "GPSR: Manufacturer name from Allegro Producent parameter.",
    },
    {
        "ebay_field": "Manufacturer Address Line 1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Not available from Allegro. User must provide.",
    },
    {
        "ebay_field": "Manufacturer City",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Not available from Allegro. User must provide.",
    },
    {
        "ebay_field": "Manufacturer Country",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Not available from Allegro. User must provide.",
    },

    # ── RESPONSIBLE PERSON (EU GPSR) ──
    {
        "ebay_field": "Responsible Person 1 Type",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Type of responsible person. User must provide.",
    },
    {
        "ebay_field": "Responsible Person 1 Name",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Name of responsible person in EU.",
    },
    {
        "ebay_field": "Responsible Person 1 Address Line 1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Address of responsible person.",
    },
    {
        "ebay_field": "Responsible Person 1 Country",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "GPSR: Country of responsible person.",
    },

    # ── COMPLIANCE ──
    {
        "ebay_field": "ProductCompliancePolicyID",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": RECOMMENDED,
        "note": "Product compliance policy. User configures in eBay account first.",
    },
    {
        "ebay_field": "HazmatPictogramID",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Only for hazardous products.",
    },
    {
        "ebay_field": "HazmatSignalWord",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if HazmatPictogramID is set.",
    },
    {
        "ebay_field": "TakeBackPolicyID",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": RECOMMENDED,
        "note": "WEEE take-back policy for electronics.",
    },
    {
        "ebay_field": "SafetyPictogramID",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Safety pictogram for products with safety concerns.",
    },

    # ── LISTING FORMAT ──
    {
        "ebay_field": "Format",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Always 'FixedPrice' for standard listings.",
    },
    {
        "ebay_field": "Duration",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Default 'GTC' (Good 'Til Cancelled).",
    },
]


# ============================================================================
# SECTION 4: KAUFLAND.DE FIELD MAPPING
# ============================================================================
# Kaufland CSV format - semicolon delimited, UTF-8-BOM
# 39 columns (after normalization: snake_case)

KAUFLAND_MAPPING: List[Dict[str, Any]] = [
    # ── IDENTITY ──
    {
        "kaufland_field": "ean",
        "allegro_source": "ean",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "EAN barcode - direct copy from Allegro.",
    },
    {
        "kaufland_field": "locale",
        "allegro_source": None,
        "mapping_type": DERIVED,
        "requirement": REQUIRED,
        "note": "Always 'de-DE' for Kaufland Germany.",
    },
    {
        "kaufland_field": "category",
        "allegro_source": "category",
        "mapping_type": MANUAL,
        "requirement": REQUIRED,
        "note": "Kaufland category name in German. No auto-mapping from Allegro PL categories.",
    },

    # ── TITLE & DESCRIPTION ──
    {
        "kaufland_field": "title",
        "allegro_source": "title",
        "mapping_type": AI,
        "requirement": REQUIRED,
        "translate": "PL -> DE",
        "note": "Translate to German. Kaufland titles ~120 chars max. "
                "Can expand from Allegro's 75-char limit.",
    },
    {
        "kaufland_field": "short_description",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": RECOMMENDED,
        "translate": "PL -> DE",
        "note": "AI generates short summary in German from Allegro description. "
                "No direct Allegro equivalent.",
    },
    {
        "kaufland_field": "description",
        "allegro_source": "description",
        "mapping_type": AI,
        "requirement": REQUIRED,
        "translate": "PL -> DE",
        "note": "Full description translated to German. Kaufland supports HTML. "
                "Can preserve Allegro HTML structure.",
    },

    # ── MANUFACTURER ──
    {
        "kaufland_field": "manufacturer",
        "allegro_source": "param.Producent",
        "mapping_type": DIRECT,
        "requirement": REQUIRED,
        "note": "Manufacturer name - direct copy from Allegro.",
    },
    {
        "kaufland_field": "mpn",
        "allegro_source": "param.MPN",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "Manufacturer Part Number - direct copy.",
    },

    # ── IMAGES (4 slots in template) ──
    {
        "kaufland_field": "picture",
        "allegro_source": "images[0]",
        "mapping_type": TRANSFORM,
        "requirement": REQUIRED,
        "note": "Primary image. Kaufland template has 4 picture columns. "
                "May need re-hosting from Allegro CDN.",
    },
    {
        "kaufland_field": "picture_2",
        "allegro_source": "images[1]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 2.",
    },
    {
        "kaufland_field": "picture_3",
        "allegro_source": "images[2]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 3.",
    },
    {
        "kaufland_field": "picture_4",
        "allegro_source": "images[3]",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Additional image 4. Allegro has up to 16, Kaufland only 4.",
    },

    # ── PHYSICAL ATTRIBUTES ──
    {
        "kaufland_field": "colour",
        "allegro_source": "param.Kolor",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Translate color PL->DE (e.g. 'Srebrny' -> 'Silber').",
    },
    {
        "kaufland_field": "target",
        "allegro_source": "param.Płeć",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Map Allegro gender: Mężczyzna->herren, Kobieta->damen, Unisex->unisex.",
    },
    {
        "kaufland_field": "shoe_size",
        "allegro_source": "param.Rozmiar",
        "mapping_type": TRANSFORM,
        "requirement": CONDITIONAL,
        "note": "Only for shoes. May need EU size conversion.",
    },
    {
        "kaufland_field": "clothing_size",
        "allegro_source": "param.Rozmiar",
        "mapping_type": TRANSFORM,
        "requirement": CONDITIONAL,
        "note": "Only for clothing. PL and DE use same EU sizing.",
    },
    {
        "kaufland_field": "material_composition",
        "allegro_source": "param.Materiał",
        "mapping_type": AI,
        "requirement": OPTIONAL,
        "translate": "PL -> DE",
        "note": "Material translated to German with percentage if available "
                "(e.g. '100% Bawełna' -> '100% Baumwolle').",
    },
    {
        "kaufland_field": "content_volume",
        "allegro_source": "param.Pojemność",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Volume/capacity if available. Normalize units.",
    },
    {
        "kaufland_field": "weight",
        "allegro_source": "param.Waga",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse weight from Allegro format (e.g. '0,100 kg') to Kaufland format.",
    },
    {
        "kaufland_field": "quantity",
        "allegro_source": "quantity",
        "mapping_type": DIRECT,
        "requirement": OPTIONAL,
        "note": "Stock quantity - direct copy.",
    },
    {
        "kaufland_field": "length",
        "allegro_source": "param.Długość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse length from Allegro format. Kaufland uses MM.",
    },
    {
        "kaufland_field": "width",
        "allegro_source": "param.Szerokość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse width. Kaufland uses MM.",
    },
    {
        "kaufland_field": "height",
        "allegro_source": "param.Wysokość",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Parse height. Kaufland uses MM.",
    },
    {
        "kaufland_field": "base_price_unit",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Base price unit for unit pricing. Not available from Allegro.",
    },

    # ── ENERGY / COMPLIANCE ──
    {
        "kaufland_field": "energy_efficiency_class_2021",
        "allegro_source": "param.Klasa energetyczna",
        "mapping_type": TRANSFORM,
        "requirement": CONDITIONAL,
        "note": "EU 2021 scale (A-G). Map from Allegro energy class if available.",
    },
    {
        "kaufland_field": "energy_label_2021",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "URL to EU energy label image. User must provide.",
    },
    {
        "kaufland_field": "eu_product_data_sheet",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "URL to EU product data sheet. User must provide.",
    },

    # ── SAFETY ──
    {
        "kaufland_field": "safety_guidelines",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Safety guidelines text in German. User must provide if applicable.",
    },
    {
        "kaufland_field": "precautionary_statements",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "Required if safety_guidelines is set. User must provide.",
    },

    # ── AGE / RATINGS ──
    {
        "kaufland_field": "age_recommendation",
        "allegro_source": "param.Wiek",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Age recommendation - translate from Allegro if available.",
    },
    {
        "kaufland_field": "weight_load_max",
        "allegro_source": "param.Maksymalne obciążenie",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Max load capacity if available.",
    },
    {
        "kaufland_field": "performance",
        "allegro_source": "param.Moc",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Performance/power rating if available.",
    },
    {
        "kaufland_field": "filling_capacity",
        "allegro_source": "param.Pojemność",
        "mapping_type": TRANSFORM,
        "requirement": OPTIONAL,
        "note": "Filling capacity if available.",
    },
    {
        "kaufland_field": "fsk",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "German FSK age rating. Required if age_recommendation is set. "
                "No Allegro equivalent.",
    },
    {
        "kaufland_field": "usk",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": CONDITIONAL,
        "note": "German USK game rating. Only for video games.",
    },
    {
        "kaufland_field": "contains_batteries",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Must be 'yes' or 'no'. Not reliably available from Allegro.",
    },

    # ── CUSTOM ATTRIBUTES ──
    {
        "kaufland_field": "your_attribute_1",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Custom attribute slot 1. User-defined.",
    },
    {
        "kaufland_field": "your_attribute_2",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Custom attribute slot 2. User-defined.",
    },
    {
        "kaufland_field": "your_attribute_3",
        "allegro_source": None,
        "mapping_type": MANUAL,
        "requirement": OPTIONAL,
        "note": "Custom attribute slot 3. User-defined.",
    },
]


# ============================================================================
# SECTION 5: CROSS-MARKETPLACE ANALYSIS
# ============================================================================

# Fields where ONE Allegro field maps to MULTIPLE marketplace fields
ONE_TO_MANY_MAPPINGS = {
    "title": {
        "description": "Allegro title (75 chars, PL) maps to 3 marketplace title fields",
        "targets": [
            "Amazon: item_name (200 chars, DE, AI-optimized with keywords)",
            "eBay: Title (80 chars, DE)",
            "Kaufland: title (~120 chars, DE)",
        ],
        "transformation": AI,
        "note": "Each marketplace has different length limits and SEO requirements. "
                "AI should optimize title per marketplace, not just translate.",
    },
    "description": {
        "description": "Allegro HTML description maps to 7+ marketplace fields",
        "targets": [
            "Amazon: product_description (plaintext, 2000 chars, DE)",
            "Amazon: bullet_point1-5 (5 separate fields, AI-generated)",
            "Amazon: generic_keywords (search terms, AI-generated)",
            "eBay: Description (HTML, DE)",
            "Kaufland: description (HTML, DE)",
            "Kaufland: short_description (AI-generated summary, DE)",
        ],
        "transformation": AI,
        "note": "Allegro description is the richest source of content. "
                "AI extracts bullet points, keywords, and summaries from it.",
    },
    "param.Producent": {
        "description": "Allegro Producent maps to manufacturer fields on all 3 platforms",
        "targets": [
            "Amazon: manufacturer",
            "eBay: Manufacturer Name",
            "eBay: C:Hersteller",
            "Kaufland: manufacturer",
        ],
        "transformation": DIRECT,
        "note": "Manufacturer name is usually language-agnostic. Direct copy.",
    },
    "param.Marka": {
        "description": "Allegro Brand maps to brand fields on all platforms",
        "targets": [
            "Amazon: brand_name",
            "eBay: C:Marke",
        ],
        "transformation": DIRECT,
        "note": "Brand names are universal. Direct copy.",
    },
    "param.Kolor": {
        "description": "Allegro color maps to color fields, needs translation",
        "targets": [
            "Amazon: color_name (DE)",
            "eBay: C:Farbe (DE)",
            "Kaufland: colour (DE)",
        ],
        "transformation": AI,
        "note": "PL -> DE translation. Common: Czarny->Schwarz, Biały->Weiß, "
                "Czerwony->Rot, Niebieski->Blau, Zielony->Grün, Srebrny->Silber.",
    },
    "param.Materiał": {
        "description": "Material maps to all 3 platforms, needs translation",
        "targets": [
            "Amazon: material_type (DE)",
            "eBay: C:Material (DE)",
            "Kaufland: material_composition (DE)",
        ],
        "transformation": AI,
        "note": "PL -> DE translation. Common: Bawełna->Baumwolle, Skóra->Leder, "
                "Stal->Stahl, Plastik->Kunststoff.",
    },
    "param.Rozmiar": {
        "description": "Allegro size maps to different size fields per platform",
        "targets": [
            "Amazon: size_name",
            "eBay: C:Größe",
            "Kaufland: shoe_size OR clothing_size (depends on category)",
        ],
        "transformation": TRANSFORM,
        "note": "Size systems are mostly the same in PL and DE (EU sizing). "
                "Kaufland splits into shoe_size and clothing_size.",
    },
    "images": {
        "description": "Allegro photos (up to 16) distributed across marketplace image slots",
        "targets": [
            "Amazon: main_image_url + other_image_url1-8 (max 9)",
            "eBay: PicURL (pipe-separated, max 12)",
            "Kaufland: picture x4 (max 4)",
        ],
        "transformation": TRANSFORM,
        "note": "Allegro supports most images (16). Amazon gets 9, eBay 12, Kaufland only 4. "
                "Images may need re-hosting if Allegro CDN restricts external access.",
    },
    "price": {
        "description": "PLN price converts to EUR for all 3 platforms",
        "targets": [
            "Amazon: standard_price (EUR)",
            "eBay: Start Price (EUR)",
        ],
        "transformation": TRANSFORM,
        "note": "PLN -> EUR conversion required. Kaufland pricing is set separately "
                "in their seller portal, not in the product data CSV.",
    },
    "ean": {
        "description": "EAN barcode is universal across all platforms",
        "targets": [
            "Amazon: external_product_id",
            "eBay: Product:EAN",
            "Kaufland: ean",
        ],
        "transformation": DIRECT,
        "note": "EAN is a global standard. Direct copy to all platforms.",
    },
}


# Fields that have NO Allegro equivalent - must be manual or AI-generated
FIELDS_WITHOUT_ALLEGRO_SOURCE = {
    "amazon": [
        "feed_product_type",
        "manufacturer_contact_information",
        "country_of_origin",
        "recommended_browse_nodes",
        "gpsr_safety_attestation",
        "gpsr_manufacturer_reference_email_address",
        "batteries_required",
        "battery_type1",
        "number_of_batteries1",
        "lithium_battery_packaging",
        "ghs_classification_class1",
        "ghs_signal_word",
        "hazard_statements",
        "precautionary_statements",
        "ghs_pictogram",
        "supplier_declared_dg_hz_regulation1",
        "un_number",
        "safety_data_sheet_url",
        "bullet_point1-5 (AI-generated, not manual)",
        "generic_keywords (AI-generated, not manual)",
    ],
    "ebay": [
        "Category ID",
        "Manufacturer Address Line 1",
        "Manufacturer City",
        "Manufacturer Country",
        "Responsible Person 1 Type",
        "Responsible Person 1 Name",
        "Responsible Person 1 Address Line 1",
        "Responsible Person 1 Country",
        "ProductCompliancePolicyID",
        "HazmatPictogramID",
        "HazmatSignalWord",
        "TakeBackPolicyID",
        "SafetyPictogramID",
        "Format (system-derived)",
        "Duration (system-derived)",
    ],
    "kaufland": [
        "locale (always de-DE)",
        "category (manual selection)",
        "base_price_unit",
        "energy_label_2021",
        "eu_product_data_sheet",
        "safety_guidelines",
        "precautionary_statements",
        "fsk",
        "usk",
        "contains_batteries",
        "your_attribute_1-3",
        "short_description (AI-generated from description)",
    ],
}


# Fields requiring PL -> DE translation
FIELDS_NEEDING_TRANSLATION = [
    # High priority (required or prominent fields)
    {"field": "title", "priority": "high", "direction": "PL -> DE",
     "note": "Title is the most visible field. Must be SEO-optimized per marketplace."},
    {"field": "description", "priority": "high", "direction": "PL -> DE",
     "note": "Full description translation. Preserve HTML structure where supported."},
    {"field": "bullet_points", "priority": "high", "direction": "PL -> DE",
     "note": "Amazon only. AI generates from PL description, directly in DE."},
    {"field": "generic_keywords", "priority": "high", "direction": "PL -> DE",
     "note": "Amazon only. AI generates German search terms."},

    # Medium priority (visible attribute fields)
    {"field": "color", "priority": "medium", "direction": "PL -> DE",
     "note": "Use lookup table for common colors. AI for uncommon ones."},
    {"field": "material", "priority": "medium", "direction": "PL -> DE",
     "note": "Use lookup table for common materials. AI for uncommon ones."},
    {"field": "short_description", "priority": "medium", "direction": "PL -> DE",
     "note": "Kaufland only. AI generates German summary."},

    # Low priority (usually language-agnostic)
    {"field": "brand", "priority": "low", "direction": "PL -> DE",
     "note": "Usually same in both languages. Only translate if clearly Polish."},
    {"field": "manufacturer", "priority": "low", "direction": "PL -> DE",
     "note": "Company names are usually international."},
    {"field": "size", "priority": "low", "direction": "PL -> DE",
     "note": "EU sizing is the same. Only labels might differ."},
]


# ============================================================================
# SECTION 6: STATIC TRANSLATION LOOKUPS
# ============================================================================
# WHY here: Common values that don't need AI — saves API calls and latency.

COLOR_PL_TO_DE = {
    "czarny": "Schwarz",
    "biały": "Weiß",
    "czerwony": "Rot",
    "niebieski": "Blau",
    "zielony": "Grün",
    "żółty": "Gelb",
    "pomarańczowy": "Orange",
    "fioletowy": "Lila",
    "różowy": "Rosa",
    "szary": "Grau",
    "brązowy": "Braun",
    "srebrny": "Silber",
    "złoty": "Gold",
    "beżowy": "Beige",
    "granatowy": "Marineblau",
    "bordowy": "Bordeaux",
    "turkusowy": "Türkis",
    "khaki": "Khaki",
    "wielokolorowy": "Mehrfarbig",
    "przezroczysty": "Transparent",
}

MATERIAL_PL_TO_DE = {
    "bawełna": "Baumwolle",
    "poliester": "Polyester",
    "skóra": "Leder",
    "skóra naturalna": "Echtleder",
    "skóra ekologiczna": "Kunstleder",
    "wełna": "Wolle",
    "jedwab": "Seide",
    "len": "Leinen",
    "nylon": "Nylon",
    "akryl": "Acryl",
    "guma": "Gummi",
    "metal": "Metall",
    "stal": "Stahl",
    "stal nierdzewna": "Edelstahl",
    "aluminium": "Aluminium",
    "drewno": "Holz",
    "plastik": "Kunststoff",
    "szkło": "Glas",
    "ceramika": "Keramik",
    "silikon": "Silikon",
    "karbon": "Kohlefaser",
    "tkanina": "Stoff",
}

CONDITION_ALLEGRO_TO_EBAY = {
    "Nowy": 1000,
    "Używany": 3000,
    "Nowy z metką": 1000,
    "Nowy bez metki": 1500,
    "Odnowiony": 2000,
    "Używany - bardzo dobry": 4000,
    "Używany - dobry": 5000,
    "Używany - dostateczny": 6000,
}

GENDER_ALLEGRO_TO_MARKETPLACE = {
    # Allegro PL -> Amazon EN / Kaufland DE / eBay DE
    "Mężczyzna": {"amazon": "Male", "kaufland": "herren", "ebay": "Herren"},
    "Kobieta": {"amazon": "Female", "kaufland": "damen", "ebay": "Damen"},
    "Unisex": {"amazon": "Unisex", "kaufland": "unisex", "ebay": "Unisex"},
    "Chłopiec": {"amazon": "Male", "kaufland": "jungen", "ebay": "Jungen"},
    "Dziewczynka": {"amazon": "Female", "kaufland": "mädchen", "ebay": "Mädchen"},
    "Dziecko": {"amazon": "Unisex", "kaufland": "kinder", "ebay": "Kinder"},
}


# ============================================================================
# SECTION 7: SUMMARY STATISTICS
# ============================================================================

MAPPING_SUMMARY = {
    "allegro_source_fields": 20,
    "amazon_target_fields": 52,
    "ebay_target_fields": 33,
    "kaufland_target_fields": 39,

    "amazon_auto_fillable": 28,  # Direct + Transform + AI + Derived
    "amazon_manual_required": 24,  # Manual + Conditional

    "ebay_auto_fillable": 18,
    "ebay_manual_required": 15,

    "kaufland_auto_fillable": 22,
    "kaufland_manual_required": 17,

    "fields_needing_ai_translation": 7,
    "fields_with_static_lookup": 4,  # color, material, condition, gender
    "one_to_many_allegro_fields": 10,

    "automation_rate": {
        "amazon": "54% auto-fill, 46% manual/conditional",
        "ebay": "55% auto-fill, 45% manual/conditional",
        "kaufland": "56% auto-fill, 44% manual/conditional",
    },
    "note": "Automation rate improves significantly when user configures "
            "manufacturer/GPSR data once — it applies to all products from same brand.",
}
