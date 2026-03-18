# backend/services/validator_service.py
# Purpose: Orchestrator — gather data → Beast AI prompt → parse → save to DB
# NOT for: Data fetching (validator_data_sources.py) or route handling (validator_routes.py)

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Dict, Tuple

import structlog
from sqlalchemy.orm import Session

from models.validator import ValidationRun
from services.llm_providers import call_llm
from services.groq_client import call_groq, sanitize_llm_input
from services.validator_data_sources import (
    fetch_google_trends,
    fetch_allegro_competition,
    fetch_amazon_competition,
)

logger = structlog.get_logger()


def _detect_input_type(product_input: str) -> str:
    """Detect whether input is a product name, ASIN, or URL."""
    trimmed = product_input.strip()
    if trimmed.startswith("http"):
        return "url"
    if re.match(r'^[A-Z0-9]{10}$', trimmed, re.IGNORECASE):
        return "asin"
    return "name"


def _extract_product_name(product_input: str, input_type: str) -> str:
    """Extract a searchable product name from any input type."""
    if input_type == "name":
        return product_input.strip()[:200]
    if input_type == "asin":
        return product_input.strip().upper()
    # URL — extract from path
    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(product_input.strip())
        path_parts = [p for p in parsed.path.split("/") if p and p not in ("dp", "gp", "product")]
        # WHY: Amazon URL path often has product name as slug
        name = unquote(path_parts[0]).replace("-", " ") if path_parts else product_input
        return name[:200]
    except Exception:
        return product_input.strip()[:200]


def _build_prompt(product_name: str, trends_data: Dict, competition_data: Dict, marketplace: str) -> str:
    """Build Beast AI prompt with anti-konfabulacja guard."""
    return f"""Jesteś ekspertem od e-commerce i analizy rynku. Oceń potencjał sprzedażowy produktu.

PRODUKT: {sanitize_llm_input(product_name)}
MARKETPLACE: {marketplace}

=== ZWERYFIKOWANE FAKTY ===
Bazuj TYLKO na danych poniżej. NIE wymyślaj statystyk ani trendów.

TRENDY GOOGLE:
{json.dumps(trends_data, ensure_ascii=False, indent=2)}

DANE KONKURENCJI:
{json.dumps(competition_data, ensure_ascii=False, indent=2)}

=== ZADANIE ===
Oceń produkt w 6 wymiarach (score 1-10 każdy):
1. Popyt — czy jest realne zainteresowanie?
2. Konkurencja — ile jest konkurentów, jaki poziom?
3. Marża — czy ceny pozwalają na zysk?
4. Sezonowość — czy popyt jest stabilny?
5. Bariery wejścia — certyfikaty, patenty, kapitał?
6. Skalowalność — czy da się rozszerzyć na inne rynki?

Odpowiedz TYLKO JSON (bez markdown, bez ```):
{{"score": 7, "verdict": "warto", "explanation": "...", "dimensions": [{{"name": "Popyt", "score": 8, "comment": "..."}}, {{"name": "Konkurencja", "score": 6, "comment": "..."}}, {{"name": "Marża", "score": 7, "comment": "..."}}, {{"name": "Sezonowość", "score": 8, "comment": "..."}}, {{"name": "Bariery wejścia", "score": 7, "comment": "..."}}, {{"name": "Skalowalność", "score": 6, "comment": "..."}}]}}

verdict: "warto" (score>=7), "ryzykowne" (4-6), "odpusc" (<4)
explanation: 2-3 zdania po polsku, konkretne, bez ogólników."""


def _parse_llm_response(text: str) -> Dict:
    """Parse LLM JSON response, handling code blocks."""
    # WHY: Some models wrap response in ```json ... ```
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # WHY: Fallback — extract JSON object from surrounding text
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if not match:
            raise ValueError("LLM nie zwrócił poprawnego JSON")
        data = json.loads(match.group())

    # Validate
    score = int(data.get("score", 5))
    score = max(1, min(10, score))
    verdict = data.get("verdict", "ryzykowne")
    if verdict not in ("warto", "ryzykowne", "odpusc"):
        verdict = "warto" if score >= 7 else "odpusc" if score < 4 else "ryzykowne"

    return {
        "score": score,
        "verdict": verdict,
        "explanation": str(data.get("explanation", "Brak wyjaśnienia")),
        "dimensions": data.get("dimensions", []),
    }


async def analyze_product(
    product_input: str,
    marketplace: str,
    user_id: str,
    client_ip: str | None,
    db: Session,
) -> Dict:
    """Main orchestrator: parallel data gather → Beast AI → parse → save."""
    start_ms = time.time()
    input_type = _detect_input_type(product_input)
    product_name = _extract_product_name(product_input, input_type)

    # WHY: Parallel data fetching — 3 independent sources
    trends_task = fetch_google_trends(product_name)
    allegro_task = fetch_allegro_competition(product_name)
    amazon_task = fetch_amazon_competition(product_name, marketplace.upper() if marketplace != "allegro" else "DE")

    trends_data, allegro_data, amazon_data = await asyncio.gather(
        trends_task, allegro_task, amazon_task, return_exceptions=True
    )

    # WHY: Graceful degradation — if a source fails, continue with others
    if isinstance(trends_data, Exception):
        trends_data = {"available": False, "error": str(trends_data)}
    if isinstance(allegro_data, Exception):
        allegro_data = {"available": False, "error": str(allegro_data)}
    if isinstance(amazon_data, Exception):
        amazon_data = {"available": False, "error": str(amazon_data)}

    competition_data = {"allegro": allegro_data, "amazon": amazon_data}
    prompt = _build_prompt(product_name, trends_data, competition_data, marketplace)

    # WHY: Beast primary, Groq fallback. to_thread() prevents event loop blocking.
    provider_used = "beast"
    tokens_used = 0
    try:
        text, usage = await asyncio.to_thread(call_llm, "beast", "", None, prompt, 0.3, 1500)
        if usage:
            tokens_used = usage.get("total_tokens", 0)
    except Exception as e:
        logger.warning("beast_failed_fallback_groq", error=str(e))
        provider_used = "groq"
        try:
            text, usage = await asyncio.to_thread(call_groq, prompt, 0.3, 1500)
            if usage:
                tokens_used = usage.get("total_tokens", 0)
        except Exception as e2:
            logger.error("all_llm_failed", error=str(e2))
            raise ValueError("Analiza AI niedostępna. Spróbuj ponownie za chwilę.")

    parsed = _parse_llm_response(text)
    latency_ms = int((time.time() - start_ms) * 1000)

    # Save to DB
    run = ValidationRun(
        user_id=user_id,
        product_input=product_input[:500],
        input_type=input_type,
        marketplace=marketplace,
        trends_data=trends_data,
        competition_data=competition_data,
        score=parsed["score"],
        verdict=parsed["verdict"],
        explanation=parsed["explanation"],
        dimensions=parsed["dimensions"],
        provider_used=provider_used,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        client_ip=client_ip,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # WHY: Mask provider — Mateusz sees "zaawansowany model AI", never "Beast"/"qwen3"
    return {
        "id": run.id,
        "product_input": run.product_input,
        "input_type": run.input_type,
        "marketplace": run.marketplace,
        "score": run.score,
        "verdict": run.verdict,
        "explanation": run.explanation,
        "dimensions": run.dimensions,
        "provider_used": "zaawansowany model AI",
        "latency_ms": run.latency_ms,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
