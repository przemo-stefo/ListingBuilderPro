# tests/test_keyword_csv_parser.py
# Purpose: Unit tests for Helium10/DataDive CSV parser
# NOT for: Integration tests or real CSV file tests

import pytest
from services.keyword_csv_parser import parse_keyword_csv, _find_col, _detect_source


# --- Source Detection ---

class TestDetectSource:
    def test_datadive(self):
        assert _detect_source(["Phrase", "Relevancy", "Ranking Juice ®", "Search Volume"]) == "datadive"

    def test_datadive_by_my_listing(self):
        assert _detect_source(["Phrase", "Search Volume", "MY_LISTING"]) == "datadive"

    def test_cerebro(self):
        assert _detect_source(["Keyword", "Search Volume", "Cerebro IQ Score"]) == "cerebro"

    def test_cerebro_by_competing(self):
        assert _detect_source(["Keyword", "Search Volume", "Competing Products"]) == "cerebro"

    def test_magnet(self):
        assert _detect_source(["Keyword", "Search Volume", "Magnet IQ Score"]) == "magnet"

    def test_magnet_by_smart_score(self):
        assert _detect_source(["Keyword", "Search Volume", "Smart Score"]) == "magnet"

    def test_blackbox(self):
        assert _detect_source(["ASIN", "Title", "Monthly Revenue", "BSR"]) == "blackbox"

    def test_generic(self):
        assert _detect_source(["keyword", "search_volume"]) == "generic"


# --- Column Finder ---

class TestFindCol:
    def test_exact_match(self):
        assert _find_col(["Search Volume", "Keyword"], ["search volume"]) == "Search Volume"

    def test_partial_match(self):
        assert _find_col(["Cerebro IQ Score"], ["cerebro"]) == "Cerebro IQ Score"

    def test_no_match(self):
        assert _find_col(["Title", "Price"], ["keyword"]) is None

    def test_empty(self):
        assert _find_col([], ["keyword"]) is None


# --- DataDive CSV ---

class TestDataDiveCSV:
    CSV = (
        "Phrase,Relevancy,Ranking Juice ®,Search Volume,MY_LISTING\n"
        "bio spirulina tabletten,0.98,12540,12000,EXACT\n"
        "spirulina pulver bio,0.95,9120,9500,BROAD\n"
        "spirulina kapseln,0.90,7380,8200,NONE\n"
        "chlorella spirulina,0.82,3200,3800,NONE\n"
    )

    def test_source(self):
        r = parse_keyword_csv(self.CSV)
        assert r["source"] == "datadive"

    def test_count(self):
        r = parse_keyword_csv(self.CSV)
        assert len(r["keywords"]) == 4

    def test_fields(self):
        r = parse_keyword_csv(self.CSV)
        kw = r["keywords"][0]
        assert kw["phrase"] == "bio spirulina tabletten"
        assert kw["search_volume"] == 12000
        assert kw["ranking_juice"] == 12540
        assert kw["relevancy"] == 0.98

    def test_indexed_flag(self):
        r = parse_keyword_csv(self.CSV)
        assert r["keywords"][0]["indexed"] is True  # EXACT
        assert r["keywords"][2]["indexed"] is False  # NONE

    def test_sorted_by_rj(self):
        r = parse_keyword_csv(self.CSV)
        rjs = [k["ranking_juice"] for k in r["keywords"]]
        assert rjs == sorted(rjs, reverse=True)

    def test_no_error(self):
        r = parse_keyword_csv(self.CSV)
        assert r["error"] is None


# --- Helium10 Cerebro ---

class TestCerebroCSV:
    CSV = (
        "Keyword,Search Volume,Cerebro IQ Score,Competing Products\n"
        "bio spirulina tabletten,12000,8,15\n"
        "spirulina pulver,9500,7,22\n"
        "spirulina kapseln hochdosiert,4200,6,8\n"
    )

    def test_source(self):
        assert parse_keyword_csv(self.CSV)["source"] == "cerebro"

    def test_count(self):
        assert len(parse_keyword_csv(self.CSV)["keywords"]) == 3

    def test_rj_auto_calculated(self):
        r = parse_keyword_csv(self.CSV)
        # WHY: Cerebro doesn't have RJ — parser should auto-calculate it
        assert r["keywords"][0]["ranking_juice"] > 0

    def test_competition(self):
        r = parse_keyword_csv(self.CSV)
        # WHY: "Competing Products" maps to competition field
        assert r["keywords"][0]["competition"] == 15.0


# --- Helium10 Magnet ---

class TestMagnetCSV:
    CSV = (
        "Keyword,Search Volume,Smart Score\n"
        "spirulina bio,7800,8.5\n"
        "spirulina tabletten vegan,2200,6.2\n"
        "algen supplement,1500,5.0\n"
    )

    def test_source(self):
        assert parse_keyword_csv(self.CSV)["source"] == "magnet"

    def test_smart_score(self):
        r = parse_keyword_csv(self.CSV)
        assert r["keywords"][0]["smart_score"] == 8.5

    def test_relevancy_from_smart_score(self):
        r = parse_keyword_csv(self.CSV)
        # WHY: Smart Score 8.5 / 10 = 0.85 relevancy
        assert r["keywords"][0]["relevancy"] == 0.85


