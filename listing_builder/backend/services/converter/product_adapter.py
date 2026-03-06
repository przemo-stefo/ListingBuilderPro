# backend/services/converter/product_adapter.py
# Purpose: Adapt Product DB model → AllegroProduct for converter pipeline
# NOT for: Scraping, translation, or conversion logic

from typing import List
from models.product import Product
from services.scraper.allegro_scraper import AllegroProduct


def product_to_allegro(product: Product) -> AllegroProduct:
    """Convert a DB Product into AllegroProduct format for the converter pipeline.

    WHY: Converter expects AllegroProduct (scraped data). This adapter lets us
    reuse the entire convert_batch() pipeline for products already in the database.
    """
    attributes = product.attributes if isinstance(product.attributes, dict) else {}
    images = product.images if isinstance(product.images, list) else []

    return AllegroProduct(
        source_url=product.source_url or "",
        source_id=product.source_id or str(product.id),
        title=product.title_original or "",
        description=product.description_original or "",
        price=str(product.price) if product.price else "",
        currency=product.currency or "PLN",
        ean=str(attributes.get("ean", "")),
        images=images,
        category=product.category or "",
        quantity=str(attributes.get("quantity", "1")),
        condition=str(attributes.get("condition", "new")),
        parameters=attributes.get("parameters") if isinstance(attributes.get("parameters"), dict) else {},
        brand=product.brand or "",
        manufacturer=str(attributes.get("manufacturer", "")),
    )


def products_to_allegro(products: List[Product]) -> List[AllegroProduct]:
    """Batch convert DB Products to AllegroProduct format."""
    return [product_to_allegro(p) for p in products]
