# backend/services/video_render.py
# Purpose: Video rendering entry point — dispatch to template, encode MP4
# NOT for: Template logic (video_templates.py), core utils (video_core.py)

import base64
import tempfile
from typing import Any, Dict, List, Optional

import numpy as np
from moviepy import ImageSequenceClip

from services.video_core import FPS
from services.video_templates import render_product_highlight, render_feature_breakdown, render_sale_promo

# WHY: Metadata for /templates endpoint — frontend shows template picker
AVAILABLE_TEMPLATES = {
    "product_highlight": {
        "name": "Prezentacja produktu",
        "desc": "5 slajdow: hero, produkt, cechy (x2), CTA",
        "slides": 5,
    },
    "feature_breakdown": {
        "name": "Rozklad cech",
        "desc": "Intro + kazda cecha osobno z duzym numerem + CTA",
        "slides": "2 + liczba cech (max 5)",
    },
    "sale_promo": {
        "name": "Promocja / wyprzedaz",
        "desc": "Produkt + cena, PROMOCJA, cechy, CTA z urgency",
        "slides": 4,
    },
}

TEMPLATE_RENDERERS = {
    "product_highlight": render_product_highlight,
    "feature_breakdown": render_feature_breakdown,
    "sale_promo": render_sale_promo,
}


def render_video(
    template: str,
    product_name: str,
    brand: str,
    features: List[str],
    theme: str = "dark_premium",
    image_url: Optional[str] = None,
    original_price: Optional[str] = None,
    sale_price: Optional[str] = None,
) -> Dict[str, Any]:
    """Render TikTok 9:16 video and return base64-encoded MP4."""
    renderer = TEMPLATE_RENDERERS.get(template)
    if not renderer:
        raise ValueError(f"Nieznany szablon: {template}")

    kwargs = {
        "product_name": product_name,
        "brand": brand,
        "features": features or ["Produkt premium"],
        "theme": theme,
        "image_url": image_url,
    }

    # WHY: sale_promo needs price fields, others ignore them
    if template == "sale_promo":
        kwargs["original_price"] = original_price
        kwargs["sale_price"] = sale_price

    frames = renderer(**kwargs)
    video_b64 = _encode_mp4(frames)

    return {
        "video_base64": video_b64,
        "template": template,
        "format": "mp4",
        "resolution": "1080x1920",
        "fps": FPS,
    }


def _encode_mp4(frames: List[np.ndarray]) -> str:
    """Encode numpy frames to MP4 via MoviePy + FFmpeg, return base64."""
    clip = ImageSequenceClip(frames, fps=FPS)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
        clip.write_videofile(
            tmp.name,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="fast",
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
            logger=None,
        )
        tmp.seek(0)
        return base64.b64encode(tmp.read()).decode("utf-8")
