# backend/services/knowledge_service.py
# Purpose: Search Inner Circle transcript chunks for expert context injection
# NOT for: Ingestion, chunk management, or low-level search (see search_strategies.py)

from __future__ import annotations

from sqlalchemy.orm import Session
import structlog

from config import settings
from services.embedding_service import get_embedding
from services.query_understanding import analyze_query
from services.search_strategies import lexical_search, vector_search, hybrid_merge

logger = structlog.get_logger()

# WHY: Map prompt types to relevant transcript categories
CATEGORY_MAP = {
    "title": ["listing_optimization", "keyword_research", "ranking"],
    "bullets": ["listing_optimization", "conversion_optimization", "keyword_research"],
    "description": ["listing_optimization", "conversion_optimization", "general"],
}

MAX_CONTEXT_CHARS = 3000
ALL_CATEGORIES = list({c for cats in CATEGORY_MAP.values() for c in cats})


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
    """Fetch expert context for all prompt types in a single search pass.

    Returns {"title": "...", "bullets": "...", "description": "..."}.
    """
    try:
        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)
        limit = max_chunks_per_type * 3

        rows = await _get_search_rows(db, search_query, ALL_CATEGORIES, limit, query_embedding)
        if not rows:
            rows = await _get_search_rows(db, search_query, None, limit, query_embedding)

        result = {}
        for prompt_type, categories in CATEGORY_MAP.items():
            cat_set = set(categories)
            matched = [r for r in rows if r[3] in cat_set] or list(rows)
            result[prompt_type] = _format_chunks(matched[:max_chunks_per_type])

        hit_count = sum(1 for v in result.values() if v)
        if hit_count:
            logger.info("knowledge_batch_hit", mode=settings.rag_mode,
                        chunks_fetched=len(rows), types_with_context=hit_count,
                        query_preview=query[:60])

        return result
    except Exception as e:
        logger.warning("knowledge_batch_error", error=str(e))
        return {"title": "", "bullets": "", "description": ""}


async def search_knowledge(
    db: Session, query: str, prompt_type: str, max_chunks: int = 5,
) -> str:
    """Search knowledge chunks with hybrid/lexical/semantic based on rag_mode.

    WHY: This must never crash the optimizer — expert context is a bonus, not required.
    """
    try:
        categories = CATEGORY_MAP.get(prompt_type, ["general"])
        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)

        rows = await _get_search_rows(db, search_query, categories, max_chunks, query_embedding)
        if not rows:
            rows = await _get_search_rows(db, search_query, None, max_chunks, query_embedding)
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
) -> tuple[str, list[str]]:
    """Search ALL knowledge chunks regardless of category (for Expert Q&A)."""
    try:
        search_query = await _expand_query(query)
        query_embedding = await _get_embedding_if_needed(search_query)

        rows = await _get_search_rows(db, search_query, None, max_chunks, query_embedding)
        if not rows:
            return "", []

        return _format_chunks_with_sources(rows)
    except Exception as e:
        logger.warning("knowledge_search_all_error", error=str(e))
        return "", []
