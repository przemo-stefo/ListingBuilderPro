# backend/services/converter/marketplace_converters.py
# Purpose: Individual marketplace converter functions (Amazon, eBay, Kaufland, BOL, Rozetka)
# NOT for: Orchestration logic (that's converter_service.py), AI calls, or templates

from typing import Dict

from services.scraper.allegro_scraper import AllegroProduct
from services.converter.converter_helpers import (
    ConvertedProduct, get_param, parse_weight, parse_dimension_cm,
    parse_dimension_mm, convert_pln_to_eur,
)
from services.converter.static_translations import (
    translate_gender,
    translate_condition,
)


def convert_to_amazon(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Map scraped Allegro product to Amazon.de flat file fields."""
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="amazon",
    )

    f = result.fields

    # Identity
    f["item_sku"] = f"ALG-{product.source_id}"
    f["update_delete"] = "Update"
    f["external_product_id"] = product.ean
    f["external_product_id_type"] = "EAN" if product.ean else ""

    # Title + Description (AI-translated)
    f["item_name"] = ai.get("title_de", product.title)
    f["product_description"] = ai.get("description_de", "")

    # Bullet points (AI-generated, Amazon max 5)
    bullets = ai.get("bullet_points", [""] * 5)
    for i, bp in enumerate(bullets[:5]):
        f[f"bullet_point{i+1}"] = bp

    # Search keywords
    f["generic_keywords"] = ai.get("search_keywords", "")

    # Brand / Manufacturer
    f["brand_name"] = product.brand or get_param(product, "Marka")
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")
    f["part_number"] = get_param(product, "MPN", "Numer producenta")
    f["model"] = get_param(product, "Model")

    # GPSR (user-provided, same for all products from same manufacturer)
    f["manufacturer_contact_information"] = gpsr_data.get("manufacturer_contact", "")
    f["country_of_origin"] = gpsr_data.get("country_of_origin", "")
    f["gpsr_safety_attestation"] = gpsr_data.get("safety_attestation", "")

    # Pricing
    f["standard_price"] = convert_pln_to_eur(product.price, eur_rate)
    f["quantity"] = product.quantity or "1"

    # Images
    for i, img_url in enumerate(product.images[:9]):
        if i == 0:
            f["main_image_url"] = img_url
        else:
            f[f"other_image_url{i}"] = img_url

    # Physical attributes
    f["item_weight"] = parse_weight(get_param(product, "Waga"))
    f["item_dimensions_length"] = parse_dimension_cm(get_param(product, "Długość"))
    f["item_dimensions_width"] = parse_dimension_cm(get_param(product, "Szerokość"))
    f["item_dimensions_height"] = parse_dimension_cm(get_param(product, "Wysokość"))

    # Color / Material
    f["color_name"] = ai.get("color_de", "")
    f["material_type"] = ai.get("material_de", "")

    # Size / Gender
    f["size_name"] = get_param(product, "Rozmiar")
    gender = get_param(product, "Płeć")
    f["target_gender"] = translate_gender(gender, "amazon") or ""

    # Language
    f["language_value1"] = "German"

    # Category (user must provide)
    f["recommended_browse_nodes"] = gpsr_data.get("amazon_browse_node", "")
    f["feed_product_type"] = gpsr_data.get("amazon_product_type", "")

    # Warnings for missing required fields
    if not product.ean:
        result.warnings.append("EAN missing — required for Amazon")
    if not f["brand_name"]:
        result.warnings.append("Brand missing — required for Amazon")
    if not f["manufacturer_contact_information"]:
        result.warnings.append("GPSR manufacturer contact missing — provide in settings")
    if not f["recommended_browse_nodes"]:
        result.warnings.append("Amazon browse node missing — select category")

    return result


def convert_to_ebay(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Map scraped Allegro product to eBay.de bulk listing fields."""
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="ebay",
    )

    f = result.fields

    # System fields
    f["*Action(SiteID=77)"] = "Add"
    f["Category ID"] = gpsr_data.get("ebay_category_id", "")

    # Title + Description (AI)
    f["Title"] = ai.get("title_de", product.title)[:80]
    f["Description"] = ai.get("description_de", "")

    # Identifiers
    f["Custom label (SKU)"] = f"ALG-{product.source_id}"
    f["Product:EAN"] = product.ean
    f["Product:MPN"] = get_param(product, "MPN", "Numer producenta")

    # Pricing
    f["Start Price"] = convert_pln_to_eur(product.price, eur_rate)
    f["Quantity"] = product.quantity or "1"

    # Condition
    condition = product.condition or get_param(product, "Stan")
    f["Condition ID"] = str(translate_condition(condition) or 1000)

    # Images (pipe-separated for eBay)
    f["PicURL"] = "|".join(product.images[:12]) if product.images else ""

    # Item specifics
    f["C:Marke"] = product.brand or get_param(product, "Marka")
    f["C:Hersteller"] = product.manufacturer or get_param(product, "Producent")
    f["C:Herstellernummer"] = get_param(product, "MPN", "Numer producenta")
    f["C:Farbe"] = ai.get("color_de", "")
    f["C:Material"] = ai.get("material_de", "")
    f["C:Größe"] = get_param(product, "Rozmiar")

    # GPSR manufacturer
    f["Manufacturer Name"] = product.manufacturer or get_param(product, "Producent")
    f["Manufacturer Address Line 1"] = gpsr_data.get("manufacturer_address", "")
    f["Manufacturer City"] = gpsr_data.get("manufacturer_city", "")
    f["Manufacturer Country"] = gpsr_data.get("manufacturer_country", "")

    # GPSR responsible person
    f["Responsible Person 1 Type"] = gpsr_data.get("responsible_person_type", "")
    f["Responsible Person 1 Name"] = gpsr_data.get("responsible_person_name", "")
    f["Responsible Person 1 Address Line 1"] = gpsr_data.get("responsible_person_address", "")
    f["Responsible Person 1 Country"] = gpsr_data.get("responsible_person_country", "")

    # Listing format
    f["Format"] = "FixedPrice"
    f["Duration"] = "GTC"

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — required for eBay")
    if not f["Category ID"]:
        result.warnings.append("eBay Category ID missing — select category")
    if not f["Manufacturer Address Line 1"]:
        result.warnings.append("GPSR manufacturer address missing — provide in settings")

    return result


