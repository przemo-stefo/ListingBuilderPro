# backend/tests/test_grey_market.py
# Purpose: Grey market risk scoring calculator tests
# NOT for: SP-API data fetching

import pytest
from services.grey_market_service import score_grey_market


class TestGreyMarketScoring:

    def test_zero_risk_default(self):
        result = score_grey_market()
        assert result["score"] == 0
        assert result["risk_level"] == "LOW"

    def test_low_risk(self):
        result = score_grey_market(unauthorized_sellers=1, buy_box_rate=95)
        assert result["score"] < 20
        assert result["risk_level"] == "LOW"

    def test_moderate_risk(self):
        result = score_grey_market(unauthorized_sellers=1, buy_box_rate=80)
        assert 20 <= result["score"] < 40
        assert result["risk_level"] == "MODERATE"

    def test_high_risk(self):
        result = score_grey_market(
            unauthorized_sellers=2, buy_box_rate=70, suppressed_asins=1
        )
        assert 40 <= result["score"] < 70
        assert result["risk_level"] == "HIGH"

    def test_critical_risk(self):
        result = score_grey_market(
            unauthorized_sellers=3, buy_box_rate=50,
            suppressed_asins=2, hijack_reports=2
        )
        assert result["score"] >= 70
        assert result["risk_level"] == "CRITICAL"

    def test_score_capped_at_100(self):
        result = score_grey_market(
            unauthorized_sellers=10, buy_box_rate=0,
            suppressed_asins=10, hijack_reports=10
        )
        assert result["score"] <= 100

    def test_components_included(self):
        result = score_grey_market(unauthorized_sellers=2)
        assert "components" in result
        assert "unauthorized_sellers" in result["components"]
        assert "buy_box_erosion" in result["components"]
        assert "suppressed_asins" in result["components"]
        assert "hijack_reports" in result["components"]

    def test_recommendation_present(self):
        result = score_grey_market()
        assert "recommendation" in result
        assert len(result["recommendation"]) > 10

    def test_buy_box_above_90_no_penalty(self):
        result = score_grey_market(buy_box_rate=95)
        assert result["components"]["buy_box_erosion"] == 0

    def test_seller_score_capped_at_45(self):
        result = score_grey_market(unauthorized_sellers=10)
        assert result["components"]["unauthorized_sellers"] == 45
