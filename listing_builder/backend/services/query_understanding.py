# backend/services/query_understanding.py
# Purpose: Analyze search queries to extract concepts + expand for better retrieval
# NOT for: Embedding generation (that's embedding_service.py)

from __future__ import annotations

import asyncio
import json
from groq import Groq
from config import settings
import structlog

logger = structlog.get_logger()

# WHY: 8b model is fast (~200ms) and free on Groq — perfect for lightweight preprocessing
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a search query analyzer for an Amazon marketplace knowledge base containing expert training transcripts about Amazon selling, keywords, PPC, listing optimization, and ranking.

Given a user query, extract:
1. key_concepts: 3-5 core concepts from the query
2. expanded_query: A rewritten, expanded version of the query that captures synonyms and related terms (max 100 words)
3. category_hints: Which transcript categories are most relevant (from: keyword_research, ranking, listing_optimization, ppc, conversion_optimization, general)

Respond ONLY with valid JSON, no explanation."""


async def analyze_query(query: str) -> dict | None:
    """Analyze a search query to extract concepts and expand it for better retrieval.

    Returns {"key_concepts": [...], "expanded_query": "...", "category_hints": [...]}
    or None on failure.

    WHY: Only called in hybrid/semantic mode — adds ~200ms latency, zero cost (Groq free).
    """
    if settings.rag_mode == "lexical":
        return None

    try:
        def _call():
            keys = settings.groq_api_keys
            last_error = None
            for key in keys:
                try:
                    client = Groq(api_key=key)
                    return client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": query},
                        ],
                        temperature=0,
                        max_tokens=200,
                    )
                except Exception as e:
                    last_error = e
                    if "429" in str(e) or "rate_limit" in str(e):
                        continue
                    raise
            raise last_error

        response = await asyncio.to_thread(_call)
        content = response.choices[0].message.content.strip()

        # WHY: Parse JSON — handle markdown code blocks that LLMs sometimes add
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)

        logger.info(
            "query_understood",
            original=query[:60],
            concepts=result.get("key_concepts", []),
            categories=result.get("category_hints", []),
        )

        return result

    except Exception as e:
        logger.warning("query_understanding_error", error=str(e), query=query[:60])
        return None