def convert_to_kaufland(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
) -> ConvertedProduct:
    """Map scraped Allegro product to Kaufland.de CSV fields."""
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="kaufland",
    )

    f = result.fields

    # Identity
    f["ean"] = product.ean
    f["locale"] = "de-DE"
    f["category"] = gpsr_data.get("kaufland_category", "")

    # Title + Description (AI)
    f["title"] = ai.get("title_de", product.title)[:120]
    f["short_description"] = ai.get("short_description_de", "")
    f["description"] = ai.get("description_de", "")

    # Manufacturer
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")
    f["mpn"] = get_param(product, "MPN", "Numer producenta")

    # Images (Kaufland: 4 slots)
    for i, img_url in enumerate(product.images[:4]):
        f[f"picture_{i+1}"] = img_url

    # Physical attributes
    f["colour"] = ai.get("color_de", "")
    gender = get_param(product, "Płeć")
    f["target"] = translate_gender(gender, "kaufland") or ""
    f["material_composition"] = ai.get("material_de", "")
    f["weight"] = parse_weight(get_param(product, "Waga"))
    f["quantity"] = product.quantity or "1"
    f["length"] = parse_dimension_mm(get_param(product, "Długość"))
    f["width"] = parse_dimension_mm(get_param(product, "Szerokość"))
    f["height"] = parse_dimension_mm(get_param(product, "Wysokość"))

    # Size
    size = get_param(product, "Rozmiar")
    f["shoe_size"] = ""
    f["clothing_size"] = size

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — required for Kaufland")
    if not f["category"]:
        result.warnings.append("Kaufland category missing — select category (German name)")
    if not f["manufacturer"]:
        result.warnings.append("Manufacturer missing — required for Kaufland")

    return result


