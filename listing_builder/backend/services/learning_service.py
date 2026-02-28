# backend/services/learning_service.py
# Purpose: Self-learning — store successful listings, retrieve as few-shot examples
# NOT for: Ranking Juice calculation or LLM calls

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

# WHY: 75 is the quality gate — listings below this aren't good enough as examples
MIN_RANKING_JUICE = 75


def store_successful_listing(
    db: Session,
    listing_data: Dict,
    ranking_juice_data: Dict,
    user_id: str = "",
) -> Optional[str]:
    """
    INSERT into listing_history when RJ >= 75.
    Returns the new row's UUID or None if below threshold.
    """
    score = ranking_juice_data.get("score", 0)
    if score < MIN_RANKING_JUICE:
        return None

    try:
        # WHY: user_id for tenant isolation — each user's listings are scoped
        result = db.execute(
            text("""
                INSERT INTO listing_history
                    (brand, marketplace, product_title, title, bullets, description,
                     backend_keywords, ranking_juice, grade, keyword_count, user_id)
                VALUES
                    (:brand, :marketplace, :product_title, :title, CAST(:bullets AS jsonb),
                     :description, :backend_keywords, :ranking_juice, :grade, :keyword_count, :user_id)
                RETURNING id
            """),
            {
                "brand": listing_data.get("brand", ""),
                "marketplace": listing_data.get("marketplace", ""),
                "product_title": listing_data.get("product_title", ""),
                "title": listing_data.get("title", ""),
                "bullets": str(listing_data.get("bullets", "[]")),
                "description": listing_data.get("description", ""),
                "backend_keywords": listing_data.get("backend_keywords", ""),
                "ranking_juice": score,
                "grade": ranking_juice_data.get("grade", ""),
                "keyword_count": listing_data.get("keyword_count", 0),
                "user_id": user_id or None,
            },
        )
        row = result.fetchone()
        db.commit()
        listing_id = str(row[0]) if row else None
        logger.info("learning_stored", rj=score, grade=ranking_juice_data.get("grade"))
        return listing_id
    except Exception as e:
        logger.warning("learning_store_failed", error=str(e))
        db.rollback()
        return None


def get_past_successes(
    db: Session, marketplace: str, limit: int = 3, user_id: str = ""
) -> List[Dict]:
    """
    SELECT top listings by ranking_juice WHERE RJ >= 75 AND marketplace matches.
    Returns few-shot examples for prompt injection.
    WHY: user_id filter prevents cross-tenant data leak (User A's listings → User B's prompts).
    """
    try:
        # WHY: Single query with dynamic user_id filter — DRY, prevents cross-tenant data leak
        params: Dict = {"min_rj": MIN_RANKING_JUICE, "marketplace": marketplace, "limit": limit}
        if user_id:
            user_filter = "AND user_id = :user_id"
            params["user_id"] = user_id
        else:
            user_filter = "AND user_id IS NULL"

        result = db.execute(
            text(f"""
                SELECT title, bullets, description, backend_keywords, ranking_juice, grade
                FROM listing_history
                WHERE ranking_juice >= :min_rj AND marketplace = :marketplace {user_filter}
                ORDER BY ranking_juice DESC
                LIMIT :limit
            """),
            params,
        )
        rows = result.fetchall()
        return [
            {
                "title": r[0],
                "bullets": r[1],  # Already JSONB → Python list
                "description": r[2],
                "backend_keywords": r[3],
                "ranking_juice": r[4],
                "grade": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning("learning_fetch_failed", error=str(e))
        return []


def submit_feedback(db: Session, listing_id: str, rating: int, user_id: str) -> bool:
    """UPDATE user_rating on a listing_history row. Verifies ownership via user_id column."""
    try:
        # WHY: Direct user_id check — simpler than JOIN through optimization_runs
        result = db.execute(
            text("""
                UPDATE listing_history SET user_rating = :rating
                WHERE id = :id AND user_id = :user_id
            """),
            {"rating": rating, "id": listing_id, "user_id": user_id},
        )
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.warning("learning_feedback_failed", error=str(e))
        db.rollback()
        return False
