# backend/services/converter/ai_prompts.py
# Purpose: Individual AI translation prompts (fallback when batch JSON fails)
# NOT for: Batch translation (ai_translator.py), static lookups (static_translations.py)

from typing import Callable, Dict, Any

from services.converter.static_translations import strip_html, translate_color, translate_material


def translate_title(
    call_groq: Callable[..., str], title_pl: str, marketplace: str, brand: str = "", category: str = ""
) -> str:
    """Translate + optimize title for target marketplace."""
    limits = {"amazon": 200, "ebay": 80, "kaufland": 120}
    max_chars = limits.get(marketplace, 150)

    prompt = f"""Translate this Polish product title to German and optimize it for {marketplace.upper()} marketplace.

Polish title: {title_pl}
Brand: {brand or 'unknown'}
Category: {category or 'unknown'}
Max length: {max_chars} characters

Rules:
- Translate to natural German (not Google Translate quality)
- Include brand name at the start
- Add relevant German search keywords
- Do NOT use promotional words (BEST, TOP, etc.)
- Do NOT exceed {max_chars} characters
- Return ONLY the German title, nothing else"""

    result = call_groq(prompt, max_tokens=100)
    if result and len(result) > max_chars:
        result = result[:max_chars].rsplit(" ", 1)[0]
    return result or title_pl


def translate_description(call_groq: Callable[..., str], desc_pl: str, marketplace: str) -> str:
    """Translate product description PL→DE.

    WHY: Amazon = plaintext max 2000 chars. eBay/Kaufland = HTML preserved.
    """
    if not desc_pl:
        return ""

    if marketplace == "amazon":
        plain_text = strip_html(desc_pl)
        prompt = f"""Translate this Polish product description to German for Amazon.de.

Polish text: {plain_text[:3000]}

Rules:
- Professional German, not machine-translated
- Max 2000 characters
- Plaintext only (no HTML, no markdown)
- Focus on features and benefits
- Return ONLY the German text"""

        result = call_groq(prompt, max_tokens=800)
        return result[:2000] if result else ""

    prompt = f"""Translate this Polish HTML product description to German for {marketplace.upper()}.

Polish HTML: {desc_pl[:4000]}

Rules:
- Keep HTML tags intact (translate only text content)
- Professional German
- Return ONLY the translated HTML"""

    return call_groq(prompt, max_tokens=1000) or ""


def generate_bullet_points(call_groq: Callable[..., str], title: str, description: str, parameters: Dict) -> list:
    """Generate 5 Amazon bullet points in German from product data."""
    plain_desc = strip_html(description) if description else ""
    params_text = ", ".join(f"{k}: {v}" for k, v in parameters.items()) if parameters else ""

    prompt = f"""Generate exactly 5 bullet points in German for an Amazon.de product listing.

Product title (Polish): {title}
Description (Polish): {plain_desc[:1500]}
Parameters: {params_text[:500]}

Rules:
- Each bullet point max 500 characters
- Write in German
- Start each with a key benefit/feature
- Be specific and factual
- No promotional language
- Format: Return exactly 5 lines, one bullet point per line
- Do NOT include bullet symbols or numbers"""

    result = call_groq(prompt, max_tokens=600)
    if not result:
        return [""] * 5

    lines = [line.strip() for line in result.strip().split("\n") if line.strip()]
    while len(lines) < 5:
        lines.append("")
    return lines[:5]


def generate_search_keywords(call_groq: Callable[..., str], title: str, description: str, parameters: Dict) -> str:
    """Generate German search keywords for Amazon (max 250 bytes)."""
    plain_desc = strip_html(description) if description else ""

    prompt = f"""Generate German search keywords for an Amazon.de product listing.

Product title (Polish): {title}
Description excerpt (Polish): {plain_desc[:500]}

Rules:
- Write in German
- Max 250 bytes total (about 40-50 words)
- Include synonyms and related search terms
- Do NOT repeat words already in the title
- Separate words with spaces (not commas)
- Lowercase only
- Return ONLY the keywords string"""

    result = call_groq(prompt, max_tokens=100)
    if result:
        while len(result.encode("utf-8")) > 250:
            result = result.rsplit(" ", 1)[0]
    return result or ""


def translate_value(call_groq: Callable[..., str], value: str, field_type: str) -> str:
    """Translate a single field value PL→DE using AI (fallback for static lookups)."""
    if not value:
        return ""

    prompt = f"""Translate this Polish {field_type} to German.

Polish: {value}

Return ONLY the German translation, one word or short phrase."""

    return call_groq(prompt, max_tokens=20) or value


def fallback_individual(
    call_groq: Callable[..., str], title: str, description: str, parameters: Dict, marketplace: str
) -> Dict:
    """Fall back to individual API calls when batch JSON parsing fails.

    WHY: Individual prompts are more reliable than batch JSON,
    at the cost of multiple API calls instead of one.
    """
    output = {
        "title_de": translate_title(call_groq, title, marketplace, parameters.get("Marka", "")),
        "description_de": translate_description(call_groq, description, marketplace),
        "short_description_de": "",
    }

    if marketplace == "amazon":
        output["bullet_points"] = generate_bullet_points(call_groq, title, description, parameters)
        output["search_keywords"] = generate_search_keywords(call_groq, title, description, parameters)

    color_de = translate_color(parameters.get("Kolor", ""))
    material_de = translate_material(parameters.get("Materiał", ""))
    output["color_de"] = color_de or translate_value(call_groq, parameters.get("Kolor", ""), "color")
    output["material_de"] = material_de or translate_value(call_groq, parameters.get("Materiał", ""), "material")

    return output
