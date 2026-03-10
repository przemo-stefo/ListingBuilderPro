# backend/services/image_core.py
# Purpose: Shared constants, palettes, font loading, and drawing helpers for image generation
# NOT for: Image rendering logic (image_generators.py) or Gemini API (image_gemini.py)

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

from PIL import ImageDraw, ImageFont

# WHY: Font path relative to backend/ → assets/fonts/
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")

_font_cache: Dict[Tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Montserrat (headlines) or Open Sans (body) with disk cache.

    WHY: Professional fonts are the #1 difference between amateur and pro design.
    Cache avoids re-reading TTF files on every call (~10+ per image).
    """
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]

    paths = [
        os.path.join(_FONT_DIR, "Montserrat.ttf" if bold else "OpenSans.ttf"),
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        try:
            loaded = ImageFont.truetype(p, size)
            _font_cache[key] = loaded
            return loaded
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color (#RGB or #RRGGBB) to (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    # WHY: Support both 3-char (#DDD) and 6-char (#DDDDDD) hex colors
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# WHY: Research-backed palettes. Amazon shoppers respond to clean, high-contrast designs.
PALETTES: Dict[str, Dict[str, str]] = {
    "dark_premium": {
        "bg": "#0B0F19", "card": "#131926", "accent": "#00B4D8",
        "accent2": "#0077B6", "text": "#FFFFFF", "muted": "#94A3B8",
        "border": "#1E293B", "success": "#22C55E", "danger": "#EF4444",
        "highlight": "#F59E0B",
    },
    "light_clean": {
        "bg": "#FFFFFF", "card": "#F8FAFC", "accent": "#0066FF",
        "accent2": "#3B82F6", "text": "#0F172A", "muted": "#64748B",
        "border": "#E2E8F0", "success": "#16A34A", "danger": "#DC2626",
        "highlight": "#EA580C",
    },
    "amazon_white": {
        "bg": "#FFFFFF", "card": "#FFF7ED", "accent": "#FF9900",
        "accent2": "#232F3E", "text": "#0F1111", "muted": "#565959",
        "border": "#DDD", "success": "#067D62", "danger": "#CC0C39",
        "highlight": "#FF9900",
    },
}

VALID_THEMES = frozenset(PALETTES.keys())


def get_palette(theme: str) -> Dict[str, str]:
    """Return palette for theme, defaulting to dark_premium."""
    return PALETTES.get(theme, PALETTES["dark_premium"])


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    """Word-wrap text to fit within pixel width."""
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, r: int, fill: tuple,
                 outline: tuple | None = None, width: int = 1) -> None:
    """Shorthand for draw.rounded_rectangle."""
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def draw_check(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple, size: int = 14) -> None:
    """Draw a filled circle with checkmark lines."""
    r = size
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=color)
    lw = max(2, size // 5)
    draw.line([(cx - r // 2, cy), (cx - r // 6, cy + r // 2)], fill=(255, 255, 255), width=lw)
    draw.line([(cx - r // 6, cy + r // 2), (cx + r // 2, cy - r // 3)], fill=(255, 255, 255), width=lw)


def draw_cross(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple, size: int = 14) -> None:
    """Draw a filled circle with X lines."""
    r = size
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=color)
    lw = max(2, size // 5)
    s = r // 2
    draw.line([(cx - s, cy - s), (cx + s, cy + s)], fill=(255, 255, 255), width=lw)
    draw.line([(cx + s, cy - s), (cx - s, cy + s)], fill=(255, 255, 255), width=lw)


def sanitize_for_prompt(text: str) -> str:
    """Strip characters that could enable prompt injection in Gemini prompts."""
    return re.sub(r'["\'\n\r\\;{}]', '', text)[:200]
