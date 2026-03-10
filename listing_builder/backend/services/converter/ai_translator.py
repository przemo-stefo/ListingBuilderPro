# backend/services/converter/ai_translator.py
# Purpose: AI-powered batch translation (PL→DE/NL) for marketplace listings
# NOT for: Static lookups (static_translations.py), individual prompts (ai_prompts.py)

import re
import json
from typing import Dict, Optional

import structlog
from groq import Groq

from services.converter.static_translations import (
    strip_html,
    translate_color,
    translate_material,
)
from services.converter.ai_prompts import fallback_individual

logger = structlog.get_logger()


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

        WHY: Tries all available keys per model, then falls back to smaller model.
        WHY timeout=30: Prevents hanging requests from blocking the worker thread.
        """
        from config import settings
        keys = settings.groq_api_keys
        models = [self.model, "llama-3.1-8b-instant"]
        last_error = ""
        for model in models:
            for i, key in enumerate(keys):
                try:
                    client = Groq(api_key=key, timeout=30.0)
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    last_error = str(e)
                    is_rate_limit = "429" in last_error or "rate_limit" in last_error
                    logger.warning(
                        "groq_retry",
                        reason="rate_limit" if is_rate_limit else "error",
                        model=model,
                        key_index=i,
                    )
                    continue
            logger.warning("groq_all_keys_exhausted", model=model)
        logger.error("groq_all_models_exhausted", last_error=last_error[:200])
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
            # WHY: Check for title_de OR title_nl (BOL uses Dutch)
            if isinstance(data, dict) and (data.get("title_de") or data.get("title_nl")):
                return data
        except json.JSONDecodeError:
            pass

        # WHY: Model sometimes adds explanation text before/after the JSON
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            try:
                data = json.loads(cleaned[brace_start:brace_end + 1])
                if isinstance(data, dict) and (data.get("title_de") or data.get("title_nl")):
                    return data
            except json.JSONDecodeError:
                pass

        return None

    def translate_product_batch(
        self, title: str, description: str, parameters: Dict, marketplace: str,
    ) -> Dict:
        """Translate all AI-dependent fields in one batch call.

        Falls back to individual API calls (ai_prompts.py) if JSON parsing fails.
        """
        plain_desc = strip_html(description) if description else ""
        params_text = json.dumps(parameters, ensure_ascii=False) if parameters else "{}"

        # WHY: BOL = Dutch, everything else = German
        is_bol = marketplace == "bol"
        lang = "Dutch" if is_bol else "German"
        suffix = "nl" if is_bol else "de"

        # Static lookups first (zero latency, zero cost) — German only
        color_static = translate_color(parameters.get("Kolor", "")) if not is_bol else None
        material_static = translate_material(parameters.get("Materiał", "")) if not is_bol else None

        limits = {"amazon": 200, "ebay": 80, "kaufland": 120, "bol": 500}
        max_title = limits.get(marketplace, 150)

        json_keys = {
            f"title_{suffix}": f"{lang} SEO title, max {max_title} chars",
            f"description_{suffix}": f"{lang} description, max 2000 chars, {'plaintext only' if marketplace in ('amazon', 'bol') else 'HTML allowed'}",
            f"short_description_{suffix}": f"{lang} one-sentence summary, max {'300' if is_bol else '200'} chars",
        }

        if marketplace == "amazon":
            for i in range(1, 6):
                json_keys[f"bullet_{i}"] = f"German bullet point {i}, key feature, max 500 chars"
            json_keys["search_keywords"] = "German keywords, lowercase, space-separated, max 250 bytes"

        if is_bol:
            for i in range(1, 9):
                json_keys[f"bullet_nl_{i}"] = f"Dutch bullet point {i}, key feature, max 300 chars"

        if not color_static and parameters.get("Kolor"):
            json_keys[f"color_{suffix}"] = f"{lang} translation of '{parameters['Kolor']}'"
        if not material_static and parameters.get("Materiał"):
            json_keys[f"material_{suffix}"] = f"{lang} translation of '{parameters['Materiał']}'"

        prompt = f"""You are a professional Polish-to-{lang} e-commerce translator.

TASK: Translate the Polish product below into {lang} for {marketplace.upper()}.
Return ONLY a valid JSON object. No markdown, no explanation, no code blocks.

=== PRODUCT (Polish) ===
Title: {title}
Description: {plain_desc[:2000]}
Parameters: {params_text[:500]}

=== REQUIRED OUTPUT ===
Replace each placeholder with actual {lang} product content:
{json.dumps(json_keys, indent=2, ensure_ascii=False)}

CRITICAL: Fill every value with REAL {lang} content about THIS specific product. Do NOT return the placeholder descriptions."""

        raw = self._call_groq(prompt, max_tokens=1500, temperature=0.3)
        parsed = self._parse_json_response(raw)

        if not parsed:
            logger.warning("batch_json_failed_using_fallback", marketplace=marketplace)
            if not is_bol:
                return fallback_individual(self._call_groq, title, description, parameters, marketplace)
            return {}

        output = {
            f"title_{suffix}": (parsed.get(f"title_{suffix}", "") or "")[:max_title],
            f"description_{suffix}": parsed.get(f"description_{suffix}", ""),
            f"short_description_{suffix}": parsed.get(f"short_description_{suffix}", ""),
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

        if is_bol:
            output["bullet_points_nl"] = [
                parsed.get(f"bullet_nl_{i}", "") for i in range(1, 9)
            ]

        output[f"color_{suffix}"] = color_static or parsed.get(f"color_{suffix}", parameters.get("Kolor", ""))
        output[f"material_{suffix}"] = material_static or parsed.get(f"material_{suffix}", parameters.get("Materiał", ""))

        return output
