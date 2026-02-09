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

# WHY: Union of all categories across prompt types — for batch query
ALL_CATEGORIES = list({c for cats in CATEGORY_MAP.values() for c in cats})


def search_knowledge_batch(
    db: Session,
    query: str,
    max_chunks_per_type: int = 5,
) -> dict[str, str]:
    """Fetch expert context for all prompt types in a single DB query.

    Returns {"title": "...", "bullets": "...", "description": "..."}.
    WHY: 1 query instead of 3-6 round-trips per optimization request.
    """
    try:
        rows = db.execute(
            text("""
                SELECT content, filename, category,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                FROM knowledge_chunks
                WHERE search_vector @@ plainto_tsquery('english', :query)
                  AND category = ANY(:categories)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {
                "query": query,
                "categories": ALL_CATEGORIES,
                "limit": max_chunks_per_type * 3,
            },
        ).fetchall()

        # WHY: If category-filtered returned nothing, try without filter
        if not rows:
            rows = db.execute(
                text("""
                    SELECT content, filename, category,
                           ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                    FROM knowledge_chunks
                    WHERE search_vector @@ plainto_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT :limit
                """),
                {"query": query, "limit": max_chunks_per_type * 3},
            ).fetchall()

        result = {}
        for prompt_type, categories in CATEGORY_MAP.items():
            cat_set = set(categories)
            # WHY: Pick top chunks whose category matches this prompt type
            matched = [r for r in rows if r[2] in cat_set]
            # Fallback: if no category match, use all rows (better than nothing)
            if not matched:
                matched = list(rows)

            parts = []
            total_len = 0
            for row in matched[:max_chunks_per_type]:
                chunk = f"[{row[2]} — {row[1]}]\n{row[0]}"
                if total_len + len(chunk) > MAX_CONTEXT_CHARS:
                    break
                parts.append(chunk)
                total_len += len(chunk)

            result[prompt_type] = "\n\n".join(parts)

        hit_count = sum(1 for v in result.values() if v)
        if hit_count:
            logger.info(
                "knowledge_batch_hit",
                chunks_fetched=len(rows),
                types_with_context=hit_count,
                query_preview=query[:60],
            )

        return result

    except Exception as e:
        logger.warning("knowledge_batch_error", error=str(e))
        return {"title": "", "bullets": "", "description": ""}


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
