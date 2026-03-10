# backend/services/image_gemini.py
# Purpose: Gemini Image Gen API integration for premium AI-generated infographics
# NOT for: Pillow rendering (image_generators.py) or orchestration (image_service.py)

from __future__ import annotations

import base64
from typing import Dict, Optional

import structlog

from services.image_core import PALETTES, sanitize_for_prompt

logger = structlog.get_logger()


def _generate_with_gemini(prompt: str, api_key: str) -> Optional[bytes]:
    """Generate an image using Gemini 2.5 Flash Image via REST API.

    WHY: REST API works with any google-generativeai version — no SDK compatibility issues.
    Returns PNG bytes or None on failure.
    """
    try:
        import requests as req
    except ImportError:
        logger.warning("gemini_image_no_requests", error="requests package not installed")
        return None

    try:
        # WHY: API key in header (not URL) — prevents key leaking to logs/proxies
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
        }
        resp = req.post(url, json=payload, headers=headers, timeout=90)
        if resp.status_code != 200:
            logger.warning("gemini_image_api_error", status=resp.status_code)
            return None

        data = resp.json()
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        return None
    except (req.RequestException, ValueError, KeyError) as e:
        logger.warning("gemini_image_gen_failed", error=str(e))
        return None


def _theme_style_block(theme: str) -> str:
    """Build style description from palette — so Gemini prompts respect theme choice."""
    p = PALETTES.get(theme, PALETTES["dark_premium"])
    return (
        f"Background: {p['bg']}. Cards/rows: {p['card']}. "
        f"Accent color: {p['accent']}. Secondary: {p['accent2']}. "
        f"Text: {p['text']}. Muted text: {p['muted']}. "
        f"Success (green): {p['success']}. Danger (red): {p['danger']}."
    )


def generate_gemini_infographic(
    image_type: str, product_name: str, brand: str,
    content_data: Dict, api_key: str,
    theme: str = "dark_premium", lang: str = "pl",
) -> Optional[str]:
    """Generate a premium infographic using Gemini Image Gen API.

    Returns base64-encoded PNG or None if Gemini fails.
    """
    product_name = sanitize_for_prompt(product_name)
    brand = sanitize_for_prompt(brand)
    style = _theme_style_block(theme)

    prompts = {
        "feature_grid": f"""Create a professional Amazon A+ Content infographic (970x600px).
Product: {product_name} by {brand}
Style: {style}
Layout: Product name centered top, accent underline. 2x3 grid of feature cards with rounded corners.
Each card: numbered circle badge, bold headline, gray description.
Features:
{chr(10).join(f'{i+1}. {f.get("headline","")}: {f.get("description","")}' for i, f in enumerate(content_data.get("features", [])[:6]))}
Sans-serif typography. NO watermarks, NO photos. Language: {lang}""",

        "comparison": f"""Create a professional comparison chart image (970x600px).
Product: {product_name} by {brand}
Style: {style}
Title: "Dlaczego {brand}?" — 3-column table (Feature | {brand} | Others).
{brand} column: green checks/values. Others: red X/values.
{chr(10).join(f'- {pt.get("feature","")}: {brand}={pt.get("ours","")} vs Others={pt.get("others","")}' for pt in content_data.get("comparison", [])[:8])}
NO watermarks. Language: {lang}""",

        "hero_banner": f"""Create a premium hero banner (970x300px).
Brand: {brand} | Product: {product_name}
Style: {style}
Headline: {sanitize_for_prompt(content_data.get('hero', {}).get('headline', brand))}
Subheadline: {sanitize_for_prompt(content_data.get('hero', {}).get('subheadline', ''))}
Minimalist, no photos, premium typography. Language: {lang}""",

        "specs": f"""Create a specifications card (970x500px).
Product: {product_name}
Style: {style}
Title: "Specyfikacja techniczna". Rows with accent dot, bold label left, accent value right.
{chr(10).join(f'- {s.get("label","")}: {s.get("value","")}' for s in content_data.get("specs", [])[:10])}
Clean, readable. NO decorative elements. Language: {lang}""",
    }

    prompt = prompts.get(image_type)
    if not prompt:
        return None

    png_bytes = _generate_with_gemini(prompt, api_key)
    if png_bytes:
        return base64.b64encode(png_bytes).decode()
    return None