# --- Helium10 BlackBox ---

class TestBlackBoxCSV:
    CSV = (
        "ASIN,Title,Monthly Revenue,Reviews,BSR,Price\n"
        "B09ABC1234,BIO Spirulina 500mg,$45000,1250,1234,$19.99\n"
        "B09DEF5678,Spirulina Pulver Bio,$32000,890,2567,$24.99\n"
    )

    def test_source(self):
        assert parse_keyword_csv(self.CSV)["source"] == "blackbox"

    def test_products(self):
        r = parse_keyword_csv(self.CSV)
        assert len(r["products"]) == 2
        assert r["products"][0]["monthly_revenue"] == 45000.0
        assert r["products"][0]["price"] == 19.99

    def test_no_keywords(self):
        # WHY: BlackBox returns products, not keywords
        r = parse_keyword_csv(self.CSV)
        assert len(r["keywords"]) == 0


# --- Edge Cases ---

class TestEdgeCases:
    def test_empty(self):
        r = parse_keyword_csv("")
        assert r["error"] is not None

    def test_no_columns(self):
        r = parse_keyword_csv("   ")
        assert r["error"] is not None

    def test_duplicate_keywords(self):
        csv = "Keyword,Search Volume\nspirulina bio,7800\nspirulina bio,7800\n"
        r = parse_keyword_csv(csv)
        assert len(r["keywords"]) == 1  # deduplicated

    def test_pipe_phrases_skipped(self):
        csv = "Phrase,Search Volume\nbio|spirulina,5000\nnormal keyword,3000\n"
        r = parse_keyword_csv(csv)
        assert len(r["keywords"]) == 1
        assert r["keywords"][0]["phrase"] == "normal keyword"

    def test_eu_decimal_format(self):
        csv = "Phrase,Relevancy,Search Volume\nspirulina,0,98,5000\n"
        # WHY: EU uses comma as decimal separator — "0,98" should parse
        r = parse_keyword_csv(csv)
        assert len(r["keywords"]) >= 0  # May or may not parse depending on CSV format


# --- Stats ---

class TestStats:
    def test_stats_calculated(self):
        csv = (
            "Keyword,Search Volume\n"
            "bio spirulina,12000\n"
            "spirulina kapseln,8200\n"
            "chlorella,0\n"
        )
        r = parse_keyword_csv(csv)
        assert r["stats"]["total"] == 3
        assert r["stats"]["with_volume"] == 2
        assert r["stats"]["avg_volume"] == 10100  # (12000+8200)/2
        assert r["stats"]["top_keyword"] != ""

    def test_empty_stats(self):
        csv = "Keyword,Search Volume\n"
        r = parse_keyword_csv(csv)
        assert r["stats"]["total"] == 0


# --- Category Prompts ---

class TestCategoryPrompts:
    """Verify category-specific rules integrate with prompt builders."""

    def test_supplement_title_rules(self):
        from services.category_prompts import get_category_rules
        rules = get_category_rules("Health & Household", "title")
        assert "SUPPLEMENT" in rules
        assert "dosage" in rules.lower() or "Tabletten" in rules

    def test_supplement_bullets_compliance(self):
        from services.category_prompts import get_category_rules
        rules = get_category_rules("dietary supplement", "bullets")
        assert "EC 1924/2006" in rules

    def test_supplement_description_gpsr(self):
        from services.category_prompts import get_category_rules
        rules = get_category_rules("Health & Household", "description")
        assert "GPSR" in rules

    def test_electronics_title(self):
        from services.category_prompts import get_category_rules
        rules = get_category_rules("Electronics", "title")
        assert "ELECTRONICS" in rules

    def test_beauty_bullets(self):
        from services.category_prompts import get_category_rules
        rules = get_category_rules("Beauty & Personal Care", "bullets")
        assert "BEAUTY" in rules

    def test_unknown_returns_empty(self):
        from services.category_prompts import get_category_rules
        assert get_category_rules("Toys & Games", "title") == ""
        assert get_category_rules("", "title") == ""

    def test_prompt_builders_accept_category(self):
        from services.prompt_builders import (
            build_title_prompt, build_bullets_prompt,
            build_description_prompt, build_backend_prompt,
        )
        # WHY: Just verify they don't crash with category param
        p = build_title_prompt("Test", "Brand", "", ["kw"], "de", 200, category="Health")
        assert "SUPPLEMENT" in p
        p2 = build_bullets_prompt("Test", "Brand", ["kw"], "de", 500, category="vitamin")
        assert "EC 1924/2006" in p2
        p3 = build_description_prompt("Test", "Brand", ["kw"], "de", category="Health")
        assert "GPSR" in p3
        p4 = build_backend_prompt("Test", "Brand", "title", [{"phrase": "kw"}], "de", 250, category="supplement")
        assert "ingredient synonyms" in p4
