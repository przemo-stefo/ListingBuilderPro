# backend/services/grey_market_service.py
# Purpose: Grey market risk scoring — standalone calculator
# NOT for: SP-API data fetching (that requires AMAZON_REFRESH_TOKEN, not yet available)

from __future__ import annotations

from typing import Dict, Any
import structlog

logger = structlog.get_logger()


def score_grey_market(
    unauthorized_sellers: int = 0,
    buy_box_rate: float = 100.0,
    suppressed_asins: int = 0,
    hijack_reports: int = 0,
) -> Dict[str, Any]:
    """
    Calculate grey market risk score 0-100.
    WHY: DataDive identified these as the top 4 signals for unauthorized seller activity.
    Higher score = higher risk.
    """
    score = 0.0

    # WHY: Each unauthorized seller adds 15 points — 3+ sellers is critical
    seller_score = min(unauthorized_sellers * 15, 45)
    score += seller_score

    # WHY: Buy box rate below 90% suggests competition from unauthorized sellers
    if buy_box_rate < 90:
        buybox_score = min((90 - buy_box_rate) * 1.5, 25)
        score += buybox_score
    else:
        buybox_score = 0.0

    # WHY: Suppressed ASINs indicate policy violations — often from grey market sellers
    suppressed_score = min(suppressed_asins * 10, 20)
    score += suppressed_score

    # WHY: IP/hijack reports are the strongest signal — each report worth 10 points
    hijack_score = min(hijack_reports * 10, 20)
    score += hijack_score

    total = min(round(score), 100)

    logger.info("grey_market_scored", score=total, sellers=unauthorized_sellers, buybox=buy_box_rate)

    if total >= 70:
        risk_level = "CRITICAL"
        recommendation = "Immediate action required — file IP complaints and contact Amazon Brand Registry"
    elif total >= 40:
        risk_level = "HIGH"
        recommendation = "Monitor closely — consider test purchases to verify unauthorized sellers"
    elif total >= 20:
        risk_level = "MODERATE"
        recommendation = "Keep watching — set up alerts for new seller activity"
    else:
        risk_level = "LOW"
        recommendation = "No immediate concern — maintain regular monitoring"

    return {
        "score": total,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "components": {
            "unauthorized_sellers": round(seller_score, 1),
            "buy_box_erosion": round(buybox_score, 1),
            "suppressed_asins": round(suppressed_score, 1),
            "hijack_reports": round(hijack_score, 1),
        },
    }
