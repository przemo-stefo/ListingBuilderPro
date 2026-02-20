# backend/services/search_strategies.py
# Purpose: Low-level search functions — lexical, vector, hybrid merge
# NOT for: High-level knowledge search logic (that's knowledge_service.py)

from __future__ import annotations

import re
from sqlalchemy.orm import Session
from sqlalchemy import text

# WHY: Weights for hybrid merge — vector captures semantics, keyword captures exact terms
VECTOR_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

# WHY: Stop words removed before lexical search — plainto_tsquery fails with full sentences
# because PostgreSQL's English parser doesn't match well on wordy natural language queries.
# Extracting meaningful keywords dramatically improves tsvector recall.
STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could must need to of in on at by for with from "
    "and or but not no nor so yet if then else when while as than that this these "
    "those it its my your his her our their what which who whom how where why "
    "about into through during before after above below between under over again "
    "further once here there all each every both few more most other some such "
    "only own same too very just because also still already even much many any "
    "up out off down away back well now new get got go going like make made using "
    "write writing create creating develop developing approach use build".split()
)


def _extract_keywords(query: str, min_len: int = 3) -> str:
    """Extract meaningful keywords from natural language query for tsvector matching.

    WHY: plainto_tsquery('english', 'How to write a unique mechanism') returns few matches
    because tsquery includes stop words that dilute the search. Stripping them and keeping
    only content words gives much better recall.
    """
    words = re.findall(r'[a-zA-Z]+', query.lower())
    keywords = [w for w in words if w not in STOP_WORDS and len(w) >= min_len]
    return " ".join(keywords) if keywords else query


def lexical_search(
    db: Session, query: str, categories: list[str] | None, limit: int
) -> list[tuple]:
    """Keyword search using tsvector. Returns (id, content, filename, category, score).

    WHY: First tries the raw query, then falls back to extracted keywords if no results.
    This handles both keyword-style and natural-language queries.
    """
    rows = _lexical_query(db, query, categories, limit)

    # WHY: If raw query fails (common with full sentences), retry with extracted keywords
    if not rows:
        keywords = _extract_keywords(query)
        if keywords != query:
            rows = _lexical_query(db, keywords, categories, limit)

    return rows


def _lexical_query(
    db: Session, query: str, categories: list[str] | None, limit: int
) -> list[tuple]:
    """Execute tsvector search query."""
    if categories:
        return db.execute(
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
    return db.execute(
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
