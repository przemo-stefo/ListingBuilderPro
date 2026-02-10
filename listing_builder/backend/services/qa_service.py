# backend/services/qa_service.py
# Purpose: Expert Q&A — answer Amazon questions using Inner Circle transcript RAG
# NOT for: Listing optimization (that's optimizer_service.py)

from __future__ import annotations

import asyncio
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from sqlalchemy import text
from config import settings
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"
MAX_CONTEXT_CHARS = 6000  # WHY: More context for Q&A than for optimization prompts


def _search_all_categories(db: Session, query: str, max_chunks: int = 8) -> str:
    """Search ALL knowledge chunks regardless of category. Returns formatted context."""
    try:
        rows = db.execute(
            text("""
                SELECT content, filename, category,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
                FROM knowledge_chunks
                WHERE search_vector @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"query": query, "limit": max_chunks},
        ).fetchall()

        if not rows:
            return ""

        parts = []
        total_len = 0
        for row in rows:
            chunk = f"[{row[2]} — {row[1]}]\n{row[0]}"
            if total_len + len(chunk) > MAX_CONTEXT_CHARS:
                break
            parts.append(chunk)
            total_len += len(chunk)

        return "\n\n".join(parts)

    except Exception as e:
        logger.warning("qa_search_error", error=str(e))
        return ""


def _build_qa_prompt(question: str, context: str) -> str:
    """Build system prompt with expert knowledge context for Q&A."""
    context_block = ""
    if context:
        context_block = f"""
EXPERT KNOWLEDGE FROM INNER CIRCLE TRANSCRIPTS:
{context}

"""
    return f"""You are an expert Amazon marketplace consultant with deep knowledge from Inner Circle training transcripts. Answer the user's question using the expert knowledge provided below.

{context_block}Rules:
- Answer based on the expert knowledge when available
- Be specific and actionable — give concrete steps, not vague advice
- If the knowledge doesn't cover the question, say so honestly but still give your best advice
- Use examples when helpful
- Keep answers concise but complete
- Answer in the same language as the question

Question: {question}"""


async def ask_expert(
    question: str,
    db: Session,
) -> Dict:
    """
    RAG-powered Q&A: search knowledge base → inject into Groq prompt → return answer.
    """
    # WHY: Search all categories — Q&A can be about anything (keywords, PPC, ranking, etc.)
    context = _search_all_categories(db, question)

    logger.info(
        "qa_question",
        question=question[:80],
        context_len=len(context),
        has_context=bool(context),
    )

    prompt = _build_qa_prompt(question, context)

    # WHY: Higher temperature (0.6) for more natural conversational answers
    # WHY: Try all available keys to handle 429 rate limits
    def _call_with_rotation():
        keys = settings.groq_api_keys
        last_error = None
        for i, key in enumerate(keys):
            try:
                client = Groq(api_key=key)
                return client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,
                    max_tokens=1500,
                )
            except Exception as e:
                last_error = e
                if "429" in str(e) or "rate_limit" in str(e):
                    logger.warning("qa_groq_rate_limit", key_index=i)
                    continue
                raise
        raise last_error

    response = await asyncio.to_thread(_call_with_rotation)

    answer = response.choices[0].message.content.strip()

    # WHY: Count sources so frontend can show "Based on X transcript excerpts"
    source_count = context.count("[") if context else 0

    return {
        "answer": answer,
        "sources_used": source_count,
        "has_context": bool(context),
    }
