# backend/services/optimizer_scoring.py
# Purpose: Post-optimization scoring — coverage, compliance, anti-stuffing, RJ, PPC, TOS
# NOT for: LLM calls, keyword placement, or post-processing

from __future__ import annotations

from typing import List, Dict, Any
from services.coverage_service import (
    calculate_multi_tier_coverage, coverage_for_text,
    count_exact_matches, grade,
)
from services.ranking_juice_service import calculate_ranking_juice
from services.anti_stuffing_service import run_anti_stuffing_check
from services.ppc_service import generate_ppc_recommendations
from services.listing_post_processing import check_compliance
from services.amazon_tos_checker import check_amazon_tos


def score_listing(
    all_kw: List[dict], tier1: List[dict],
    title_text: str, bullet_lines: List[str], desc_text: str, backend_kw: str,
    brand: str, limits: dict, marketplace: str = "amazon",
) -> Dict[str, Any]:
    """Run all scoring: coverage, compliance, anti-stuffing, RJ, PPC, Amazon TOS.

    Returns dict with all scoring results — consumed by optimizer_service.
    """
    full_listing_text = title_text + " " + " ".join(bullet_lines) + " " + desc_text
    full_text_with_backend = full_listing_text + " " + backend_kw
    backend_bytes = len(backend_kw.encode("utf-8"))

    cov_pct, _, _ = coverage_for_text(all_kw, full_text_with_backend)
    exact_matches = count_exact_matches(all_kw, full_text_with_backend)
    title_cov, _, _ = coverage_for_text(tier1, title_text)

    compliance = check_compliance(title_text, bullet_lines, desc_text, brand, limits)

    # WHY: Anti-stuffing catches keyword repetition that compliance check misses
    stuffing_warnings = run_anti_stuffing_check(title_text, bullet_lines, desc_text)
    if stuffing_warnings:
        compliance["warnings"].extend(stuffing_warnings)
        compliance["warning_count"] = len(compliance["warnings"])
        if compliance["status"] == "PASS":
            compliance["status"] = "WARN"

    backend_util = round((backend_bytes / limits["backend"]) * 100, 1) if limits["backend"] > 0 else 0
    rj = calculate_ranking_juice(all_kw, title_text, bullet_lines, backend_kw, desc_text)
    coverage_breakdown = calculate_multi_tier_coverage(all_kw, title_text, bullet_lines, backend_kw, desc_text)
    ppc = generate_ppc_recommendations(all_kw, full_text_with_backend)

    # WHY: Amazon TOS check catches suppression risks that basic compliance misses
    tos = check_amazon_tos(title_text, bullet_lines, desc_text, backend_kw, marketplace)
    if tos.get("violations"):
        for v in tos["violations"]:
            if v["severity"] == "SUPPRESSION":
                compliance["errors"].append(f"[TOS] {v['message']}")
            else:
                compliance["warnings"].append(f"[TOS] {v['message']}")
        compliance["error_count"] = len(compliance["errors"])
        compliance["warning_count"] = len(compliance["warnings"])
        if compliance["errors"]:
            compliance["status"] = "FAIL"
        elif compliance["warnings"] and compliance["status"] == "PASS":
            compliance["status"] = "WARN"

    return {
        "coverage_pct": cov_pct,
        "coverage_mode": grade(cov_pct),
        "exact_matches": exact_matches,
        "title_cov": title_cov,
        "backend_bytes": backend_bytes,
        "backend_util": backend_util,
        "compliance": compliance,
        "rj": rj,
        "coverage_breakdown": coverage_breakdown,
        "ppc": ppc,
        "missing": coverage_breakdown.get("missing_keywords", []),
        "tos": tos,
    }