def convert_to_bol(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Map scraped Allegro product to BOL.com Retailer CSV fields.

    WHY: BOL.com (Netherlands/Belgium) uses Dutch product data.
    AI translator handles PL→NL. No GPSR required (yet).
    """
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="bol",
    )

    f = result.fields

    # Identity
    f["ean"] = product.ean
    f["sku"] = f"ALG-{product.source_id}"
    f["condition"] = "NEW"

    # Title + Description (AI-translated to Dutch)
    f["title"] = ai.get("title_nl", product.title)[:500]
    f["short_description"] = ai.get("short_description_nl", "")[:300]
    f["description"] = ai.get("description_nl", "")[:2000]

    # Brand / Manufacturer
    f["brand"] = product.brand or get_param(product, "Marka")
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")
    f["mpn"] = get_param(product, "MPN", "Numer producenta")

    # Pricing (EUR — BOL uses EUR natively)
    f["price"] = convert_pln_to_eur(product.price, eur_rate)
    f["stock"] = product.quantity or "1"

    # Delivery (BOL requires delivery code)
    f["delivery_code"] = "3-5d"

    # Images (BOL supports up to 10)
    for i, img_url in enumerate(product.images[:10]):
        f[f"image_{i+1}"] = img_url

    # Physical attributes
    f["weight_kg"] = parse_weight(get_param(product, "Waga"))
    f["length_cm"] = parse_dimension_cm(get_param(product, "Długość"))
    f["width_cm"] = parse_dimension_cm(get_param(product, "Szerokość"))
    f["height_cm"] = parse_dimension_cm(get_param(product, "Wysokość"))

    # Color / Material (Dutch)
    f["color"] = ai.get("color_nl", "")
    f["material"] = ai.get("material_nl", "")
    f["size"] = get_param(product, "Rozmiar")

    # Bullet points (BOL supports up to 8)
    bullets = ai.get("bullet_points_nl", [])
    for i, bp in enumerate(bullets[:8]):
        f[f"bullet_point_{i+1}"] = bp

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — required for BOL.com")
    if not f["brand"]:
        result.warnings.append("Brand missing — required for BOL.com")

    return result


def convert_to_rozetka(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    uah_rate: float = 9.5,
) -> ConvertedProduct:
    """Map scraped Allegro product to Rozetka marketplace fields.

    WHY: Rozetka (Ukraine) requires Ukrainian-language listings.
    AI translator handles PL→UK. Currency is UAH.
    """
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="rozetka",
    )

    f = result.fields

    # Identity
    f["ean"] = product.ean
    f["sku"] = f"ALG-{product.source_id}"
    f["condition"] = "new"

    # Title + Description (AI-translated to Ukrainian)
    f["title"] = ai.get("title_uk", product.title)[:150]
    f["description"] = ai.get("description_uk", "")[:4000]

    # Brand / Manufacturer
    f["brand"] = product.brand or get_param(product, "Marka")
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")

    # Pricing (UAH — 1 PLN ≈ 9.5 UAH)
    try:
        pln = float((product.price or "0").replace(",", ".").strip())
        f["price"] = f"{pln * uah_rate:.2f}"
    except (ValueError, AttributeError):
        f["price"] = product.price or ""
    f["stock"] = product.quantity or "1"
    f["currency"] = "UAH"

    # Images (Rozetka supports up to 10)
    for i, img_url in enumerate(product.images[:10]):
        f[f"image_{i+1}"] = img_url

    # Physical attributes
    f["weight_kg"] = parse_weight(get_param(product, "Waga"))
    f["length_cm"] = parse_dimension_cm(get_param(product, "Długość"))
    f["width_cm"] = parse_dimension_cm(get_param(product, "Szerokość"))
    f["height_cm"] = parse_dimension_cm(get_param(product, "Wysokość"))

    # Color / Material (Ukrainian)
    f["color"] = ai.get("color_uk", "")
    f["material"] = ai.get("material_uk", "")
    f["size"] = get_param(product, "Rozmiar")

    # Bullet points
    bullets = ai.get("bullet_points_uk", [])
    for i, bp in enumerate(bullets[:8]):
        f[f"bullet_point_{i+1}"] = bp

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — recommended for Rozetka")
    if not f["brand"]:
        result.warnings.append("Brand missing — recommended for Rozetka")

    return result
