# tests/test_datadive_services.py
# Purpose: Unit tests for DataDive integration services (anti-stuffing, PPC, grey market, keyword placement)
# NOT for: Integration tests or anything that needs Groq/Supabase

import pytest
from services.anti_stuffing_service import (
    run_anti_stuffing_check,
    validate_keyword_density,
    validate_word_repetition,
    _word_counts,
)
from services.ppc_service import (
    generate_ppc_recommendations,
    _detect_competitor_terms,
    _estimate_budget,
)
from services.grey_market_service import score_grey_market
from services.keyword_placement_service import (
    prepare_keywords_by_rj,
    prepare_keywords_with_fallback,
    get_bullet_count,
    get_bullet_limit,
)
from services.coverage_service import (
    calculate_multi_tier_coverage,
    extract_words,
    keyword_covered,
)


# --- Fixtures ---

@pytest.fixture
def sample_keywords():
    """12 keywords sorted by search_volume desc."""
    return [
        {"phrase": "water bottle", "search_volume": 12000},
        {"phrase": "stainless steel bottle", "search_volume": 8000},
        {"phrase": "insulated water bottle", "search_volume": 6000},
        {"phrase": "travel bottle", "search_volume": 4000},
        {"phrase": "sports bottle", "search_volume": 3500},
        {"phrase": "metal water bottle", "search_volume": 3000},
        {"phrase": "thermos bottle", "search_volume": 2500},
        {"phrase": "vacuum bottle", "search_volume": 2000},
        {"phrase": "flask water", "search_volume": 1500},
        {"phrase": "bpa free bottle", "search_volume": 1200},
        {"phrase": "trinkflasche edelstahl", "search_volume": 1100},
        {"phrase": "isolierflasche", "search_volume": 900},
    ]


# ==================== Anti-Stuffing ====================

class TestWordCounts:
    def test_counts_words(self):
        counts = _word_counts("bottle water bottle test")
        assert counts["bottle"] == 2
        assert counts["water"] == 1
        assert counts["test"] == 1

    def test_ignores_stop_words(self):
        counts = _word_counts("the bottle and the water for the test")
        assert "the" not in counts
        assert "and" not in counts
        assert "for" not in counts

    def test_ignores_german_stop_words(self):
        counts = _word_counts("die Flasche und der Deckel für den Transport")
        assert "die" not in counts
        assert "und" not in counts
        assert "für" not in counts
        assert "den" not in counts
        assert "flasche" in counts

    def test_ignores_single_char(self):
        counts = _word_counts("a b c bottle")
        assert "a" not in counts
        assert "b" not in counts
        assert "bottle" in counts


class TestValidateKeywordDensity:
    def test_clean_text_passes(self):
        text = "Premium stainless steel water bottle for outdoor sports and hiking adventures"
        warnings = validate_keyword_density(text)
        assert len(warnings) == 0

    def test_stuffed_text_warns(self):
        # WHY: "bottle" appears 5x out of ~12 words = ~42% density
        text = "bottle bottle bottle bottle bottle water steel"
        warnings = validate_keyword_density(text)
        assert any("bottle" in w for w in warnings)

    def test_empty_text(self):
        assert validate_keyword_density("") == []


class TestValidateWordRepetition:
    def test_clean_title(self):
        warnings = validate_word_repetition(
            "HYDROFLASK Stainless Steel Water Bottle 750ml",
            ["Premium quality", "BPA free material"],
        )
        title_warnings = [w for w in warnings if "Title" in w]
        assert len(title_warnings) == 0

    def test_title_repetition(self):
        # WHY: "bottle" 3x in title exceeds TITLE_MAX_REPEATS=2
        warnings = validate_word_repetition(
            "Bottle Water Bottle Steel Bottle",
            ["Some bullet"],
        )
        title_warnings = [w for w in warnings if "Title" in w and "bottle" in w.lower()]
        assert len(title_warnings) > 0

    def test_listing_repetition(self):
        # WHY: "bottle" 6x across title+bullets exceeds LISTING_MAX_REPEATS=5
        warnings = validate_word_repetition(
            "Water Bottle Premium",
            ["Bottle design", "Steel bottle", "Best bottle ever", "Bottle holder", "Another bottle"],
        )
        listing_warnings = [w for w in warnings if "Listing" in w and "bottle" in w.lower()]
        assert len(listing_warnings) > 0


class TestRunAntiStuffingCheck:
    def test_combined_check(self):
        warnings = run_anti_stuffing_check(
            title="Normal Product Title",
            bullets=["Good bullet one", "Good bullet two"],
            description="A nice product description",
        )
        assert isinstance(warnings, list)

    def test_returns_warnings_for_stuffed_content(self):
        warnings = run_anti_stuffing_check(
            title="Bottle Bottle Bottle Bottle",
            bullets=["Bottle bottle", "More bottle text", "Bottle again", "Bottle five"],
            description="The bottle is a bottle among bottles",
        )
        assert len(warnings) > 0


# ==================== PPC Service ====================

