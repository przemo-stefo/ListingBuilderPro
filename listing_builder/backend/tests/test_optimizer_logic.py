# tests/test_optimizer_logic.py
# Purpose: Unit tests for optimizer pure-logic functions (no LLM, no DB)
# NOT for: Integration tests or anything that needs Groq/Supabase

import pytest
from services.optimizer_service import (
    _prepare_keywords,
    _extract_root_words,
    _pack_backend_keywords,
    _calculate_coverage,
    _find_missing_keywords,
    _check_compliance,
    _sanitize_llm_input,
    _strip_promo_words,
    _get_limits,
    _detect_language,
)


# --- Fixtures ---

@pytest.fixture
def keywords_with_volume():
    return [
        {"phrase": "trinkflasche edelstahl", "search_volume": 5000},
        {"phrase": "wasserflasche 1 liter", "search_volume": 3000},
        {"phrase": "thermosflasche sport", "search_volume": 2000},
        {"phrase": "trinkflasche bpa frei", "search_volume": 1800},
        {"phrase": "edelstahl wasserflasche", "search_volume": 1500},
        {"phrase": "isolierflasche kinder", "search_volume": 1200},
        {"phrase": "sportflasche auslaufsicher", "search_volume": 900},
        {"phrase": "vakuumflasche camping", "search_volume": 700},
        {"phrase": "thermoskanne wandern", "search_volume": 500},
        {"phrase": "trinkflasche schule", "search_volume": 300},
    ]


@pytest.fixture
def full_listing_text():
    return (
        "AquaPure Trinkflasche Edelstahl 1 Liter - BPA Frei Wasserflasche Sport "
        "Premium Edelstahl Trinkflasche BPA frei Thermosflasche Sport outdoor "
        "Wasserflasche 1 Liter auslaufsicher isolierflasche kinder vakuumflasche "
        "camping thermoskanne wandern sportflasche trinkflasche schule"
    )


# --- _prepare_keywords ---

class TestPrepareKeywords:
    def test_sorts_by_volume_desc(self, keywords_with_volume):
        all_kw, _, _, _ = _prepare_keywords(keywords_with_volume)
        volumes = [k["search_volume"] for k in all_kw]
        assert volumes == sorted(volumes, reverse=True)

    def test_tier_sizes(self, keywords_with_volume):
        _, t1, t2, t3 = _prepare_keywords(keywords_with_volume)
        assert len(t1) == 3   # 30% of 10
        assert len(t2) == 4   # 40% of 10
        assert len(t3) == 3   # remaining 30%
        assert len(t1) + len(t2) + len(t3) == 10

    def test_tier1_has_highest_volume(self, keywords_with_volume):
        _, t1, t2, _ = _prepare_keywords(keywords_with_volume)
        min_t1_vol = min(k["search_volume"] for k in t1)
        max_t2_vol = max(k["search_volume"] for k in t2)
        assert min_t1_vol >= max_t2_vol

    def test_single_keyword(self):
        kws = [{"phrase": "test", "search_volume": 100}]
        all_kw, t1, t2, t3 = _prepare_keywords(kws)
        assert len(t1) >= 1
        assert len(all_kw) == 1


# --- _extract_root_words ---

class TestExtractRootWords:
    def test_extracts_unique_words(self, keywords_with_volume):
        roots = _extract_root_words(keywords_with_volume)
        words = [r["word"] for r in roots]
        assert "trinkflasche" in words
        assert "edelstahl" in words

    def test_aggregates_volume(self, keywords_with_volume):
        roots = _extract_root_words(keywords_with_volume)
        root_dict = {r["word"]: r["total_volume"] for r in roots}
        # "trinkflasche" appears in 3 phrases: 5000 + 1800 + 300 = 7100
        assert root_dict.get("trinkflasche", 0) == 7100

    def test_skips_short_words(self):
        kws = [{"phrase": "a b cd ef", "search_volume": 100}]
        roots = _extract_root_words(kws)
        words = [r["word"] for r in roots]
        assert "a" not in words
        assert "b" not in words
        assert "cd" in words

    def test_max_20_roots(self):
        kws = [{"phrase": f"word{i}", "search_volume": i} for i in range(30)]
        roots = _extract_root_words(kws)
        assert len(roots) <= 20


