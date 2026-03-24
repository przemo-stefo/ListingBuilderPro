# backend/services/attribute_service.py
# Purpose: Orchestrator — fetch category params, build prompt, call Beast/Groq, parse response
# NOT for: Allegro API calls (allegro_categories.py) or LLM dispatch (llm_providers.py)

import asyncio
import json
import re
import time
import structlog
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from services.allegro_categories import fetch_category_parameters
from services.llm_providers import call_llm
from services.groq_client import call_groq, sanitize_llm_input
from models.attribute_run import AttributeRun

logger = structlog.get_logger()


def _build_prompt(product_input: str, category_name: str, category_path: str, params: List[dict], marketplace: str = "allegro") -> str:
    """Build Beast/Groq prompt with category parameter schema.

    WHY: Structured prompt with parameter types + options prevents LLM konfabulacja.
    DICTIONARY params get explicit option lists so LLM can only pick valid values.
    """
    safe_input = sanitize_llm_input(product_input)

    required_section = []
    optional_section = []

    for p in params:
        line = f"- {p['name']} (ID: {p['id']}, typ: {p['type']}"
        if p.get("unit"):
            line += f", jednostka: {p['unit']}"
        if p.get("restrictions"):
            r = p["restrictions"]
            if r.get("min") is not None or r.get("max") is not None:
                line += f", zakres: {r.get('min', '?')}-{r.get('max', '?')}"
        line += ")"

        if p["type"] == "DICTIONARY" and p.get("options"):
            opts = p["options"][:30]  # WHY: Limit to 30 options to save tokens
            opts_str = ", ".join(f'"{o["value"]}" (id:{o["id"]})' for o in opts)
            line += f"\n  OPCJE: [{opts_str}]"

        if p.get("required"):
            required_section.append(line)
        else:
            optional_section.append(line)

    # WHY: Kaufland uses Allegro categories but needs extra generic attributes
    kaufland_extra = ""
    if marketplace == "kaufland":
        kaufland_extra = """
DODATKOWE ATRYBUTY KAUFLAND (dodaj jeśli możesz wywnioskować z tytułu):
- Kolor (STRING)
- Rozmiar (STRING)
- Waga produktu (FLOAT, w kg)
- Płeć (DICTIONARY: Mężczyzna, Kobieta, Unisex, Dziecko)
- Materiał (STRING)
- Marka/Brand (STRING)
- EAN/GTIN (STRING — wpisz null jeśli nieznany)
"""

    marketplace_label = "Allegro" if marketplace == "allegro" else "Kaufland"

    prompt = f"""Jesteś ekspertem od e-commerce {marketplace_label}. Uzupełnij atrybuty produktowe na podstawie tytułu.

ZWERYFIKOWANE FAKTY:
- Produkt: {safe_input}
- Kategoria: {category_name} ({category_path})
- Bazuj WYŁĄCZNIE na tytule produktu i wiedzy o kategorii
- Dla DICTIONARY — wybierz TYLKO z podanych opcji (podaj ID i value)
- Jeśli nie możesz ustalić wartości — wpisz null

WYMAGANE PARAMETRY:
{chr(10).join(required_section) if required_section else "(brak)"}

OPCJONALNE PARAMETRY:
{chr(10).join(optional_section) if optional_section else "(brak)"}
{kaufland_extra}
Odpowiedz TYLKO poprawnym JSON (bez markdown, bez komentarzy):
[{{"name": "...", "value": "...", "param_id": "...", "required": true/false}}]

Dla DICTIONARY: value = wartość z listy OPCJE, param_id = id parametru.
Dla STRING/INTEGER/FLOAT: value = sensowna wartość, param_id = id parametru.
Jeśli nie znasz wartości: value = null."""

    return prompt


def _parse_attributes_response(raw: str, params: List[dict]) -> List[dict]:
    """Parse LLM JSON response and validate against parameter schema.

    WHY: LLM may return markdown-wrapped JSON or malformed output.
    We try json.loads first, then regex extraction as fallback.
    """
    # WHY: Build lookup by both ID and name for flexible matching
    param_lookup: Dict[str, dict] = {}
    for p in params:
        param_lookup[p["id"]] = p
        param_lookup[p["name"].lower()] = p

    # Try direct JSON parse
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        # WHY: Regex fallback — extract JSON array from LLM noise
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                items = json.loads(match.group())
            except json.JSONDecodeError:
                logger.error("attribute_parse_failed", raw_length=len(raw))
                return []
        else:
            return []

    if not isinstance(items, list):
        return []

    parsed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        param_id = str(item.get("param_id", ""))
        name = item.get("name", "")

        # WHY: Match against known params to get type/options
        ref = param_lookup.get(param_id) or param_lookup.get(name.lower())

        parsed.append({
            "name": name,
            "value": item.get("value"),
            "param_id": param_id,
            "required": item.get("required", False),
            "type": ref["type"] if ref else "STRING",
            "options": ref.get("options", []) if ref else [],
        })

    return parsed


async def generate_attributes(
    product_input: str,
    category_id: str,
    category_name: str,
    category_path: str,
    marketplace: str,
    user_id: str,
    client_ip: Optional[str],
    db: Session,
) -> Dict:
    """Orchestrate attribute generation: params → prompt → Beast/Groq → parse → save."""
    start = time.time()

    # Step 1: Fetch category parameters from Allegro
    params = await fetch_category_parameters(category_id)
    if not params:
        raise ValueError(f"Nie znaleziono parametrów dla kategorii {category_id}")

    # Step 2: Build prompt
    prompt = _build_prompt(product_input, category_name, category_path, params, marketplace)

    # Step 3: Call Beast primary, Groq fallback
    provider_used = "beast"
    tokens_used = 0
    try:
        raw_text, usage = await asyncio.to_thread(
            call_llm, "beast", "", None, prompt, 0.2, 2000,
        )
        if usage:
            tokens_used = usage.get("total_tokens", 0)
    except Exception as e:
        logger.warning("beast_failed_fallback_groq", error=str(e))
        provider_used = "groq"
        try:
            raw_text, usage = await asyncio.to_thread(
                call_groq, prompt, 0.2, 2000,
            )
            if usage:
                tokens_used = usage.get("total_tokens", 0)
        except Exception as e2:
            logger.error("both_providers_failed", beast_error=str(e), groq_error=str(e2))
            raise ValueError("Oba providery AI niedostępne. Spróbuj ponownie za chwilę.")

    # Step 4: Parse response
    attributes = _parse_attributes_response(raw_text, params)

    if not attributes:
        logger.warning("empty_attributes_result", raw_length=len(raw_text))
        raise ValueError("AI nie zwróciło atrybutów. Spróbuj bardziej szczegółowy tytuł produktu.")

    latency_ms = int((time.time() - start) * 1000)

    # Step 5: Save to DB
    run = AttributeRun(
        user_id=user_id,
        product_input=product_input[:500],
        marketplace=marketplace,
        category_id=category_id,
        category_name=category_name,
        category_path=category_path,
        attributes=attributes,
        params_count=len(attributes),
        provider_used=provider_used,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        client_ip=client_ip,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # WHY: Provider masking — Mateusz sees "zaawansowany model AI", not "beast"/"groq"
    return {
        "id": run.id,
        "product_input": run.product_input,
        "category_name": category_name,
        "category_path": category_path,
        "attributes": attributes,
        "params_count": len(attributes),
        "provider_used": "zaawansowany model AI",
        "latency_ms": latency_ms,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
