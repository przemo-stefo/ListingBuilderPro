# backend/services/qa_service.py
# Purpose: Expert Q&A — answer marketplace questions using RAG knowledge base
# NOT for: Listing optimization (that's optimizer_service.py)

from __future__ import annotations

import asyncio
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import search_all_categories
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"

# WHY: Mode-specific system prompt rules — controls how strictly LLM uses transcript knowledge
MODE_RULES = {
    "strict": (
        "- ONLY answer based on the expert knowledge provided above\n"
        "- If the transcripts don't cover this topic, say: "
        "\"I don't have specific information about this in my training transcripts. "
        "Please ask about Amazon keywords, listings, PPC, or ranking.\"\n"
        "- Never supplement with general knowledge\n"
        "- Cite which transcript concept your answer comes from"
    ),
    "balanced": (
        "- Answer based on the expert knowledge when available\n"
        "- Be specific and actionable — give concrete steps, not vague advice\n"
        "- If the knowledge doesn't cover the question, say so honestly but still give your best advice\n"
        "- Use examples when helpful\n"
        "- Keep answers concise but complete"
    ),
    "flexible": (
        "- Use expert knowledge as your primary source\n"
        "- Freely supplement with your general Amazon marketplace knowledge\n"
        "- Blend transcript insights with broader best practices\n"
        "- Be comprehensive — cover the topic fully"
    ),
    "bypass": (
        "- Answer purely from your general Amazon marketplace knowledge\n"
        "- Ignore any transcript context provided\n"
        "- Be comprehensive and actionable"
    ),
}


def _build_qa_prompt(question: str, context: str, mode: str = "balanced") -> str:
    """Build system prompt with expert knowledge context and mode-specific rules."""
    rules = MODE_RULES.get(mode, MODE_RULES["balanced"])

    # WHY: In bypass mode, skip RAG context entirely — pure LLM
    if mode == "bypass":
        return f"""You are an expert Amazon and e-commerce marketplace consultant. Answer the user's question.

Rules:
{rules}
- Answer in Polish (odpowiadaj po polsku) unless the user explicitly writes in English

Question: {question}"""

    context_block = ""
    if context:
        context_block = f"""
EXPERT KNOWLEDGE FROM TRAINING TRANSCRIPTS (Inner Circle + Ecom Creative Expert):
{context}

"""
    return f"""You are an expert Amazon and e-commerce marketplace consultant with deep knowledge from training transcripts covering: Amazon keywords, listings, PPC, ranking strategies, as well as video ads, creative strategies, AI tools, and marketing psychology. Answer the user's question using the expert knowledge provided below.

{context_block}Rules:
{rules}
- Answer in Polish (odpowiadaj po polsku) unless the user explicitly writes in English

Question: {question}"""


async def ask_expert(
    question: str,
    db: Session,
    mode: str = "balanced",
) -> Dict:
    """
    RAG-powered Q&A: search knowledge base → inject into Groq prompt → return answer.
    """
    # WHY: Bypass mode skips RAG entirely — no search needed
    context = ""
    source_names = []
    if mode != "bypass":
        context, source_names = await search_all_categories(db, question)

    logger.info(
        "qa_question",
        question=question[:80],
        mode=mode,
        context_len=len(context),
        has_context=bool(context),
        sources=len(source_names),
    )

    prompt = _build_qa_prompt(question, context, mode)

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

    return {
        "answer": answer,
        "sources_used": len(source_names),
        "has_context": bool(context),
        "mode": mode,
        # WHY: Source filenames displayed in frontend — builds trust in expert answers
        "sources": source_names[:10],
    }