class TestGeneratePPCRecommendations:
    def test_returns_all_match_types(self, sample_keywords):
        listing = "water bottle stainless steel insulated travel sports"
        result = generate_ppc_recommendations(sample_keywords, listing)
        assert "exact_match" in result
        assert "phrase_match" in result
        assert "broad_match" in result
        assert "negative_suggestions" in result
        assert "summary" in result

    def test_exact_match_has_top_keywords(self, sample_keywords):
        listing = "water bottle stainless steel insulated travel sports metal thermos vacuum flask bpa"
        result = generate_ppc_recommendations(sample_keywords, listing)
        exact_phrases = [k["phrase"] for k in result["exact_match"]]
        assert "water bottle" in exact_phrases

    def test_indexed_flag(self, sample_keywords):
        # WHY: Keywords present in listing should be flagged as indexed
        listing = "water bottle stainless steel"
        result = generate_ppc_recommendations(sample_keywords, listing)
        for kw in result["exact_match"]:
            if kw["phrase"] == "water bottle":
                assert kw["indexed"] is True
                break

    def test_summary_counts(self, sample_keywords):
        result = generate_ppc_recommendations(sample_keywords, "some listing text")
        summary = result["summary"]
        assert summary["exact_count"] >= 0
        assert summary["phrase_count"] >= 0
        assert summary["broad_count"] >= 0
        assert isinstance(summary["estimated_daily_budget_usd"], float)

    def test_empty_keywords(self):
        result = generate_ppc_recommendations([], "listing text")
        assert result["summary"]["exact_count"] == 0


class TestDetectCompetitorTerms:
    def test_flags_single_word_non_generic(self):
        kws = [
            {"phrase": "hydroflask", "search_volume": 5000},
            {"phrase": "bottle", "search_volume": 3000},
        ]
        suspects = _detect_competitor_terms(kws)
        assert "hydroflask" in suspects
        # WHY: "bottle" is in generic_words list — should NOT be flagged
        assert "bottle" not in suspects

    def test_skips_multi_word_phrases(self):
        kws = [{"phrase": "some brand name", "search_volume": 1000}]
        suspects = _detect_competitor_terms(kws)
        assert len(suspects) == 0

    def test_skips_short_words(self):
        kws = [{"phrase": "bpa", "search_volume": 1000}]
        suspects = _detect_competitor_terms(kws)
        assert "bpa" not in suspects


class TestEstimateBudget:
    def test_returns_float(self):
        kws = [{"phrase": "test", "search_volume": 30000}]
        result = _estimate_budget(kws, [])
        assert isinstance(result, float)
        assert result > 0

    def test_zero_volume(self):
        kws = [{"phrase": "test", "search_volume": 0}]
        assert _estimate_budget(kws, []) == 0


# ==================== Grey Market Service ====================

class TestGreyMarketScoring:
    def test_low_risk(self):
        result = score_grey_market(
            unauthorized_sellers=0, buy_box_rate=100.0,
            suppressed_asins=0, hijack_reports=0,
        )
        assert result["score"] == 0
        assert result["risk_level"] == "LOW"

    def test_critical_risk(self):
        result = score_grey_market(
            unauthorized_sellers=5, buy_box_rate=50.0,
            suppressed_asins=3, hijack_reports=3,
        )
        assert result["risk_level"] == "CRITICAL"
        assert result["score"] >= 70

    def test_moderate_risk(self):
        result = score_grey_market(
            unauthorized_sellers=1, buy_box_rate=85.0,
            suppressed_asins=0, hijack_reports=0,
        )
        assert result["risk_level"] == "MODERATE"
        assert 20 <= result["score"] < 40

    def test_components_present(self):
        result = score_grey_market(unauthorized_sellers=2, buy_box_rate=80.0)
        components = result["components"]
        assert "unauthorized_sellers" in components
        assert "buy_box_erosion" in components
        assert "suppressed_asins" in components
        assert "hijack_reports" in components

    def test_score_capped_at_100(self):
        result = score_grey_market(
            unauthorized_sellers=10, buy_box_rate=0.0,
            suppressed_asins=10, hijack_reports=10,
        )
        assert result["score"] <= 100

    def test_hijack_reports_scaling(self):
        # WHY: Verify fix — 1 report = 10 pts, 2 reports = 20 pts (cap)
        r1 = score_grey_market(hijack_reports=1)
        r2 = score_grey_market(hijack_reports=2)
        r3 = score_grey_market(hijack_reports=3)
        assert r1["components"]["hijack_reports"] == 10
        assert r2["components"]["hijack_reports"] == 20
        assert r3["components"]["hijack_reports"] == 20  # capped


# ==================== Keyword Placement Service ====================

class TestGetBulletCount:
    def test_seller_5(self):
        assert get_bullet_count("seller") == 5

    def test_vendor_10(self):
        assert get_bullet_count("vendor") == 10

    def test_unknown_defaults_seller(self):
        assert get_bullet_count("unknown") == 5


