# backend/services/aplus_rag.py
# Purpose: RAG lookup + feedback for A+ Content training examples
# NOT for: Image rendering or LLM calls

from typing import List, Dict, Optional
import structlog
from sqlalchemy.orm import Session
from models.aplus_example import AplusTrainingExample

logger = structlog.get_logger()


def fetch_examples(category: str, lang: str, limit: int = 3, db: Optional[Session] = None) -> List[Dict]:
    """Fetch best training examples matching category+lang for few-shot injection.

    WHY: RAG lookup — LLM sees concrete examples of good JSON structure,
    dramatically improving valid output rate.

    Fallback chain: exact match → same category any lang → same lang any category.
    """
    if not db:
        return []

    # WHY: times_used ASC tie-breaker ensures variety among equal-quality examples
    def _query(cat_filter, lang_filter):
        q = db.query(AplusTrainingExample).filter(AplusTrainingExample.quality_score > 0.3)
        if cat_filter:
            q = q.filter(AplusTrainingExample.category == cat_filter)
        if lang_filter:
            q = q.filter(AplusTrainingExample.lang == lang_filter)
        return q.order_by(
            AplusTrainingExample.quality_score.desc(),
            AplusTrainingExample.times_used.asc(),
        ).limit(limit).all()

    results = _query(category, lang)
    if not results and category:
        results = _query(category, None)
    if not results:
        results = _query(None, lang)
    if not results:
        return []

    # WHY: Increment times_used so less-used examples get picked next time
    for row in results:
        row.times_used = (row.times_used or 0) + 1
    try:
        db.commit()
    except Exception:
        db.rollback()

    return [{"id": r.id, "content_data": r.content_data} for r in results]


def record_feedback(example_ids: List[int], accepted: bool, db: Session):
    """Update quality scores based on user accept/reject feedback.

    WHY: Laplace smoothing — quality_score = (accepted + 1) / (accepted + rejected + 2).
    Starts at 0.5 with no data, biased to 0.7 for imported examples.
    """
    if not example_ids or not db:
        return

    examples = db.query(AplusTrainingExample).filter(
        AplusTrainingExample.id.in_(example_ids)
    ).all()

    for ex in examples:
        if accepted:
            ex.times_accepted = (ex.times_accepted or 0) + 1
        else:
            ex.times_rejected = (ex.times_rejected or 0) + 1
        # WHY: Laplace smoothing gives stable scores even with few data points
        ex.quality_score = (ex.times_accepted + 1) / (ex.times_accepted + ex.times_rejected + 2)

    try:
        db.commit()
        logger.info("aplus_feedback_recorded", ids=example_ids, accepted=accepted)
    except Exception:
        db.rollback()


def save_user_example(product_name: str, brand: str, category: str, lang: str,
                      content_data: dict, db: Session):
    """Save user-accepted generation as new training example.

    WHY: Self-improving loop — accepted content becomes future few-shot example.
    Starts at 0.6 quality (lower than imported 0.7, can rise with feedback).
    """
    ex = AplusTrainingExample(
        product_name=product_name[:500],
        brand=brand[:200],
        category=category[:100] or "General",
        lang=lang[:10] or "pl",
        content_data=content_data,
        quality_score=0.6,
        source="user_generated",
    )
    db.add(ex)
    try:
        db.commit()
        logger.info("aplus_user_example_saved", product=product_name[:50])
    except Exception:
        db.rollback()
