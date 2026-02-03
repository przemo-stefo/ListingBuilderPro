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
        self.client = Groq(api_key=groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    def _call_groq(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        """Make a single Groq API call. Returns stripped text."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("groq_call_failed", error=str(e))
            return ""

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
        """Translate all AI-dependent fields for one product in a single batch.

        Combines multiple translations into fewer API calls by sending
        one comprehensive prompt. More efficient than calling translate_title,
        translate_description, etc. separately.

        Returns dict with all translated fields ready for template insertion.
        """
        plain_desc = strip_html(description) if description else ""
        params_text = json.dumps(parameters, ensure_ascii=False) if parameters else "{}"

        # Try static lookups first
        color_de = translate_color(parameters.get("Kolor", ""))
        material_de = translate_material(parameters.get("Materiał", ""))

        limits = {"amazon": 200, "ebay": 80, "kaufland": 120}
        max_title = limits.get(marketplace, 150)

        # Build batch prompt — one API call for title + description + keywords
        sections = f"""Translate this Polish product listing to German for {marketplace.upper()}.

=== PRODUCT DATA (Polish) ===
Title: {title}
Description: {plain_desc[:2000]}
Parameters: {params_text[:500]}

=== GENERATE (in German) ===

1. TITLE (max {max_title} chars, SEO-optimized for {marketplace}):
2. DESCRIPTION (max 2000 chars, {'plaintext for Amazon' if marketplace == 'amazon' else 'HTML ok'}):
3. SHORT_DESCRIPTION (max 200 chars, one-sentence summary):"""

        if marketplace == "amazon":
            sections += """
4. BULLET_1:
5. BULLET_2:
6. BULLET_3:
7. BULLET_4:
8. BULLET_5:
9. SEARCH_KEYWORDS (max 250 bytes, lowercase, spaces between words):"""

        if not color_de and parameters.get("Kolor"):
            sections += f"\n10. COLOR_DE (translate '{parameters['Kolor']}'):"
        if not material_de and parameters.get("Materiał"):
            sections += f"\n11. MATERIAL_DE (translate '{parameters['Materiał']}'):"

        sections += "\n\nReturn ONLY the numbered answers. No explanations."

        result = self._call_groq(sections, max_tokens=1500, temperature=0.3)

        # Parse the numbered response
        parsed = self._parse_batch_response(result)

        output = {
            "title_de": (parsed.get("1", "") or "")[:max_title],
            "description_de": parsed.get("2", ""),
            "short_description_de": parsed.get("3", ""),
        }

        if marketplace == "amazon":
            output["bullet_points"] = [
                parsed.get("4", ""),
                parsed.get("5", ""),
                parsed.get("6", ""),
                parsed.get("7", ""),
                parsed.get("8", ""),
            ]
            output["search_keywords"] = parsed.get("9", "")

        # Use static lookup or AI result for color/material
        output["color_de"] = color_de or parsed.get("10", parameters.get("Kolor", ""))
        output["material_de"] = material_de or parsed.get("11", parameters.get("Materiał", ""))

        return output

    def _parse_batch_response(self, text: str) -> Dict[str, str]:
        """Parse numbered response from batch translation prompt."""
        result = {}
        if not text:
            return result

        # Match patterns like "1. content" or "1: content"
        current_num = None
        current_lines = []

        for line in text.split("\n"):
            match = re.match(r'^(\d+)[.):]\s*(.*)', line)
            if match:
                # Save previous section
                if current_num is not None:
                    result[current_num] = "\n".join(current_lines).strip()
                current_num = match.group(1)
                current_lines = [match.group(2)]
            elif current_num is not None:
                current_lines.append(line)

        # Save last section
        if current_num is not None:
            result[current_num] = "\n".join(current_lines).strip()

        return result
