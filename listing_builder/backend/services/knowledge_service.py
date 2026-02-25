# backend/services/knowledge_service.py
# Purpose: Search knowledge chunks for expert context injection
# NOT for: Ingestion, chunk management, or low-level search (see search_strategies.py)

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

from config import settings
from services.embedding_service import get_embedding
from services.query_understanding import analyze_query
from services.search_strategies import lexical_search, vector_search, hybrid_merge

logger = structlog.get_logger()

# WHY: Primary categories = high-signal marketplace knowledge (listing, keyword, ranking, ppc).
# Copywriting (25K chunks) excluded from primary — too generic, drowns real marketplace advice.
# Secondary categories used only as fallback when primary returns < 2 results.
CATEGORY_MAP = {
    "title": {
        "primary": ["listing_optimization", "keyword_research", "ranking"],
        "fallback": ["copywriting", "ppc"],
    },
    "bullets": {
        "primary": ["listing_optimization", "conversion_optimization", "keyword_research"],
        "fallback": ["copywriting", "marketing_psychology"],
    },
    "description": {
        "primary": ["listing_optimization", "conversion_optimization", "market_research"],
        "fallback": ["copywriting", "marketing_psychology"],
    },
}

MAX_CONTEXT_CHARS = 3000
# WHY: Only primary categories for the batch search — keeps results focused
ALL_PRIMARY = list({c for cats in CATEGORY_MAP.values() for c in cats["primary"]})


async def _get_search_rows(
    db: Session, query: str, categories: list[str] | None,
    limit: int, query_embedding: list[float] | None = None,
) -> list[tuple]:
    """Route to the right search strategy based on rag_mode config."""
    mode = settings.rag_mode

    if mode == "semantic" and query_embedding:
        return vector_search(db, query_embedding, categories, limit)

    if mode == "hybrid" and query_embedding:
        v_rows = vector_search(db, query_embedding, categories, limit)
        k_rows = lexical_search(db, query, categories, limit)
        return hybrid_merge(v_rows, k_rows, limit)

    return lexical_search(db, query, categories, limit)


async def _expand_query(query: str) -> str:
    """Use query understanding to expand search terms in non-lexical modes."""
    if settings.rag_mode == "lexical":
        return query
    understood = await analyze_query(query)
    if understood and understood.get("expanded_query"):
        return understood["expanded_query"]
    return query


async def _get_embedding_if_needed(query: str) -> list[float] | None:
    """Get query embedding only when rag_mode requires it.

    WHY: HuggingFace embeddings are free — no API key check needed.
    """
    if settings.rag_mode == "lexical":
        return None
    return await get_embedding(query)


