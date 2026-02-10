# tests/test_ranking_juice.py
# Purpose: Unit tests for Ranking Juice scoring algorithm
# NOT for: LLM, DB, or integration tests

import pytest
from services.ranking_juice_service import (
    calculate_ranking_juice,
    quick_ranking_juice,
    _coverage_score,
    _exact_match_score,
    _search_volume_score,
    _backend_efficiency,
    _structure_score,
)


# --- Fixtures ---

@pytest.fixture
def sample_keywords():
    return [
        {"phrase": "trinkflasche edelstahl", "search_volume": 5000},
        {"phrase": "wasserflasche 1 liter", "search_volume": 3000},
        {"phrase": "thermosflasche sport", "search_volume": 2000},
        {"phrase": "trinkflasche bpa frei", "search_volume": 1800},
        {"phrase": "edelstahl wasserflasche", "search_volume": 1500},
    ]


@pytest.fixture
def good_title():
    return "AquaPure Trinkflasche Edelstahl 1 Liter - BPA Frei Wasserflasche - Thermosflasche Sport Outdoor"


@pytest.fixture
def good_bullets():
    return [
        "PREMIUM EDELSTAHL - Doppelwandige Trinkflasche aus hochwertigem 18/8 Edelstahl, BPA frei und lebensmittelecht",
        "TEMPERATUR ISOLIERT - Hält Getränke 24 Stunden kalt oder 12 Stunden heiß, perfekte Thermosflasche für Sport",
        "AUSLAUFSICHER - Wasserflasche 1 Liter mit auslaufsicherem Deckel, ideal für Büro, Schule und Reisen",
        "UMWELTFREUNDLICH - Wiederverwendbare edelstahl Wasserflasche ersetzt hunderte Plastikflaschen pro Jahr",
        "UNIVERSELL EINSETZBAR - Sport Trinkflasche passt in jeden Rucksack und Getränkehalter, leicht zu reinigen",
    ]


# --- calculate_ranking_juice ---

class TestCalculateRankingJuice:
    def test_returns_required_keys(self, sample_keywords, good_title, good_bullets):
        result = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "outdoor camping")
        assert "score" in result
        assert "grade" in result
        assert "verdict" in result
        assert "components" in result
        assert "weights" in result

    def test_score_range(self, sample_keywords, good_title, good_bullets):
        result = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "outdoor camping")
        assert 0 <= result["score"] <= 100

    def test_grade_a_plus_for_excellent(self, sample_keywords, good_title, good_bullets):
        result = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "outdoor camping wandern")
        assert result["score"] >= 80
        assert result["grade"] in ("A+", "A")

    def test_grade_d_for_empty_listing(self, sample_keywords):
        result = calculate_ranking_juice(sample_keywords, "", [], "")
        assert result["grade"] == "D"
        assert result["score"] < 60

    def test_weights_sum_to_one(self, sample_keywords, good_title, good_bullets):
        result = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "")
        total = sum(result["weights"].values())
        assert abs(total - 1.0) < 0.001

    def test_components_all_present(self, sample_keywords, good_title, good_bullets):
        result = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "")
        expected = {"keyword_coverage", "exact_match_density", "search_volume_weighted",
                    "backend_efficiency", "structure_quality"}
        assert set(result["components"].keys()) == expected


class TestQuickRankingJuice:
    def test_returns_int(self, sample_keywords, good_title, good_bullets):
        score = quick_ranking_juice(sample_keywords, good_title, good_bullets, "")
        assert isinstance(score, int)

    def test_matches_full_score(self, sample_keywords, good_title, good_bullets):
        quick = quick_ranking_juice(sample_keywords, good_title, good_bullets, "outdoor")
        full = calculate_ranking_juice(sample_keywords, good_title, good_bullets, "outdoor")
        assert quick == int(full["score"])


# --- Component tests ---

class TestCoverageScore:
    def test_empty_keywords(self):
        assert _coverage_score([], "title", ["bullet"], "", "") == 0

    def test_all_covered(self):
        kws = [{"phrase": "hello world", "search_volume": 100}]
        score = _coverage_score(kws, "hello world title", [], "", "")
        assert score > 90

    def test_none_covered(self):
        kws = [{"phrase": "xyz abc", "search_volume": 100}]
        score = _coverage_score(kws, "completely different text", [], "", "")
        assert score < 10

    def test_partial_70pct_threshold(self):
        """3/4 words = 75% > 70% threshold → counted as covered."""
        kws = [{"phrase": "a b c d", "search_volume": 100}]
        score = _coverage_score(kws, "a b c", [], "", "")
        assert score > 90  # WHY: 75% word overlap passes the 70% gate


class TestExactMatchScore:
    def test_phrase_in_title_worth_more(self):
        kws = [{"phrase": "edelstahl flasche", "search_volume": 100}]
        title_score = _exact_match_score(kws, "edelstahl flasche premium", [])
        bullet_score = _exact_match_score(kws, "premium title", ["edelstahl flasche bullet"])
        assert title_score > bullet_score

    def test_no_matches(self):
        kws = [{"phrase": "xyz", "search_volume": 100}]
        assert _exact_match_score(kws, "abc", ["def"]) == 0


class TestSearchVolumeScore:
    def test_no_volume_returns_50(self):
        kws = [{"phrase": "test", "search_volume": 0}]
        assert _search_volume_score(kws, "test", ["test"]) == 50

    def test_high_volume_in_title(self):
        kws = [
            {"phrase": "big keyword", "search_volume": 10000},
            {"phrase": "small keyword", "search_volume": 100},
        ]
        score = _search_volume_score(kws, "big keyword title", [])
        assert score > 70  # WHY: High-volume keyword in title = good score


class TestBackendEfficiency:
    def test_optimal_range(self):
        backend = "a" * 245  # 245 bytes in optimal range
        assert _backend_efficiency(backend) == 100

    def test_over_limit_penalty(self):
        backend = "a" * 251
        assert _backend_efficiency(backend) == 50

    def test_empty_with_high_coverage(self):
        """Empty backend is OK when visible coverage is 95%+."""
        assert _backend_efficiency("", visible_coverage=96) >= 80

    def test_empty_with_low_coverage(self):
        """Empty backend is bad when visible coverage is low."""
        score = _backend_efficiency("", visible_coverage=50)
        assert score < 10


class TestStructureScore:
    def test_perfect_structure(self):
        title = "A" * 180 + " - " + "B" * 15  # ~198 chars with dash
        bullets = ["X" * 200 for _ in range(5)]
        assert _structure_score(title, bullets) == 100  # WHY: 100 base + 5 dash bonus, capped at 100

    def test_short_title_penalty(self):
        assert _structure_score("short", ["b" * 200] * 5) < 90

    def test_missing_bullets_penalty(self):
        score = _structure_score("A" * 180, ["b" * 200] * 3)
        assert score < _structure_score("A" * 180, ["b" * 200] * 5)

    def test_dash_bonus(self):
        # WHY: Use short titles (<150 chars) so base score has -15 penalty,
        # leaving room for +5 dash bonus to make a visible difference
        with_dash = _structure_score("Title - With Dash", ["b" * 200] * 5)
        without = _structure_score("Title Without Dash", ["b" * 200] * 5)
        assert with_dash > without
