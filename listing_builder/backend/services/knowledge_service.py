# backend/services/knowledge_service.py
# Purpose: Search Inner Circle transcript chunks for expert context injection
# NOT for: Ingestion or chunk management (see scripts/ingest_transcripts.py)

from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

# WHY: Map prompt types to relevant transcript categories so the LLM gets
# expert knowledge that matches what it's currently generating
CATEGORY_MAP = {
    "title": ["listing_optimization", "keyword_research", "ranking"],
    "bullets": ["listing_optimization", "conversion_optimization", "keyword_research"],
    "description": ["listing_optimization", "conversion_optimization", "general"],
}

MAX_CONTEXT_CHARS = 3000


def search_knowledge(
    db: Session,
    query: str,
    prompt_type: str,
    max_chunks: int = 5,
) -> str:
    """Search knowledge chunks by full-text search with category pre-filtering.

    Returns formatted context string or empty string on any failure.
    WHY: This must never crash the optimizer — expert context is a bonus, not required.
    """
    try:
        categories = CATEGORY_MAP.get(prompt_type, ["general"])

        # WHY: plainto_tsquery handles multi-word queries without requiring operators
        rows = db.execute(
            text("""
                SELECT content, filename, category,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                FROM knowledge_chunks
                WHERE search_vector @@ plainto_tsquery('english', :query)
                  AND category = ANY(:categories)
                ORDER BY rank DESC
                LIMIT :max_chunks
            """),
            {"query": query, "categories": categories, "max_chunks": max_chunks},
        ).fetchall()

        # WHY: Fallback without category filter if pre-filtered search returns nothing
        if not rows:
            rows = db.execute(
                text("""
                    SELECT content, filename, category,
                           ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                    FROM knowledge_chunks
                    WHERE search_vector @@ plainto_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT :max_chunks
                """),
                {"query": query, "max_chunks": max_chunks},
            ).fetchall()

        if not rows:
            return ""

        # WHY: Format chunks with source attribution so LLM knows where advice comes from
        parts = []
        total_len = 0
        for row in rows:
            chunk = f"[{row[2]} — {row[1]}]\n{row[0]}"
            if total_len + len(chunk) > MAX_CONTEXT_CHARS:
                break
            parts.append(chunk)
            total_len += len(chunk)

        logger.info(
            "knowledge_search_hit",
            prompt_type=prompt_type,
            chunks_found=len(parts),
            query_preview=query[:60],
        )

        return "\n\n".join(parts)

    except Exception as e:
        logger.warning("knowledge_search_error", error=str(e))
        return ""
