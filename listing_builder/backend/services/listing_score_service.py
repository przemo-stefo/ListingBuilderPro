# backend/services/listing_score_service.py
# Purpose: Score Amazon listings 1-10 using copywriting frameworks + Amazon TOS compliance
# NOT for: Listing optimization/generation (that's optimizer_service.py)

from __future__ import annotations

import asyncio
import json
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import search_all_categories
from services.amazon_tos_checker import check_amazon_tos
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"

# WHY: These categories contain copywriting frameworks + Amazon FBA Revolution knowledge
SCORE_CATEGORIES = [
    "copywriting", "listing_optimization",
    "conversion_optimization", "marketing_psychology",
]

SCORE_PROMPT = """Jesteś ekspertem od copywritingu Amazon opartym na frameworkach:
- Amazon FBA Revolution — Złota Formuła Listingu (CZAKO: Cecha→Zaleta→Korzyść)
- Georgi Georgiev RMBC (Research, Mechanism, Brief, Copy)
- Darek Orzechowski (polski copywriting sprzedażowy, FAB, storytelling)
- Russell Brunson (hook, story, offer, urgency)

ZASADY AMAZON TOS (PRIORYTET!):
- Tytuł: max 200 znaków, bez CAPS, bez powtórzeń słowa >2x, bez znaków specjalnych (!$?_)
- Tytuł: Brand na początku, keywords front-loaded (mobile widzi 70-90 znaków)
- Bullets: CZAKO (Cecha→Zaleta→Korzyść), najsilniejszy bullet na górze
- Bullets: 2-3 keywords naturalnie, konkretne korzyści ("zaoszczędzisz 2h" nie "najwyższa jakość")
- Opis: każde keyword RAZ (powtórzenie degraduje ranking!), max 2000 znaków
- ZABRONIONE: frazy promocyjne, roszczenia zdrowotne, kontakt, URL, ceny
- Backend: 250 bajtów max, NIGDY ASINy konkurencji, NIGDY brand names konkurencji

{tos_section}

KONTEKST EKSPERCKI Z KURSÓW:
{context}

LISTING DO OCENY:
Tytuł: {title}
Bullet points:
{bullets}
{description_section}

Oceń listing w 6 wymiarach, każdy 1-10. Odpowiedz WYŁĄCZNIE w JSON (bez markdown, bez komentarzy):
{{
  "dimensions": [
    {{
      "name": "tos_compliance",
      "score": <1-10>,
      "explanation": "<1 zdanie po polsku — czy listing jest zgodny z Amazon TOS>",
      "tip": "<1 konkretna porada>"
    }},
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
- tos_compliance: Czy listing jest W PEŁNI zgodny z Amazon TOS? (PRIORYTET! Brak zgodności = suppression)
- hook_power: Czy tytuł przyciąga uwagę? (Złota Formuła: brand + keywords front-loaded)
- benefit_clarity: Czy korzyści są jasne, nie tylko cechy? (CZAKO framework z FBA Revolution)
- persuasion: Czy użyto wyzwalaczy psychologicznych? (social proof, authority — bez zabronionych fraz!)
- keyword_integration: Czy słowa kluczowe są naturalne, nie upchane?
- call_to_action: Czy listing prowadzi do decyzji zakupowej? (bez "Buy Now" — to zabronione!)

WAŻNE: tos_compliance ma NAJWYŻSZY priorytet. Listing z naruszeniem TOS = 1/10 niezależnie od jakości copy.
Bądź surowy ale sprawiedliwy. Ocena 10 = perfekcja, rzadkość. Średni listing = 5-6."""


def _build_search_query(title: str, bullets: list[str]) -> str:
    """Build a search query from listing content for RAG retrieval."""
    parts = [title] + bullets[:2]
    return " ".join(parts)[:200]


def _build_tos_section(tos_result: Dict) -> str:
    """Format TOS violations for the LLM prompt."""
    if not tos_result.get("violations"):
        return "WYNIK TOS: Brak naruszeń wykrytych przez automat."

    lines = ["NARUSZENIA TOS WYKRYTE AUTOMATYCZNIE (uwzględnij w ocenie!):"]
    for v in tos_result["violations"][:10]:
        severity_icon = "🔴" if v["severity"] == "SUPPRESSION" else "🟡"
        lines.append(f"  {severity_icon} [{v['severity']}] {v['message']}")
    return "\n".join(lines)


def _build_prompt(
    title: str, bullets: list[str], description: str, context: str, tos_section: str,
) -> str:
    """Build the scoring prompt with listing content, RAG context, and TOS results."""
    bullets_text = "\n".join(f"- {b}" for b in bullets)
    desc_section = f"Opis:\n{description}" if description else ""

    return SCORE_PROMPT.format(
        context=context or "(brak kontekstu — oceń na podstawie wiedzy ogólnej)",
        title=title,
        bullets=bullets_text,
        description_section=desc_section,
        tos_section=tos_section,
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
                temperature=0.3,
                max_tokens=1500,
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
    backend_keywords: str = "", marketplace: str = "amazon",
) -> Dict:
    """Score a listing on 6 dimensions: TOS compliance + 5 copywriting using RAG + Groq LLM.

    WHY: TOS compliance is checked FIRST (rule-based), then passed to LLM for holistic scoring.
    This ensures the LLM doesn't miss Amazon-specific violations.
    """
    # Phase 1: Rule-based TOS check (instant, no LLM cost)
    tos_result = check_amazon_tos(title, bullets, description, backend_keywords, marketplace)
    tos_section = _build_tos_section(tos_result)

    # Phase 2: RAG context retrieval
    search_query = _build_search_query(title, bullets)
    context, source_names = await search_all_categories(db, search_query, max_chunks=6)

    logger.info("listing_score_start", title=title[:60], sources=len(source_names),
                tos_violations=tos_result["violation_count"])

    # Phase 3: LLM scoring with TOS context
    prompt = _build_prompt(title, bullets, description, context, tos_section)
    raw = await asyncio.to_thread(_call_groq_with_rotation, prompt)

    parsed = _parse_score_response(raw)
    dimensions = parsed.get("dimensions", [])

    # WHY: Calculate weighted average — TOS compliance has 2x weight
    scores = []
    for d in dimensions:
        s = d.get("score")
        if isinstance(s, (int, float)):
            weight = 2.0 if d.get("name") == "tos_compliance" else 1.0
            scores.append((s, weight))

    total_weighted = sum(s * w for s, w in scores)
    total_weight = sum(w for _, w in scores)
    overall = round(total_weighted / total_weight, 1) if total_weight > 0 else 0.0

    return {
        "overall_score": overall,
        "dimensions": dimensions,
        "sources_used": len(source_names),
        "tos_check": tos_result,
    }
