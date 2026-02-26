# backend/tests/test_amazon_tos_checker.py
# Purpose: Test Amazon TOS compliance checker — all violation categories
# NOT for: Optimizer scoring integration tests (that's test_optimizer_scoring.py)

import pytest
from services.amazon_tos_checker import check_amazon_tos


class TestNonAmazonSkip:
    """Non-Amazon marketplaces should skip all checks."""

    def test_allegro_returns_pass(self):
        result = check_amazon_tos("Anything!", [], "", "", "allegro")
        assert result["severity"] == "PASS"
        assert result["violation_count"] == 0

    def test_bol_returns_pass(self):
        result = check_amazon_tos("BEST SELLER!!", [], "buy now", "", "bol_com")
        assert result["severity"] == "PASS"


class TestCleanListing:
    """A compliant listing should pass all checks."""

    def test_clean_listing_passes(self):
        result = check_amazon_tos(
            title="BrandX - Stainless Steel Water Bottle 750ml Insulated",
            bullets=["Keeps drinks cold for 24 hours", "BPA-free material"],
            description="High quality water bottle for everyday use.",
            backend_keywords="water bottle thermos flask",
            marketplace="amazon_de",
        )
        assert result["severity"] == "PASS"
        assert result["violation_count"] == 0
        assert result["suppression_risk"] is False


class TestTitleFormat:
    """Title-specific violation detection."""

    def test_title_over_200_chars(self):
        long_title = "A" * 201
        result = check_amazon_tos(long_title, [], "", "", "amazon_de")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_length" in rules

    def test_title_exactly_200_chars_passes(self):
        title = "A" * 200
        result = check_amazon_tos(title, [], "", "", "amazon_de")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_length" not in rules

    def test_all_caps_words_detected(self):
        result = check_amazon_tos("BrandX PREMIUM STEEL Bottle", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_all_caps" in rules

    def test_short_caps_words_ignored(self):
        """Words <= 3 chars in CAPS (e.g. 'USB', 'LED') are acceptable."""
        result = check_amazon_tos("BrandX USB LED Cable 2m", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_all_caps" not in rules

    def test_word_repetition_over_2x(self):
        result = check_amazon_tos("water water water bottle", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_word_repetition" in rules

    def test_word_repetition_2x_is_ok(self):
        result = check_amazon_tos("water bottle water flask", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_word_repetition" not in rules

    def test_forbidden_chars_detected(self):
        result = check_amazon_tos("BrandX Water Bottle! #1", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_forbidden_chars" in rules

    def test_normal_chars_pass(self):
        result = check_amazon_tos("BrandX - Water Bottle, 750ml (Pack of 2)", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "title_forbidden_chars" not in rules


class TestProhibitedClaims:
    """Promotional, health, pesticide, drug, eco claim detection."""

    @pytest.mark.parametrize("phrase", ["best seller", "buy now", "free shipping", "angebot", "gratis"])
    def test_promo_phrases_detected(self, phrase):
        result = check_amazon_tos(f"BrandX {phrase} Bottle", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "promo_phrase" in rules

    @pytest.mark.parametrize("claim", ["cure", "weight loss", "detox", "immune booster"])
    def test_health_claims_detected(self, claim):
        result = check_amazon_tos("Title", [f"This product helps {claim}"], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "health_claim" in rules

    @pytest.mark.parametrize("claim", ["antibacterial", "kills bacteria", "disinfect"])
    def test_pesticide_claims_detected(self, claim):
        result = check_amazon_tos("Title", [f"Surface is {claim}"], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "pesticide_claim" in rules

    @pytest.mark.parametrize("kw", ["cbd", "thc", "kratom"])
    def test_drug_keywords_detected(self, kw):
        result = check_amazon_tos("Title", [], f"Contains {kw} extract", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "drug_keyword" in rules

    @pytest.mark.parametrize("claim", ["eco-friendly", "biodegradable", "carbon neutral"])
    def test_eco_claims_are_warnings(self, claim):
        result = check_amazon_tos("Title", [f"Made with {claim} materials"], "", "", "amazon")
        eco_v = [v for v in result["violations"] if v["rule"] == "eco_claim"]
        assert len(eco_v) >= 1
        assert eco_v[0]["severity"] == "WARNING"

    def test_claims_not_in_clean_text(self):
        """Normal product descriptions should not trigger false positives."""
        result = check_amazon_tos(
            "BrandX Stainless Steel Bottle 750ml",
            ["Keeps drinks cold 24h", "Durable construction"],
            "Great for outdoor activities.",
            "",
            "amazon_de",
        )
        assert result["violation_count"] == 0


class TestExternalReferences:
    """URLs, emails, phone numbers detection."""

    def test_url_detected(self):
        result = check_amazon_tos("Title", ["Visit https://example.com"], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "external_reference" in rules

    def test_www_detected(self):
        result = check_amazon_tos("Title", [], "See www.example.com", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "external_reference" in rules

    def test_email_detected(self):
        result = check_amazon_tos("Title", ["Contact us at support@brand.com"], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "external_reference" in rules

    def test_phone_detected(self):
        result = check_amazon_tos("Title", ["Call +48 123 456 789"], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "external_reference" in rules


class TestBackendKeywords:
    """Backend search terms validation."""

    def test_backend_over_250_bytes(self):
        kw = "a " * 130  # 260 bytes
        result = check_amazon_tos("Title", [], "", kw, "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "backend_byte_limit" in rules

    def test_backend_250_bytes_passes(self):
        kw = "a " * 124  # 248 bytes
        result = check_amazon_tos("Title", [], "", kw, "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "backend_byte_limit" not in rules

    def test_asin_detected(self):
        result = check_amazon_tos("Title", [], "", "alternative to B0ABCDEFGH", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "backend_asin" in rules

    def test_non_asin_passes(self):
        result = check_amazon_tos("Title", [], "", "bottle flask thermos", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "backend_asin" not in rules

    def test_subjective_words_are_warnings(self):
        result = check_amazon_tos("Title", [], "", "best amazing water bottle", "amazon")
        subj_v = [v for v in result["violations"] if v["rule"] == "backend_subjective"]
        assert len(subj_v) >= 2
        assert all(v["severity"] == "WARNING" for v in subj_v)

    def test_empty_backend_skipped(self):
        result = check_amazon_tos("Title", [], "", "", "amazon")
        rules = [v["rule"] for v in result["violations"]]
        assert "backend_byte_limit" not in rules
        assert "backend_asin" not in rules


class TestSeverityAggregation:
    """Overall severity is correctly determined from violations."""

    def test_suppression_gives_fail(self):
        result = check_amazon_tos("BUY NOW Product!", [], "", "", "amazon")
        assert result["severity"] == "FAIL"
        assert result["suppression_risk"] is True

    def test_warning_only_gives_warn(self):
        result = check_amazon_tos("Title", [], "", "best water bottle", "amazon")
        assert result["severity"] == "WARN"
        assert result["suppression_risk"] is False

    def test_no_violations_gives_pass(self):
        result = check_amazon_tos("BrandX Water Bottle 750ml", ["Good bullet"], "Nice desc", "", "amazon")
        assert result["severity"] == "PASS"
        assert result["suppression_risk"] is False
        assert result["violation_count"] == 0