def _format_chunks(rows: list[tuple], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Format search results into context string with source attribution."""
    parts = []
    total_len = 0
    for row in rows:
        chunk = f"[{row[3]} — {row[2]}]\n{row[1]}"
        if total_len + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total_len += len(chunk)
    return "\n\n".join(parts)


def _format_chunks_with_sources(
    rows: list[tuple], max_chars: int = MAX_CONTEXT_CHARS
) -> tuple[str, list[str]]:
    """Format search results and extract unique source filenames."""
    parts = []
    filenames = []
    total_len = 0
    for row in rows:
        chunk = f"[{row[3]} — {row[2]}]\n{row[1]}"
        if total_len + len(chunk) > max_chars:
            break
        parts.append(chunk)
        filenames.append(row[2])
        total_len += len(chunk)

    unique_names = []
    seen: set[str] = set()
    for fn in filenames:
        clean = fn.rsplit(".", 1)[0].replace("_", " ")
        if clean not in seen:
            seen.add(clean)
            unique_names.append(clean)

    return "\n\n".join(parts), unique_names


async def search_knowledge_batch(
    db: Session, query: str, max_chunks_per_type: int = 5,
) -> dict[str, str]:
    """Fetch expert context per prompt type with primary/fallback category strategy.

    WHY: Searching per prompt_type separately prevents copywriting (25K chunks)
    from drowning out high-signal marketplace categories (listing_optimization, ranking).
    Fallback to copywriting only when primary categories return < 2 results.
    """
    try:
        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)
        min_primary_results = 2

        result = {}
        total_fetched = 0
        for prompt_type, cat_config in CATEGORY_MAP.items():
            rows = await _get_search_rows(
                db, search_query, cat_config["primary"],
                max_chunks_per_type, query_embedding,
            )

            # WHY: If primary categories return too few results, add fallback (copywriting etc.)
            if len(rows) < min_primary_results and cat_config["fallback"]:
                fallback_rows = await _get_search_rows(
                    db, search_query, cat_config["fallback"],
                    max_chunks_per_type - len(rows), query_embedding,
                )
                rows = rows + fallback_rows

            total_fetched += len(rows)
            result[prompt_type] = _format_chunks(rows[:max_chunks_per_type])

        hit_count = sum(1 for v in result.values() if v)
        if hit_count:
            logger.info("knowledge_batch_hit", mode=settings.rag_mode,
                        chunks_fetched=total_fetched, types_with_context=hit_count,
                        query_preview=query[:60])

        return result
    except Exception as e:
        logger.warning("knowledge_batch_error", error=str(e))
        return {"title": "", "bullets": "", "description": ""}


async def search_knowledge(
    db: Session, query: str, prompt_type: str, max_chunks: int = 5,
) -> str:
    """Search knowledge chunks with primary/fallback category strategy.

    WHY: This must never crash the optimizer — expert context is a bonus, not required.
    """
    try:
        cat_config = CATEGORY_MAP.get(prompt_type)
        primary = cat_config["primary"] if cat_config else ["listing_optimization"]
        fallback = cat_config["fallback"] if cat_config else ["copywriting"]

        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)

        rows = await _get_search_rows(db, search_query, primary, max_chunks, query_embedding)

        # WHY: If primary categories return too few, add fallback (copywriting etc.)
        if len(rows) < 2 and fallback:
            fallback_rows = await _get_search_rows(
                db, search_query, fallback, max_chunks - len(rows), query_embedding,
            )
            rows = rows + fallback_rows

        # WHY: Expanded query can be too verbose for plainto_tsquery (requires ALL terms).
        if not rows and search_query != query:
            logger.info("search_fallback_to_original", expanded=search_query[:60])
            query_embedding = await _get_embedding_if_needed(query)
            rows = await _get_search_rows(db, query, primary, max_chunks, query_embedding)

        if not rows:
            return ""

        logger.info("knowledge_search_hit", mode=settings.rag_mode,
                    prompt_type=prompt_type, chunks_found=len(rows),
                    query_preview=query[:60])
        return _format_chunks(rows)
    except Exception as e:
        logger.warning("knowledge_search_error", error=str(e))
        return ""


async def search_all_categories(
    db: Session, query: str, max_chunks: int = 8,
    category_prefix: str | None = None,
) -> tuple[str, list[str]]:
    """Search knowledge chunks for Expert Q&A.

    WHY category_prefix: Kaufland expert should prefer kaufland_ chunks,
    Amazon expert should search all. Prefix filter narrows results.
    """
    try:
        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)

        # WHY: If expert has a category prefix, search those first, then fall back to all
        categories = None
        if category_prefix:
            categories = [
                cat for cat in _get_all_categories(db)
                if cat.startswith(category_prefix) or cat == "listing_optimization"
            ] or None

        rows = await _get_search_rows(db, search_query, categories, max_chunks, query_embedding)

        # WHY: If expanded query returned nothing, retry with the user's original query.
        # Groq expansion can produce generic words that miss tsvector; original keywords
        # often match better, especially when vector search is unavailable.
        if not rows and search_query != query:
            logger.info("search_fallback_to_original", expanded=search_query[:60])
            query_embedding = await _get_embedding_if_needed(query)
            rows = await _get_search_rows(db, query, categories, max_chunks, query_embedding)

        # WHY: If category-filtered search found nothing, search all categories as fallback
        if not rows and categories:
            logger.info("search_fallback_all_categories", prefix=category_prefix)
            rows = await _get_search_rows(db, search_query, None, max_chunks, query_embedding)

        if not rows:
            return "", []

        return _format_chunks_with_sources(rows)
    except Exception as e:
        logger.warning("knowledge_search_all_error", error=str(e))
        return "", []


def _get_all_categories(db: Session) -> list[str]:
    """Get distinct category names from DB. Cached per session."""
    rows = db.execute(text("SELECT DISTINCT category FROM knowledge_chunks")).fetchall()
    return [r[0] for r in rows]
