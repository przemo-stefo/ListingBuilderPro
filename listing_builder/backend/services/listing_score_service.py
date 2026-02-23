# backend/services/listing_score_service.py
# Purpose: Score Amazon listings 1-10 using copywriting frameworks (Georgi RMBC, Orzechowski, Brunson)
# NOT for: Listing optimization/generation (that's optimizer_service.py)

from __future__ import annotations

import asyncio
import json
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import search_all_categories
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"

# WHY: These categories contain copywriting frameworks from expert e-commerce courses
SCORE_CATEGORIES = [
    "copywriting", "listing_optimization",
    "conversion_optimization", "marketing_psychology",
]

SCORE_PROMPT = """Jesteś ekspertem od copywritingu Amazon opartym na frameworkach:
- Georgi Georgiev RMBC (Research, Mechanism, Brief, Copy)
- Darek Orzechowski (polski copywriting sprzedażowy, FAB, storytelling)
- Russell Brunson (hook, story, offer, urgency)

KONTEKST EKSPERCKI Z KURSÓW:
{context}

LISTING DO OCENY:
Tytuł: {title}
Bullet points:
{bullets}
{description_section}

Oceń listing w 5 wymiarach, każdy 1-10. Odpowiedz WYŁĄCZNIE w JSON (bez markdown, bez komentarzy):
{{
  "dimensions": [
    {{
      "name": "hook_power",
      "score": <1-10>,
      "explanation": "<1 zdanie po polsku — dlaczego taki wynik>",
      "tip": "<1 konkretna porada jak poprawić>"
    }},
    {{
      "name": "benefit_clarity",
      "score": <1-10>,
      "explanation": "<1 zdanie>",
      "tip": "<1 konkretna porada>"
    }},
    {{
      "name": "persuasion",
      "score": <1-10>,
      "explanation": "<1 zdanie>",
      "tip": "<1 konkretna porada>"
    }},
    {{
      "name": "keyword_integration",
      "score": <1-10>,
      "explanation": "<1 zdanie>",
      "tip": "<1 konkretna porada>"
    }},
    {{
      "name": "call_to_action",
      "score": <1-10>,
      "explanation": "<1 zdanie>",
      "tip": "<1 konkretna porada>"
    }}
  ]
}}

Wymiary:
- hook_power: Czy tytuł przyciąga uwagę? (Georgi unique mechanism, Brunson hook)
- benefit_clarity: Czy korzyści są jasne, nie tylko cechy? (FAB framework, Orzechowski)
- persuasion: Czy użyto wyzwalaczy psychologicznych? (scarcity, social proof, authority)
- keyword_integration: Czy słowa kluczowe są naturalne, nie upchane?
- call_to_action: Czy listing prowadzi do decyzji zakupowej? (Brunson offer stack)

Bądź surowy ale sprawiedliwy. Ocena 10 = perfekcja, rzadkość. Średni listing = 5-6."""


def _build_search_query(title: str, bullets: list[str]) -> str:
    """Build a search query from listing content for RAG retrieval."""
    # WHY: Combine title + first 2 bullets — gives enough signal without flooding search
    parts = [title] + bullets[:2]
    return " ".join(parts)[:200]


def _build_prompt(title: str, bullets: list[str], description: str, context: str) -> str:
    """Build the scoring prompt with listing content and RAG context."""
    bullets_text = "\n".join(f"- {b}" for b in bullets)
    desc_section = f"Opis:\n{description}" if description else ""

    return SCORE_PROMPT.format(
        context=context or "(brak kontekstu — oceń na podstawie wiedzy ogólnej)",
        title=title,
        bullets=bullets_text,
        description_section=desc_section,
    )


def _call_groq_with_rotation(prompt: str) -> str:
    """Call Groq with key rotation on 429 rate limits."""
    keys = settings.groq_api_keys
    last_error = None
    for i, key in enumerate(keys):
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # WHY: Low temp for consistent, analytical scoring
                max_tokens=1200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("score_groq_rate_limit", key_index=i)
                continue
            raise
    raise last_error


def _parse_score_response(raw: str) -> Dict:
    """Parse LLM JSON response, stripping markdown fences if present."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


async def score_listing(
    title: str, bullets: list[str], description: str, db: Session,
) -> Dict:
    """Score a listing on 5 copywriting dimensions using RAG + Groq LLM."""
    search_query = _build_search_query(title, bullets)
    context, source_names = await search_all_categories(db, search_query, max_chunks=6)

    logger.info("listing_score_start", title=title[:60], sources=len(source_names))

    prompt = _build_prompt(title, bullets, description, context)
    raw = await asyncio.to_thread(_call_groq_with_rotation, prompt)

    parsed = _parse_score_response(raw)
    dimensions = parsed.get("dimensions", [])

    # WHY: Calculate average — gives one headline number for UI display
    scores = [d["score"] for d in dimensions if isinstance(d.get("score"), (int, float))]
    overall = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "overall_score": overall,
        "dimensions": dimensions,
        "sources_used": len(source_names),
    }