# --- _pack_backend_keywords ---

class TestPackBackendKeywords:
    def test_respects_byte_limit(self, keywords_with_volume):
        packed = _pack_backend_keywords(keywords_with_volume, "listing text", 50)
        assert len(packed.encode("utf-8")) <= 50

    def test_zero_limit_returns_empty(self, keywords_with_volume):
        assert _pack_backend_keywords(keywords_with_volume, "", 0) == ""

    def test_skips_words_already_in_listing(self):
        kws = [{"phrase": "hello world", "search_volume": 100}]
        packed = _pack_backend_keywords(kws, "hello world already here", 249)
        # "hello" and "world" are in listing, so they shouldn't be packed
        packed_words = packed.lower().split()
        assert "hello" not in packed_words
        assert "world" not in packed_words

    def test_llm_suggestions_added(self):
        kws = [{"phrase": "test phrase", "search_volume": 100}]
        packed = _pack_backend_keywords(kws, "test phrase already covered", 249,
                                         llm_suggestions="synonym related extra")
        assert "synonym" in packed.lower()
        assert "related" in packed.lower()

    def test_llm_suggestions_skip_duplicates(self):
        kws = [{"phrase": "hello", "search_volume": 100}]
        packed = _pack_backend_keywords(kws, "hello world", 249,
                                         llm_suggestions="hello world newterm")
        packed_lower = packed.lower()
        # "hello" and "world" already in listing, only "newterm" should be added
        assert "newterm" in packed_lower


# --- _calculate_coverage ---

class TestCalculateCoverage:
    def test_full_coverage(self, keywords_with_volume, full_listing_text):
        pct, _, mode = _calculate_coverage(keywords_with_volume, full_listing_text)
        assert pct >= 90
        assert mode == "EXCELLENT"

    def test_zero_coverage(self, keywords_with_volume):
        pct, _, mode = _calculate_coverage(keywords_with_volume, "completely unrelated text xyz")
        assert pct < 20

    def test_empty_keywords(self):
        pct, _, mode = _calculate_coverage([], "some text")
        assert pct == 0
        assert mode == "NONE"

    def test_exact_match_counted(self):
        kws = [{"phrase": "exact match", "search_volume": 100}]
        _, exact, _ = _calculate_coverage(kws, "this has exact match in it")
        assert exact == 1

    def test_coverage_modes(self):
        # WHY: Test all threshold boundaries
        kws = [{"phrase": f"kw{i}", "search_volume": 100} for i in range(10)]
        text_90 = " ".join(f"kw{i}" for i in range(9))  # 9/10 = 90%
        text_70 = " ".join(f"kw{i}" for i in range(7))  # 7/10 = 70%
        text_50 = " ".join(f"kw{i}" for i in range(5))  # 5/10 = 50%
        text_30 = " ".join(f"kw{i}" for i in range(3))  # 3/10 = 30%

        assert _calculate_coverage(kws, text_90)[2] == "EXCELLENT"
        assert _calculate_coverage(kws, text_70)[2] == "GOOD"
        assert _calculate_coverage(kws, text_50)[2] == "MODERATE"
        assert _calculate_coverage(kws, text_30)[2] == "LOW"


# --- _find_missing_keywords ---

class TestFindMissingKeywords:
    def test_finds_missing(self, keywords_with_volume):
        missing = _find_missing_keywords(keywords_with_volume, "trinkflasche edelstahl")
        phrases = [k["phrase"] for k in keywords_with_volume]
        assert len(missing) < len(phrases)  # At least one covered
        assert len(missing) > 0  # Not all covered

    def test_none_missing_when_all_covered(self, keywords_with_volume, full_listing_text):
        missing = _find_missing_keywords(keywords_with_volume, full_listing_text)
        assert len(missing) == 0


