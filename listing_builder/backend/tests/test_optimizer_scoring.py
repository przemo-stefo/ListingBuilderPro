# backend/tests/test_optimizer_scoring.py
# Purpose: Test the score_listing orchestration function
# NOT for: Individual service tests (coverage, RJ, PPC)

import pytest
from unittest.mock import patch, MagicMock


class TestScoreListing:

    @patch("services.optimizer_scoring.generate_ppc_recommendations")
    @patch("services.optimizer_scoring.calculate_ranking_juice")
    @patch("services.optimizer_scoring.calculate_multi_tier_coverage")
    @patch("services.optimizer_scoring.run_anti_stuffing_check")
    @patch("services.optimizer_scoring.check_compliance")
    @patch("services.optimizer_scoring.count_exact_matches")
    @patch("services.optimizer_scoring.coverage_for_text")
    def test_score_listing_returns_all_fields(
        self, mock_cov, mock_exact, mock_compliance, mock_stuffing,
        mock_multi_cov, mock_rj, mock_ppc
    ):
        from services.optimizer_scoring import score_listing

        mock_cov.return_value = (85.0, [], [])
        mock_exact.return_value = 10
        mock_compliance.return_value = {
            "status": "PASS", "warnings": [], "warning_count": 0
        }
        mock_stuffing.return_value = []
        mock_multi_cov.return_value = {"missing_keywords": []}
        mock_rj.return_value = {"total_score": 75}
        mock_ppc.return_value = {"campaigns": []}

        result = score_listing(
            all_kw=[{"keyword": "test", "tier": 1}],
            tier1=[{"keyword": "test", "tier": 1}],
            title_text="Test Product Title",
            bullet_lines=["Bullet one", "Bullet two"],
            desc_text="Description text here",
            backend_kw="test keyword",
            brand="TestBrand",
            limits={"backend": 250},
        )

        assert "coverage_pct" in result
        assert "compliance" in result
        assert "rj" in result
        assert "ppc" in result
        assert "missing" in result
        assert result["coverage_pct"] == 85.0

    @patch("services.optimizer_scoring.generate_ppc_recommendations")
    @patch("services.optimizer_scoring.calculate_ranking_juice")
    @patch("services.optimizer_scoring.calculate_multi_tier_coverage")
    @patch("services.optimizer_scoring.run_anti_stuffing_check")
    @patch("services.optimizer_scoring.check_compliance")
    @patch("services.optimizer_scoring.count_exact_matches")
    @patch("services.optimizer_scoring.coverage_for_text")
    def test_stuffing_warnings_merge_into_compliance(
        self, mock_cov, mock_exact, mock_compliance, mock_stuffing,
        mock_multi_cov, mock_rj, mock_ppc
    ):
        from services.optimizer_scoring import score_listing

        mock_cov.return_value = (90.0, [], [])
        mock_exact.return_value = 8
        mock_compliance.return_value = {
            "status": "PASS", "warnings": [], "warning_count": 0
        }
        mock_stuffing.return_value = ["Keyword stuffing: 'test' appears 5x"]
        mock_multi_cov.return_value = {"missing_keywords": []}
        mock_rj.return_value = {"total_score": 70}
        mock_ppc.return_value = {"campaigns": []}

        result = score_listing(
            all_kw=[], tier1=[], title_text="test test test",
            bullet_lines=[], desc_text="test test",
            backend_kw="", brand="", limits={"backend": 250},
        )

        assert result["compliance"]["status"] == "WARN"
        assert result["compliance"]["warning_count"] == 1

    @patch("services.optimizer_scoring.generate_ppc_recommendations")
    @patch("services.optimizer_scoring.calculate_ranking_juice")
    @patch("services.optimizer_scoring.calculate_multi_tier_coverage")
    @patch("services.optimizer_scoring.run_anti_stuffing_check")
    @patch("services.optimizer_scoring.check_compliance")
    @patch("services.optimizer_scoring.count_exact_matches")
    @patch("services.optimizer_scoring.coverage_for_text")
    def test_backend_utilization_calculation(
        self, mock_cov, mock_exact, mock_compliance, mock_stuffing,
        mock_multi_cov, mock_rj, mock_ppc
    ):
        from services.optimizer_scoring import score_listing

        mock_cov.return_value = (80.0, [], [])
        mock_exact.return_value = 5
        mock_compliance.return_value = {
            "status": "PASS", "warnings": [], "warning_count": 0
        }
        mock_stuffing.return_value = []
        mock_multi_cov.return_value = {"missing_keywords": []}
        mock_rj.return_value = {}
        mock_ppc.return_value = {}

        result = score_listing(
            all_kw=[], tier1=[], title_text="Title",
            bullet_lines=[], desc_text="",
            backend_kw="keyword data here",  # 17 bytes
            brand="", limits={"backend": 250},
        )

        assert result["backend_bytes"] == len("keyword data here".encode("utf-8"))
        assert result["backend_util"] > 0