class TestGetBulletLimit:
    def test_default_200(self):
        assert get_bullet_limit("") == 200
        assert get_bullet_limit("electronics") == 200

    def test_apparel_150(self):
        assert get_bullet_limit("apparel") == 150
        assert get_bullet_limit("Women's Clothing") == 150
        assert get_bullet_limit("shoes") == 150

    def test_case_insensitive(self):
        assert get_bullet_limit("JEWELRY") == 150
        assert get_bullet_limit("Fashion Accessories") == 150


class TestPrepareKeywordsByRJ:
    def test_seller_ranges(self, sample_keywords):
        all_kw, title, bullets, backend, desc = prepare_keywords_by_rj(sample_keywords, "seller")
        assert len(title) == 7  # range(0,7)
        assert len(bullets) == 5  # range(7,12) — only 5 left
        assert len(all_kw) == 12

    def test_vendor_ranges(self, sample_keywords):
        all_kw, title, bullets, backend, desc = prepare_keywords_by_rj(sample_keywords, "vendor")
        assert len(title) == 7  # range(0,7)
        assert len(bullets) == 5  # range(7,12) — only 5 left
        # WHY: With 12 keywords, vendor and seller bullets are same size
        # Difference only shows with >32 keywords

    def test_sorted_by_volume(self, sample_keywords):
        all_kw, _, _, _, _ = prepare_keywords_by_rj(sample_keywords)
        volumes = [k["search_volume"] for k in all_kw]
        assert volumes == sorted(volumes, reverse=True)

    def test_title_has_highest_volume(self, sample_keywords):
        _, title, bullets, _, _ = prepare_keywords_by_rj(sample_keywords)
        if title and bullets:
            min_title_vol = min(k["search_volume"] for k in title)
            max_bullet_vol = max(k["search_volume"] for k in bullets)
            assert min_title_vol >= max_bullet_vol


class TestPrepareKeywordsWithFallback:
    def test_returns_4_tuples(self, sample_keywords):
        result = prepare_keywords_with_fallback(sample_keywords)
        assert len(result) == 4  # (all, tier1, tier2, tier3)

    def test_tier3_merges_backend_and_desc(self, sample_keywords):
        # WHY: Fallback merges backend + description into tier3
        all_kw, t1, t2, t3 = prepare_keywords_with_fallback(sample_keywords)
        _, _, _, backend, desc = prepare_keywords_by_rj(sample_keywords)
        assert len(t3) == len(backend) + len(desc)


# ==================== Coverage Service (extended) ====================

class TestExtractWords:
    def test_extracts_words(self):
        words = extract_words("Hello World 750ml")
        assert "hello" in words
        assert "world" in words
        assert "750ml" in words

    def test_no_substring_matching(self):
        # WHY: This is the core fix — word set membership, not substring
        words = extract_words("capsule container")
        assert "cap" not in words
        assert "capsule" in words

    def test_handles_german_chars(self):
        words = extract_words("Trinkflasche für Kinder")
        assert "trinkflasche" in words
        assert "für" in words

    def test_handles_polish_chars(self):
        words = extract_words("butelka ze stali nierdzewnej")
        assert "butelka" in words
        assert "nierdzewnej" in words


class TestKeywordCovered:
    def test_full_match(self):
        word_set = {"water", "bottle", "steel"}
        assert keyword_covered("water bottle", word_set) is True

    def test_partial_match_above_threshold(self):
        # WHY: 2/3 words = 66.7% < 70% threshold
        word_set = {"water", "bottle"}
        assert keyword_covered("water bottle premium", word_set) is False

    def test_partial_match_at_threshold(self):
        # WHY: 7/10 = 70% = exactly at threshold
        word_set = {f"w{i}" for i in range(7)}
        phrase = " ".join(f"w{i}" for i in range(10))
        assert keyword_covered(phrase, word_set) is True

    def test_empty_phrase(self):
        assert keyword_covered("", {"word"}) is False


class TestMultiTierCoverage:
    def test_meets_target(self, sample_keywords):
        # WHY: All keywords present in full text → should meet 95% target
        full = " ".join(k["phrase"] for k in sample_keywords)
        result = calculate_multi_tier_coverage(sample_keywords, full, [], "", "")
        assert result["meets_target"] is True
        assert result["overall_pct"] >= 95

    def test_breakdown_structure(self, sample_keywords):
        result = calculate_multi_tier_coverage(
            sample_keywords, "water bottle", ["steel"], "flask", "insulated",
        )
        bd = result["breakdown"]
        assert all(k in bd for k in ["title_pct", "bullets_pct", "backend_pct", "description_pct"])

    def test_grade_excellent(self, sample_keywords):
        full = " ".join(k["phrase"] for k in sample_keywords)
        result = calculate_multi_tier_coverage(sample_keywords, full, [], "", "")
        assert result["overall_grade"] == "EXCELLENT"

    def test_grade_low(self, sample_keywords):
        result = calculate_multi_tier_coverage(sample_keywords, "xyz unrelated", [], "", "")
        assert result["overall_grade"] == "LOW"
