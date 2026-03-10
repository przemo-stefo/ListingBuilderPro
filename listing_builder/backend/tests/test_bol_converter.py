# backend/tests/test_bol_converter.py
# Purpose: Tests for BOL.com converter, CSV template, and scraper parsing
# NOT for: AI translation tests (those need Groq mocks)

import csv
import io
import pytest

from services.scraper.allegro_scraper import AllegroProduct
from services.converter.converter_service import convert_to_bol, ConvertedProduct
from services.converter.template_generator import generate_bol_csv, BOL_COLUMNS
from services.scraper.bol_scraper import (
    extract_bol_product_id,
    _parse_bol_html,
    _parse_json_ld,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_allegro_product():
    """Allegro product with typical Polish data for BOL conversion."""
    return AllegroProduct(
        source_url="https://allegro.pl/oferta/buty-sportowe-nike-12345",
        source_id="12345",
        title="Buty sportowe Nike Air Max 90",
        description="<p>Wygodne buty sportowe na co dzień.</p>",
        price="399.99",
        currency="PLN",
        ean="5901234567890",
        images=["https://img.allegro.pl/1.jpg", "https://img.allegro.pl/2.jpg"],
        category="Obuwie",
        quantity="10",
        condition="Nowy",
        parameters={"Marka": "Nike", "Kolor": "czarny", "Rozmiar": "42", "Waga": "0,500 kg"},
        brand="Nike",
        manufacturer="Nike Inc.",
    )


@pytest.fixture
def sample_ai_output():
    """AI translation output for BOL (Dutch)."""
    return {
        "title_nl": "Nike Air Max 90 Sportschoenen Zwart",
        "description_nl": "Comfortabele sportschoenen voor dagelijks gebruik.",
        "short_description_nl": "Nike Air Max 90 in zwart.",
        "color_nl": "Zwart",
        "material_nl": "Leer",
        "bullet_points_nl": [
            "Comfortabele pasvorm",
            "Duurzaam materiaal",
            "Stijlvol ontwerp",
            "Geschikt voor dagelijks gebruik",
            "Nike Air demping",
            "", "", "",
        ],
    }


# ── convert_to_bol ───────────────────────────────────────────────────────

class TestConvertToBol:

    def test_basic_fields(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        f = result.fields

        assert result.marketplace == "bol"
        assert f["ean"] == "5901234567890"
        assert f["sku"] == "ALG-12345"
        assert f["condition"] == "NEW"

    def test_dutch_title_and_description(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        f = result.fields

        assert f["title"] == "Nike Air Max 90 Sportschoenen Zwart"
        assert "Comfortabele" in f["description"]
        assert f["short_description"] == "Nike Air Max 90 in zwart."

    def test_price_eur_conversion(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {}, eur_rate=0.25)
        f = result.fields
        # 399.99 * 0.25 = ~100.00
        assert float(f["price"]) == pytest.approx(100.0, abs=1.0)

    def test_images_mapped(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        f = result.fields

        assert f["image_1"] == "https://img.allegro.pl/1.jpg"
        assert f["image_2"] == "https://img.allegro.pl/2.jpg"
        assert f.get("image_3", "") == ""

    def test_bullet_points_mapped(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        f = result.fields

        assert f["bullet_point_1"] == "Comfortabele pasvorm"
        assert f["bullet_point_5"] == "Nike Air demping"

    def test_brand_and_manufacturer(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        f = result.fields

        assert f["brand"] == "Nike"
        assert f["manufacturer"] == "Nike Inc."

    def test_delivery_code_default(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        assert result.fields["delivery_code"] == "3-5d"

    def test_weight_parsed(self, sample_allegro_product, sample_ai_output):
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        # "0,500 kg" → should parse to "0.500" or similar decimal
        assert result.fields["weight_kg"] != ""

    def test_title_truncated_to_500(self, sample_allegro_product, sample_ai_output):
        sample_ai_output["title_nl"] = "A" * 600
        result = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        assert len(result.fields["title"]) <= 500

    def test_empty_ai_output(self, sample_allegro_product):
        """convert_to_bol should not crash when AI returns empty dict."""
        result = convert_to_bol(sample_allegro_product, {}, {})
        f = result.fields

        assert result.marketplace == "bol"
        assert f["ean"] == "5901234567890"
        # Title falls back to Polish original
        assert f["title"] == "Buty sportowe Nike Air Max 90"
        assert f["brand"] == "Nike"


# ── generate_bol_csv ─────────────────────────────────────────────────────

class TestGenerateBolCsv:

    def test_csv_has_headers(self, sample_allegro_product, sample_ai_output):
        product = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        csv_bytes = generate_bol_csv([product])
        text = csv_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        assert set(BOL_COLUMNS).issubset(set(reader.fieldnames))

    def test_csv_has_data_row(self, sample_allegro_product, sample_ai_output):
        product = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        csv_bytes = generate_bol_csv([product])
        text = csv_bytes.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))

        assert len(rows) == 1
        assert rows[0]["ean"] == "5901234567890"

    def test_csv_skips_error_products(self, sample_allegro_product, sample_ai_output):
        good = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        bad = ConvertedProduct(source_url="x", marketplace="bol", error="fail")
        csv_bytes = generate_bol_csv([good, bad])
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))

        assert len(rows) == 1

    def test_csv_is_utf8(self, sample_allegro_product, sample_ai_output):
        sample_ai_output["title_nl"] = "Schoenen für Größe"
        product = convert_to_bol(sample_allegro_product, sample_ai_output, {})
        csv_bytes = generate_bol_csv([product])

        # Should not raise on decode
        text = csv_bytes.decode("utf-8")
        assert "Größe" in text


# ── BOL scraper parsing ──────────────────────────────────────────────────

class TestBolScraper:

    def test_extract_product_id_standard(self):
        url = "https://www.bol.com/nl/nl/p/product-name/9300000123456789/"
        assert extract_bol_product_id(url) == "9300000123456789"

    def test_extract_product_id_no_trailing_slash(self):
        url = "https://www.bol.com/nl/nl/p/product-name/9300000123456789"
        assert extract_bol_product_id(url) == "9300000123456789"

    def test_extract_product_id_with_query(self):
        url = "https://www.bol.com/nl/nl/p/name/9300000123456789/?promo=main"
        assert extract_bol_product_id(url) == "9300000123456789"

    def test_extract_product_id_invalid(self):
        assert extract_bol_product_id("https://www.bol.com/nl/nl/") == ""

    def test_parse_json_ld_product(self):
        from bs4 import BeautifulSoup

        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Product", "name": "Test Product", "gtin13": "1234567890123",
         "brand": {"@type": "Brand", "name": "TestBrand"},
         "offers": {"@type": "Offer", "price": "29.99"},
         "image": ["https://img.bol.com/1.jpg"]}
        </script>
        </head><body></body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        ld = _parse_json_ld(soup)

        assert ld is not None
        assert ld["name"] == "Test Product"
        assert ld["gtin13"] == "1234567890123"

    def test_parse_bol_html_with_json_ld(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "Product", "name": "Bol Test", "gtin13": "9876543210123",
         "brand": {"name": "BolBrand"}, "description": "A test product",
         "offers": {"price": "19.99"}, "image": "https://img.bol.com/main.jpg"}
        </script>
        </head><body>
        <nav aria-label="breadcrumb"><a>Home</a><a>Schoenen</a></nav>
        </body></html>
        """
        url = "https://www.bol.com/nl/nl/p/bol-test/9300000987654321/"
        product = _parse_bol_html(html, url)

        assert product.title == "Bol Test"
        assert product.ean == "9876543210123"
        assert product.brand == "BolBrand"
        assert product.price == "19.99"
        assert product.images == ["https://img.bol.com/main.jpg"]
        assert product.source_id == "9300000987654321"
        assert product.category == "Schoenen"
        assert product.error is None

    def test_parse_bol_html_no_data(self):
        html = "<html><body><p>Empty page</p></body></html>"
        product = _parse_bol_html(html, "https://www.bol.com/nl/nl/p/x/123456789012/")

        assert product.error is not None

    def test_parse_bol_html_fallback_h1(self):
        html = "<html><body><h1>Fallback Title</h1></body></html>"
        product = _parse_bol_html(html, "https://www.bol.com/nl/nl/p/x/123456789012/")

        assert product.title == "Fallback Title"
        assert product.error is None
