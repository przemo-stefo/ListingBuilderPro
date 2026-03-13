# backend/services/image_service.py
# Purpose: Orchestrator — LLM content prompt + render pipeline (Gemini → Pillow fallback)
# NOT for: Image rendering (image_generators.py), Gemini API (image_gemini.py), drawing helpers (image_core.py)

from __future__ import annotations

import base64
from typing import Dict, List

import structlog

from services.image_generators import (
    generate_feature_grid, generate_comparison_chart,
    generate_specs_card, generate_hero_banner,
)
from services.image_gemini import generate_gemini_infographic

logger = structlog.get_logger()

# WHY: Ordered list — frontend shows images in this logical order
IMAGE_TYPES = ["hero_banner", "feature_grid", "comparison", "specs"]

# WHY: Dispatch table replaces if/elif chain — easier to extend, no duplication
_PILLOW_RENDERERS = {
    "feature_grid": lambda pn, br, data, th: generate_feature_grid(pn, data.get("features", []), th),
    "comparison": lambda pn, br, data, th: generate_comparison_chart(pn, br, data.get("comparison", []), th),
    "specs": lambda pn, br, data, th: generate_specs_card(pn, data.get("specs", []), th),
    "hero_banner": lambda pn, br, data, th: generate_hero_banner(
        pn, data.get("hero", {}).get("headline", br), data.get("hero", {}).get("subheadline", ""), th,
    ),
}


IMAGE_CONTENT_PROMPT = """You are an Amazon A+ Content specialist. Based on the product info below, generate STRUCTURED DATA for product infographics.

PRODUCT: {product_name}
BRAND: {brand}
BULLETS: {bullets}
DESCRIPTION: {description}
CATEGORY: {category}

Generate a JSON object with EXACTLY these sections:

1. "features" — 6 key product features for a feature grid:
   Each: {{"headline": "short 3-5 word headline", "description": "1-2 sentence benefit-focused description"}}

2. "comparison" — 6-8 comparison points (your product vs generic alternatives):
   Each: {{"feature": "comparison dimension", "ours": "yes" or specific value, "others": "no" or specific worse value}}

3. "specs" — 8-10 technical specifications:
   Each: {{"label": "Spec name", "value": "Spec value"}}

4. "hero" — hero banner content:
   {{"headline": "Powerful 5-8 word headline", "subheadline": "Supporting benefit statement"}}

REFERENCE EXAMPLE — follow this exact structure:
{{"features":[{{"headline":"Dlugi czas pracy","description":"Ciesz sie muzyka przez 60 godzin dzieki dlugiej zywotnosci baterii."}},{{"headline":"Bezprzewodowa swoboda","description":"Rozloz skrzydla dzieki technologii Bluetooth 5.3. Laczsie bez ograniczen."}},{{"headline":"Cisza i spokoj","description":"Zredukuj szumy o 42dB dzieki zaawansowanej technologii ANC."}},{{"headline":"Wygodna konstrukcja","description":"Skladana konstrukcja ulatwia przechowywanie i transport."}},{{"headline":"Najwyzsza jakosc dzwieku","description":"Technologia LDAC zapewnia pelna klarownosc dzwieku."}},{{"headline":"Latwa obsluga","description":"Intuicyjna obsluga pozwala na latwe sterowanie."}}],"comparison":[{{"feature":"Czas pracy baterii","ours":"60h","others":"20h"}},{{"feature":"Technologia ANC","ours":"tak","others":"nie"}},{{"feature":"Wersja Bluetooth","ours":"5.3","others":"4.0"}},{{"feature":"Skladana konstrukcja","ours":"tak","others":"nie"}},{{"feature":"Redukcja szumow","ours":"-42dB","others":"-20dB"}},{{"feature":"Technologia LDAC","ours":"tak","others":"nie"}}],"specs":[{{"label":"Czas pracy baterii","value":"60 godzin"}},{{"label":"Wersja Bluetooth","value":"5.3"}},{{"label":"Technologia ANC","value":"tak"}},{{"label":"Redukcja szumow","value":"-42dB"}},{{"label":"Waga","value":"280g"}},{{"label":"Impedancja","value":"32 Ohm"}},{{"label":"Pasmo przenoszenia","value":"20Hz-40kHz"}},{{"label":"Czas ladowania","value":"2h"}}],"hero":{{"headline":"Bezprzewodowa cisza i muzyka","subheadline":"60h baterii i zaawansowana technologia ANC"}}}}
{examples_block}
RULES:
- Write in the SAME LANGUAGE as the product data ({lang})
- Focus on BENEFITS, not just features — what does the customer gain?
- Comparison: highlight genuine advantages, be specific (e.g., "24 months" vs "6 months")
- Specs: include dimensions, materials, weight, certifications — things Amazon shoppers check
- Headlines: short, punchy, use action words
- NEVER invent certifications or claims not in the product data

Return ONLY valid JSON, no markdown, no explanation.
/no_think"""


def build_image_content_prompt(
    product_name: str, brand: str, bullets: List[str],
    description: str, category: str = "", lang: str = "pl",
    examples: List[Dict] | None = None,
) -> str:
    """Build structured-data prompt for LLM → infographic content generation.

    WHY examples param: RAG injects 2-3 best training examples matching category+lang.
    """
    import json as _json
    examples_block = ""
    if examples:
        parts = []
        for i, ex in enumerate(examples[:3], 1):
            # WHY: Truncate to 1500 chars — keep prompt under token limits
            ex_json = _json.dumps(ex, ensure_ascii=False, separators=(",", ":"))[:1500]
            parts.append(f"Additional example {i}:\n{ex_json}")
        examples_block = "\n".join(parts) + "\n\n"
    return IMAGE_CONTENT_PROMPT.format(
        product_name=product_name, brand=brand,
        bullets="\n".join(f"- {b}" for b in bullets[:10]),
        description=description[:2000], category=category, lang=lang,
        examples_block=examples_block,
    )


def render_all_images(
    product_name: str, brand: str, content_data: Dict,
    theme: str = "dark_premium", gemini_api_key: str = "",
) -> Dict[str, str]:
    """Render all image types. Gemini first (premium) → Pillow fallback.

    Returns {image_type: base64_png_string}.
    """
    results: Dict[str, str] = {}

    for img_type in IMAGE_TYPES:
        # WHY: Gemini produces AI-generated visuals — premium quality
        if gemini_api_key:
            try:
                b64 = generate_gemini_infographic(
                    img_type, product_name, brand, content_data,
                    gemini_api_key, theme,
                )
                if b64:
                    results[img_type] = b64
                    logger.info("image_gen_gemini_ok", type=img_type)
                    continue
            except (ValueError, KeyError, TypeError) as e:
                logger.warning("image_gen_gemini_skip", type=img_type, error=str(e))

        # WHY: Pillow fallback — always works, zero API dependency
        renderer = _PILLOW_RENDERERS.get(img_type)
        if not renderer:
            continue
        try:
            # WHY: Map image type → content_data key (they don't always match)
            data_key = {"hero_banner": "hero", "feature_grid": "features"}.get(img_type, img_type)
            if not content_data.get(data_key):
                continue
            png = renderer(product_name, brand, content_data, theme)
            results[img_type] = base64.b64encode(png).decode()
        except (ValueError, KeyError, TypeError, OSError) as e:
            logger.warning("image_gen_pillow_failed", type=img_type, error=str(e))

    return results
