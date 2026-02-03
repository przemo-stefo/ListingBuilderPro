# backend/services/converter/template_generator.py
# Purpose: Generate marketplace-specific CSV/XLSX files from converted product data
# NOT for: Data conversion, AI translation, or scraping

import csv
import io
from typing import List

import structlog

from services.converter.converter_service import ConvertedProduct

logger = structlog.get_logger()


# ── Amazon CSV column order ───────────────────────────────────────────────
# Matches the key fields from NUTRITIONAL_SUPPLEMENT.xlsm Row 3 field IDs.
# Full flat file has 300+ columns — we only fill what we have.

AMAZON_COLUMNS = [
    "feed_product_type",
    "item_sku",
    "brand_name",
    "update_delete",
    "item_name",
    "external_product_id",
    "external_product_id_type",
    "manufacturer",
    "manufacturer_contact_information",
    "country_of_origin",
    "part_number",
    "model",
    "product_description",
    "bullet_point1",
    "bullet_point2",
    "bullet_point3",
    "bullet_point4",
    "bullet_point5",
    "generic_keywords",
    "standard_price",
    "quantity",
    "main_image_url",
    "other_image_url1",
    "other_image_url2",
    "other_image_url3",
    "other_image_url4",
    "other_image_url5",
    "other_image_url6",
    "other_image_url7",
    "other_image_url8",
    "item_weight",
    "item_dimensions_length",
    "item_dimensions_width",
    "item_dimensions_height",
    "color_name",
    "size_name",
    "material_type",
    "target_gender",
    "language_value1",
    "recommended_browse_nodes",
    "gpsr_safety_attestation",
]


# ── eBay CSV column order ─────────────────────────────────────────────────
# Matches eBay bulk listing template Row 4 headers

EBAY_COLUMNS = [
    "*Action(SiteID=77)",
    "Category ID",
    "Title",
    "Description",
    "Custom label (SKU)",
    "Product:EAN",
    "Product:MPN",
    "Start Price",
    "Quantity",
    "Condition ID",
    "PicURL",
    "C:Marke",
    "C:Hersteller",
    "C:Herstellernummer",
    "C:Farbe",
    "C:Material",
    "C:Größe",
    "Manufacturer Name",
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
    "Format",
    "Duration",
]


# ── Kaufland CSV column order ─────────────────────────────────────────────
# Matches "Product data template_en3 kaufl 2.csv" headers (39 columns)

KAUFLAND_COLUMNS = [
    "ean",
    "locale",
    "category",
    "title",
    "short_description",
    "description",
    "manufacturer",
    "mpn",
    "picture_1",
    "picture_2",
    "picture_3",
    "picture_4",
    "colour",
    "target",
    "shoe_size",
    "clothing_size",
    "material_composition",
    "content_volume",
    "weight",
    "quantity",
    "length",
    "width",
    "height",
    "base_price_unit",
    "energy_efficiency_class_2021",
    "energy_label_2021",
    "eu_product_data_sheet",
    "safety_guidelines",
    "precautionary_statements",
    "age_recommendation",
    "weight_load_max",
    "performance",
    "filling_capacity",
    "fsk",
    "usk",
    "contains_batteries",
    "your_attribute_1",
    "your_attribute_2",
    "your_attribute_3",
]


def generate_amazon_csv(products: List[ConvertedProduct]) -> bytes:
    """Generate Amazon flat file CSV from converted products.

    Amazon flat files are tab-separated. Row 1 = labels, Row 2 = blank, Row 3 = field IDs.
    For CSV import simplicity, we output field IDs as header + data rows.

    Returns:
        UTF-8 encoded CSV bytes (tab-separated)
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=AMAZON_COLUMNS,
        delimiter="\t",
        extrasaction="ignore",
    )
    writer.writeheader()

    for product in products:
        if product.error:
            continue
        writer.writerow(product.fields)

    content = output.getvalue()
    logger.info("amazon_csv_generated", products=len(products), size=len(content))
    return content.encode("utf-8")


def generate_ebay_csv(products: List[ConvertedProduct]) -> bytes:
    """Generate eBay bulk listing CSV from converted products.

    eBay uses comma-separated CSV with standard headers.

    Returns:
        UTF-8 encoded CSV bytes (comma-separated)
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=EBAY_COLUMNS,
        delimiter=",",
        extrasaction="ignore",
    )
    writer.writeheader()

    for product in products:
        if product.error:
            continue
        writer.writerow(product.fields)

    content = output.getvalue()
    logger.info("ebay_csv_generated", products=len(products), size=len(content))
    return content.encode("utf-8")


def generate_kaufland_csv(products: List[ConvertedProduct]) -> bytes:
    """Generate Kaufland product data CSV from converted products.

    Kaufland uses semicolon-separated CSV with UTF-8-BOM encoding.

    Returns:
        UTF-8-BOM encoded CSV bytes (semicolon-separated)
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=KAUFLAND_COLUMNS,
        delimiter=";",
        extrasaction="ignore",
    )
    writer.writeheader()

    for product in products:
        if product.error:
            continue
        writer.writerow(product.fields)

    content = output.getvalue()
    # Kaufland requires UTF-8-BOM
    bom = b'\xef\xbb\xbf'
    logger.info("kaufland_csv_generated", products=len(products), size=len(content))
    return bom + content.encode("utf-8")


def generate_template(
    products: List[ConvertedProduct],
    marketplace: str,
) -> bytes:
    """Generate the appropriate template file for the target marketplace.

    Args:
        products: List of converted products
        marketplace: Target marketplace name

    Returns:
        File bytes ready to write/download
    """
    generators = {
        "amazon": generate_amazon_csv,
        "ebay": generate_ebay_csv,
        "kaufland": generate_kaufland_csv,
    }

    generator = generators.get(marketplace)
    if not generator:
        raise ValueError(f"Unknown marketplace: {marketplace}. Use: amazon, ebay, kaufland")

    return generator(products)


def get_filename(marketplace: str) -> str:
    """Get the suggested filename for the generated template."""
    filenames = {
        "amazon": "amazon_flat_file.tsv",
        "ebay": "ebay_bulk_listing.csv",
        "kaufland": "kaufland_product_data.csv",
    }
    return filenames.get(marketplace, f"{marketplace}_export.csv")


def get_content_type(marketplace: str) -> str:
    """Get the HTTP content type for the generated file."""
    if marketplace == "amazon":
        return "text/tab-separated-values; charset=utf-8"
    return "text/csv; charset=utf-8"
