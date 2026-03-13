# backend/tests/test_rozetka_converter.py
# Purpose: Tests for Rozetka converter and CSV template generator
# NOT for: Rozetka OAuth tests (those are in test_rozetka_oauth.py)

import csv
import io
import pytest

from services.scraper.allegro_scraper import AllegroProduct
from services.converter.converter_service import convert_to_rozetka, ConvertedProduct
from services.converter.template_generator import generate_rozetka_csv, ROZETKA_COLUMNS


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_product():
    return AllegroProduct(
        source_url="https://allegro.pl/oferta/buty-nike-12345",
        source_id="12345",
        title="Buty sportowe Nike Air Max 90",
        description="<p>Wygodne buty sportowe.</p>",
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
def sample_ai():
    return {
        "title_uk": "Спортивне взуття Nike Air Max 90",
        "description_uk": "Зручне спортивне взуття для щоденного використання.",
        "color_uk": "Чорний",
        "material_uk": "Шкіра",
        "bullet_points_uk": [
            "Зручна посадка",
            "Міцний матеріал",
            "Стильний дизайн",
            "Для щоденного використання",
            "Амортизація Nike Air",
        ],
    }


# ── convert_to_rozetka ───────────────────────────────────────────────

class TestConvertToRozetka:

    def test_basic_fields(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        f = result.fields

        assert result.marketplace == "rozetka"
        assert f["ean"] == "5901234567890"
        assert f["sku"] == "ALG-12345"
        assert f["condition"] == "new"

    def test_ukrainian_title(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert result.fields["title"] == "Спортивне взуття Nike Air Max 90"

    def test_ukrainian_description(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert "Зручне" in result.fields["description"]

    def test_price_uah_conversion(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {}, uah_rate=9.5)
        # 399.99 * 9.5 = ~3799.91
        assert float(result.fields["price"]) == pytest.approx(3799.91, abs=1.0)

    def test_currency_uah(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert result.fields["currency"] == "UAH"

    def test_images_mapped(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        f = result.fields
        assert f["image_1"] == "https://img.allegro.pl/1.jpg"
        assert f["image_2"] == "https://img.allegro.pl/2.jpg"

    def test_bullet_points_uk(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert result.fields["bullet_point_1"] == "Зручна посадка"
        assert result.fields["bullet_point_5"] == "Амортизація Nike Air"

    def test_brand_and_manufacturer(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert result.fields["brand"] == "Nike"
        assert result.fields["manufacturer"] == "Nike Inc."

    def test_weight_parsed(self, sample_product, sample_ai):
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert result.fields["weight_kg"] != ""

    def test_title_truncated_to_150(self, sample_product, sample_ai):
        sample_ai["title_uk"] = "A" * 200
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert len(result.fields["title"]) <= 150

    def test_empty_ai_fallback(self, sample_product):
        """WHY: When AI returns empty, should fall back to Polish title."""
        result = convert_to_rozetka(sample_product, {}, {})
        assert result.fields["title"] == "Buty sportowe Nike Air Max 90"
        assert result.fields["brand"] == "Nike"

    def test_missing_ean_warning(self, sample_product, sample_ai):
        sample_product.ean = ""
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert any("EAN" in w for w in result.warnings)

    def test_missing_brand_warning(self, sample_product, sample_ai):
        sample_product.brand = ""
        sample_product.manufacturer = ""
        sample_product.parameters = {}
        result = convert_to_rozetka(sample_product, sample_ai, {})
        assert any("Brand" in w for w in result.warnings)


# ── generate_rozetka_csv ─────────────────────────────────────────────

class TestGenerateRozetkaCsv:

    def test_csv_has_headers(self, sample_product, sample_ai):
        product = convert_to_rozetka(sample_product, sample_ai, {})
        csv_bytes = generate_rozetka_csv([product])
        text = csv_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        assert set(ROZETKA_COLUMNS).issubset(set(reader.fieldnames))

    def test_csv_has_data_row(self, sample_product, sample_ai):
        product = convert_to_rozetka(sample_product, sample_ai, {})
        csv_bytes = generate_rozetka_csv([product])
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
        assert len(rows) == 1
        assert rows[0]["ean"] == "5901234567890"

    def test_csv_skips_error_products(self, sample_product, sample_ai):
        good = convert_to_rozetka(sample_product, sample_ai, {})
        bad = ConvertedProduct(source_url="x", marketplace="rozetka", error="fail")
        csv_bytes = generate_rozetka_csv([good, bad])
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
        assert len(rows) == 1

    def test_csv_utf8_cyrillic(self, sample_product, sample_ai):
        """WHY: Rozetka uses Ukrainian — CSV must handle Cyrillic correctly."""
        product = convert_to_rozetka(sample_product, sample_ai, {})
        csv_bytes = generate_rozetka_csv([product])
        text = csv_bytes.decode("utf-8")
        assert "Спортивне" in text
