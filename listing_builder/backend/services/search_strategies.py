# backend/services/search_strategies.py
# Purpose: Low-level search functions — lexical, vector, hybrid merge
# NOT for: High-level knowledge search logic (that's knowledge_service.py)

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import text

# WHY: Weights for hybrid merge — vector captures semantics, keyword captures exact terms
VECTOR_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4


def lexical_search(
    db: Session, query: str, categories: list[str] | None, limit: int
) -> list[tuple]:
    """Keyword search using tsvector. Returns (id, content, filename, category, score)."""
    if categories:
        rows = db.execute(
            text("""
                SELECT id, content, filename, category,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                FROM knowledge_chunks
                WHERE search_vector @@ plainto_tsquery('english', :query)
                  AND category = ANY(:categories)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"query": query, "categories": categories, "limit": limit},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT id, content, filename, category,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                FROM knowledge_chunks
                WHERE search_vector @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"query": query, "limit": limit},
        ).fetchall()
    return rows


def vector_search(
    db: Session, query_embedding: list[float], categories: list[str] | None, limit: int
) -> list[tuple]:
    """Vector similarity search using pgvector cosine distance.

    Returns (id, content, filename, category, similarity_score).
    WHY: 1 - cosine_distance = cosine_similarity (higher is better).
    """
    emb_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    if categories:
        rows = db.execute(
            text("""
                SELECT id, content, filename, category,
                       1 - (embedding <=> CAST(:emb AS vector)) as score
                FROM knowledge_chunks
                WHERE embedding IS NOT NULL
                  AND category = ANY(:categories)
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
            """),
            {"emb": emb_str, "categories": categories, "limit": limit},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT id, content, filename, category,
                       1 - (embedding <=> CAST(:emb AS vector)) as score
                FROM knowledge_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
            """),
            {"emb": emb_str, "limit": limit},
        ).fetchall()
    return rows


def _normalize_scores(rows: list[tuple]) -> list[tuple]:
    """Normalize scores to 0-1 range. Input: (id, content, filename, category, score)."""
    if not rows:
        return []
    scores = [r[4] for r in rows]
    min_s, max_s = min(scores), max(scores)
    span = max_s - min_s if max_s != min_s else 1.0
    return [(r[0], r[1], r[2], r[3], (r[4] - min_s) / span) for r in rows]


def hybrid_merge(
    vector_rows: list[tuple], keyword_rows: list[tuple], limit: int
) -> list[tuple]:
    """Merge vector + keyword results with weighted scores, preferring transcript diversity.

    Returns (id, content, filename, category, combined_score).
    """
    v_norm = _normalize_scores(vector_rows)
    k_norm = _normalize_scores(keyword_rows)

    # WHY: Build score map by chunk id — some chunks appear in both result sets
    scores: dict[int, dict] = {}
    for r in v_norm:
        scores[r[0]] = {"content": r[1], "filename": r[2], "category": r[3],
                         "v_score": r[4], "k_score": 0.0}
    for r in k_norm:
        if r[0] in scores:
            scores[r[0]]["k_score"] = r[4]
        else:
            scores[r[0]] = {"content": r[1], "filename": r[2], "category": r[3],
                             "v_score": 0.0, "k_score": r[4]}

    # WHY: Weighted combination — vector for semantics, keyword for exact match
    ranked = []
    for chunk_id, data in scores.items():
        combined = VECTOR_WEIGHT * data["v_score"] + KEYWORD_WEIGHT * data["k_score"]
        ranked.append((chunk_id, data["content"], data["filename"], data["category"], combined))

    ranked.sort(key=lambda x: x[4], reverse=True)

    # WHY: Prefer chunks from different transcripts for diversity
    seen_files: set[str] = set()
    diverse: list[tuple] = []
    remaining: list[tuple] = []
    for r in ranked:
        if r[2] not in seen_files:
            diverse.append(r)
            seen_files.add(r[2])
        else:
            remaining.append(r)

    return (diverse + remaining)[:limit]
