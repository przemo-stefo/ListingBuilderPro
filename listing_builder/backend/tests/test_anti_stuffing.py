# backend/tests/test_anti_stuffing.py
# Purpose: Test keyword density and word repetition limits
# NOT for: LLM or optimizer logic

import pytest
from services.anti_stuffing_service import (
    _word_counts,
    validate_keyword_density,
    validate_word_repetition,
    run_anti_stuffing_check,
    MAX_DENSITY_PCT,
    TITLE_MAX_REPEATS,
    LISTING_MAX_REPEATS,
    STOP_WORDS,
)


class TestWordCounts:

    def test_basic_counting(self):
        counts = _word_counts("hello world hello")
        assert counts["hello"] == 2
        assert counts["world"] == 1

    def test_stop_words_excluded(self):
        counts = _word_counts("the quick brown fox and the lazy dog")
        assert "the" not in counts
        assert "and" not in counts
        assert "quick" in counts

    def test_short_words_excluded(self):
        counts = _word_counts("I a x am big")
        assert "a" not in counts  # 1 char
        assert "x" not in counts  # 1 char
        assert "am" in counts  # 2 chars

    def test_case_insensitive(self):
        counts = _word_counts("Hello HELLO hello")
        assert counts["hello"] == 3

    def test_polish_chars(self):
        counts = _word_counts("łóżko łóżko stół")
        assert counts["łóżko"] == 2


class TestKeywordDensity:

    def test_no_warnings_normal_text(self):
        text = "premium stainless steel water bottle for outdoor hiking camping sports"
        warnings = validate_keyword_density(text)
        assert warnings == []

    def test_warning_on_stuffing(self):
        # "steel" repeated many times to exceed 3% density
        text = " ".join(["steel"] * 10 + ["bottle", "water", "premium", "outdoor", "camping"])
        warnings = validate_keyword_density(text)
        assert len(warnings) > 0
        assert "steel" in warnings[0]

    def test_single_occurrence_no_warning(self):
        text = "bottle water premium outdoor camping hiking sports"
        warnings = validate_keyword_density(text)
        assert warnings == []

    def test_empty_text(self):
        assert validate_keyword_density("") == []


class TestWordRepetition:

    def test_no_title_repetition(self):
        title = "Premium Steel Water Bottle 500ml"
        warnings = validate_word_repetition(title, [])
        assert warnings == []

    def test_title_repetition_detected(self):
        title = "Steel Steel Steel Water Bottle"
        warnings = validate_word_repetition(title, [])
        title_warnings = [w for w in warnings if "Title" in w]
        assert len(title_warnings) > 0

    def test_listing_repetition_detected(self):
        title = "Steel Bottle"
        bullets = [
            "Steel construction",
            "Steel material",
            "Steel design",
            "Steel quality",
            "Steel finish",
        ]
        warnings = validate_word_repetition(title, bullets)
        listing_warnings = [w for w in warnings if "Listing" in w]
        assert len(listing_warnings) > 0


class TestRunAntiStuffingCheck:

    def test_clean_listing_no_warnings(self):
        warnings = run_anti_stuffing_check(
            "Premium Water Bottle",
            ["Durable construction", "Easy to clean"],
            "Great for outdoor use",
        )
        assert warnings == []

    def test_stuffed_listing_returns_warnings(self):
        warnings = run_anti_stuffing_check(
            "Steel Steel Steel Bottle",
            ["Steel material", "Steel design", "Steel quality"],
            "Premium steel product",
        )
        assert len(warnings) > 0
