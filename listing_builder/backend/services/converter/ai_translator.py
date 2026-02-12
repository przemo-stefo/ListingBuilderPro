# backend/services/converter/ai_translator.py
# Purpose: AI-powered translation (PL→DE) and content generation for marketplace listings
# NOT for: Scraping, template generation, or compliance validation

import re
import json
from typing import Dict, Optional
from html.parser import HTMLParser

import structlog
from groq import Groq

from services.converter.field_mapping import (
    COLOR_PL_TO_DE,
    MATERIAL_PL_TO_DE,
    GENDER_ALLEGRO_TO_MARKETPLACE,
    CONDITION_ALLEGRO_TO_EBAY,
)

logger = structlog.get_logger()


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags, keep text content."""

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return " ".join(self.text_parts).strip()


def strip_html(html: str) -> str:
    """Remove HTML tags, return plain text."""
    if not html:
        return ""
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()
    # Collapse whitespace
    return re.sub(r'\s+', ' ', text).strip()


def translate_color(color_pl: str) -> Optional[str]:
    """Translate Polish color to German using lookup table.
    Returns None if not found (caller should use AI fallback).
    """
    if not color_pl:
        return None
    return COLOR_PL_TO_DE.get(color_pl.lower().strip())


def translate_material(material_pl: str) -> Optional[str]:
    """Translate Polish material to German using lookup table."""
    if not material_pl:
        return None
    return MATERIAL_PL_TO_DE.get(material_pl.lower().strip())


def translate_gender(gender_pl: str, marketplace: str) -> Optional[str]:
    """Translate Polish gender to marketplace-specific value."""
    if not gender_pl:
        return None
    mapping = GENDER_ALLEGRO_TO_MARKETPLACE.get(gender_pl)
    if mapping:
        return mapping.get(marketplace)
    return None


def translate_condition(condition_pl: str) -> Optional[int]:
    """Translate Allegro condition to eBay Condition ID."""
    if not condition_pl:
        return None
    return CONDITION_ALLEGRO_TO_EBAY.get(condition_pl)


class AITranslator:
    """Translates and generates marketplace listing content using Groq.

    Uses static lookup tables first (zero latency, zero cost),
    falls back to AI for complex translations and content generation.
    """

    def __init__(self, groq_api_key: str):
        self.primary_key = groq_api_key
        self.model = "llama-3.3-70b-versatile"

    def _call_groq(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        """Groq call with key rotation + model fallback on 429.

        WHY: Tries all available keys first, then falls back to smaller model.
        """
        from config import settings
        keys = settings.groq_api_keys
        models = [self.model, "llama-3.1-8b-instant"]
        for model in models:
            for i, key in enumerate(keys):
                try:
                    client = Groq(api_key=key)
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e):
                        logger.warning("groq_rate_limit", model=model, key_index=i)
                        continue
                    logger.error("groq_call_failed", error=str(e), model=model)
                    return ""
        return ""

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Extract and parse JSON from AI response.

        WHY: Groq sometimes wraps JSON in markdown code blocks or adds text around it.
        """
        if not text:
            return None

        cleaned = text.strip()

        # Strip markdown code block if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("title_de"):
                return data
        except json.JSONDecodeError:
            pass

        # WHY: Model sometimes adds explanation text before/after the JSON
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            try:
                data = json.loads(cleaned[brace_start:brace_end + 1])
                if isinstance(data, dict) and data.get("title_de"):
                    return data
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_individual(
        self, title: str, description: str, parameters: Dict, marketplace: str
    ) -> Dict:
        """Fall back to individual API calls when batch JSON parsing fails.

        WHY: Individual methods have simpler prompts that are more reliable,
        at the cost of multiple API calls instead of one.
        """
        output = {
            "title_de": self.translate_title(title, marketplace, parameters.get("Marka", "")),
            "description_de": self.translate_description(description, marketplace),
            "short_description_de": "",
        }

        if marketplace == "amazon":
            output["bullet_points"] = self.generate_bullet_points(title, description, parameters)
            output["search_keywords"] = self.generate_search_keywords(title, description, parameters)

        color_de = translate_color(parameters.get("Kolor", ""))
        material_de = translate_material(parameters.get("Materiał", ""))
        output["color_de"] = color_de or self.translate_value(parameters.get("Kolor", ""), "color")
        output["material_de"] = material_de or self.translate_value(parameters.get("Materiał", ""), "material")

        return output

    def translate_title(
        self, title_pl: str, marketplace: str, brand: str = "", category: str = ""
    ) -> str:
        """Translate + optimize title for target marketplace.

        Each marketplace has different length limits and SEO requirements.
        AI expands from Allegro's short 75-char titles to marketplace-optimized versions.
        """
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

        result = self._call_groq(prompt, max_tokens=100)
        # Enforce character limit
        if result and len(result) > max_chars:
            result = result[:max_chars].rsplit(" ", 1)[0]
        return result or title_pl

    def translate_description(self, desc_pl: str, marketplace: str) -> str:
        """Translate product description PL→DE.

        Preserves HTML structure for eBay/Kaufland (they support HTML).
        Strips HTML for Amazon (plaintext only, max 2000 chars).
        """
        if not desc_pl:
            return ""

        if marketplace == "amazon":
            # Amazon wants plaintext, max 2000 chars
            plain_text = strip_html(desc_pl)
            prompt = f"""Translate this Polish product description to German for Amazon.de.

Polish text: {plain_text[:3000]}

Rules:
- Professional German, not machine-translated
- Max 2000 characters
- Plaintext only (no HTML, no markdown)
- Focus on features and benefits
- Return ONLY the German text"""

            result = self._call_groq(prompt, max_tokens=800)
            return result[:2000] if result else ""

        else:
            # eBay/Kaufland support HTML - translate content, keep structure
            prompt = f"""Translate this Polish HTML product description to German for {marketplace.upper()}.

Polish HTML: {desc_pl[:4000]}

Rules:
- Keep HTML tags intact (translate only text content)
- Professional German
- Return ONLY the translated HTML"""

            return self._call_groq(prompt, max_tokens=1000) or ""

    def generate_bullet_points(self, title: str, description: str, parameters: Dict) -> list:
        """Generate 5 Amazon bullet points from product data.

        Amazon doesn't have bullet points on Allegro, so AI generates them
        from the title, description, and parameters.
        """
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

        result = self._call_groq(prompt, max_tokens=600)
        if not result:
            return [""] * 5

        lines = [line.strip() for line in result.strip().split("\n") if line.strip()]
        # Pad to exactly 5 or truncate
        while len(lines) < 5:
            lines.append("")
        return lines[:5]

    def generate_search_keywords(self, title: str, description: str, parameters: Dict) -> str:
        """Generate German search keywords for Amazon.

        Amazon backend keywords (max 250 bytes) help with discoverability.
        Should include synonyms and related terms NOT in the title.
        """
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

        result = self._call_groq(prompt, max_tokens=100)
        # Enforce 250 bytes
        if result:
            while len(result.encode("utf-8")) > 250:
                result = result.rsplit(" ", 1)[0]
        return result or ""

    def translate_value(self, value: str, field_type: str) -> str:
        """Translate a single field value PL→DE using AI.

        Used as fallback when static lookup tables don't have the value.
        """
        if not value:
            return ""

        prompt = f"""Translate this Polish {field_type} to German.

Polish: {value}

Return ONLY the German translation, one word or short phrase."""

        return self._call_groq(prompt, max_tokens=20) or value

    def translate_product_batch(
        self,
        title: str,
        description: str,
        parameters: Dict,
        marketplace: str,
    ) -> Dict:
        """Translate all AI-dependent fields in a single batch call.

        WHY JSON format: The old numbered format ("1. TITLE:") caused Groq to
        return German label translations ("Titel:") instead of actual content.
        JSON keys are unambiguous — the model fills in values, not translates labels.

        Falls back to individual API calls if JSON parsing fails.
        """
        plain_desc = strip_html(description) if description else ""
        params_text = json.dumps(parameters, ensure_ascii=False) if parameters else "{}"

        # Static lookups first (zero latency, zero cost)
        color_de = translate_color(parameters.get("Kolor", ""))
        material_de = translate_material(parameters.get("Materiał", ""))

        limits = {"amazon": 200, "ebay": 80, "kaufland": 120}
        max_title = limits.get(marketplace, 150)

        # Build JSON template showing expected output structure
        json_keys = {
            "title_de": f"German SEO title, max {max_title} chars",
            "description_de": f"German description, max 2000 chars, {'plaintext only' if marketplace == 'amazon' else 'HTML allowed'}",
            "short_description_de": "German one-sentence summary, max 200 chars",
        }

        if marketplace == "amazon":
            for i in range(1, 6):
                json_keys[f"bullet_{i}"] = f"German bullet point {i}, key feature, max 500 chars"
            json_keys["search_keywords"] = "German keywords, lowercase, space-separated, max 250 bytes"

        if not color_de and parameters.get("Kolor"):
            json_keys["color_de"] = f"German translation of '{parameters['Kolor']}'"
        if not material_de and parameters.get("Materiał"):
            json_keys["material_de"] = f"German translation of '{parameters['Materiał']}'"

        prompt = f"""You are a professional Polish-to-German e-commerce translator.

TASK: Translate the Polish product below into German for {marketplace.upper()}.
Return ONLY a valid JSON object. No markdown, no explanation, no code blocks.

=== PRODUCT (Polish) ===
Title: {title}
Description: {plain_desc[:2000]}
Parameters: {params_text[:500]}

=== REQUIRED OUTPUT ===
Replace each placeholder with actual German product content:
{json.dumps(json_keys, indent=2, ensure_ascii=False)}

CRITICAL: Fill every value with REAL German content about THIS specific product. Do NOT return the placeholder descriptions."""

        raw = self._call_groq(prompt, max_tokens=1500, temperature=0.3)
        parsed = self._parse_json_response(raw)

        if not parsed:
            logger.warning("batch_json_failed_using_fallback", marketplace=marketplace)
            return self._fallback_individual(title, description, parameters, marketplace)

        output = {
            "title_de": (parsed.get("title_de", "") or "")[:max_title],
            "description_de": parsed.get("description_de", ""),
            "short_description_de": parsed.get("short_description_de", ""),
        }

        if marketplace == "amazon":
            output["bullet_points"] = [
                parsed.get("bullet_1", ""),
                parsed.get("bullet_2", ""),
                parsed.get("bullet_3", ""),
                parsed.get("bullet_4", ""),
                parsed.get("bullet_5", ""),
            ]
            output["search_keywords"] = parsed.get("search_keywords", "")

        output["color_de"] = color_de or parsed.get("color_de", parameters.get("Kolor", ""))
        output["material_de"] = material_de or parsed.get("material_de", parameters.get("Materiał", ""))

        return output