# --- _check_compliance ---

class TestCheckCompliance:
    def test_pass_for_clean_listing(self):
        # WHY: "BPA frei" not "BPA free" — "free" is a promo word that triggers compliance failure
        result = _check_compliance(
            title="AquaPure Trinkflasche Edelstahl 1L",
            bullets=["Premium quality", "BPA frei", "Leakproof", "Durable", "Easy clean"],
            description="Great product",
            brand="AquaPure",
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert result["status"] == "PASS"
        assert result["error_count"] == 0

    def test_title_too_long(self):
        result = _check_compliance(
            title="A" * 201,
            bullets=["b"] * 5,
            description="",
            brand="A" * 10,
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert result["status"] == "FAIL"
        assert any("Title exceeds" in e for e in result["errors"])

    def test_promo_word_detected(self):
        result = _check_compliance(
            title="AquaPure Bestseller Flasche",
            bullets=["Great product"],
            description="",
            brand="AquaPure",
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert result["status"] == "FAIL"
        assert any("bestseller" in e.lower() for e in result["errors"])

    def test_forbidden_char_detected(self):
        result = _check_compliance(
            title="AquaPure Flasche! Amazing",
            bullets=["ok"],
            description="",
            brand="AquaPure",
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert any("!" in e for e in result["errors"])

    def test_brand_position_warning(self):
        result = _check_compliance(
            title="Some Product That Doesn't Start With Brand Name AquaPure",
            bullets=["ok"],
            description="",
            brand="AquaPure",
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert result["warning_count"] > 0

    def test_bullet_too_long(self):
        result = _check_compliance(
            title="AquaPure Product",
            bullets=["x" * 501],
            description="",
            brand="AquaPure",
            limits={"title": 200, "bullet": 500, "backend": 249},
        )
        assert any("Bullet" in e for e in result["errors"])


# --- _sanitize_llm_input ---

class TestSanitizeLlmInput:
    def test_strips_control_chars(self):
        assert "\x00" not in _sanitize_llm_input("hello\x00world")

    def test_collapses_newlines(self):
        result = _sanitize_llm_input("a\n\n\n\n\nb")
        assert "\n\n\n" not in result

    def test_truncates_at_1000(self):
        assert len(_sanitize_llm_input("x" * 2000)) == 1000

    def test_preserves_normal_text(self):
        assert _sanitize_llm_input("Normal product title") == "Normal product title"


# --- _strip_promo_words ---

class TestStripPromoWords:
    def test_strips_bestseller(self):
        assert "bestseller" not in _strip_promo_words("The Bestseller Product").lower()

    def test_preserves_normal_words(self):
        assert _strip_promo_words("Premium Quality Product") == "Premium Quality Product"

    def test_no_double_spaces(self):
        result = _strip_promo_words("The Best Seller Product Here")
        assert "  " not in result

    def test_word_boundary(self):
        """'deal' inside 'ideal' should NOT be stripped."""
        assert "ideal" in _strip_promo_words("An ideal product")


# --- Marketplace helpers ---

class TestGetLimits:
    def test_known_marketplace(self):
        limits = _get_limits("amazon_de")
        assert limits["title"] == 200
        assert limits["backend"] == 249

    def test_unknown_falls_back(self):
        limits = _get_limits("unknown_marketplace")
        assert limits["title"] == 200  # Falls back to amazon_de

    def test_ebay_different_limits(self):
        limits = _get_limits("ebay_de")
        assert limits["title"] == 80
        assert limits["backend"] == 0


class TestDetectLanguage:
    def test_explicit_overrides(self):
        assert _detect_language("amazon_de", "en") == "en"

    def test_marketplace_default(self):
        assert _detect_language("amazon_de", None) == "de"
        assert _detect_language("amazon_com", None) == "en"
        assert _detect_language("amazon_pl", None) == "pl"
