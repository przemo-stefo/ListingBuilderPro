# backend/services/video_core.py
# Purpose: Core video utilities — fonts, colors, gradients, text wrapping, image loading
# NOT for: Template logic (video_templates.py) or encoding (video_render.py)

import os
import textwrap
from io import BytesIO
from typing import Tuple, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

# --- Constants ---
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_PER_SLIDE = 4  # seconds

# WHY: DejaVu is installed via fonts-dejavu-core in Dockerfile
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# WHY: 3 themes matching A+ Content image generator
THEMES = {
    "dark_premium": {
        "bg_top": (15, 15, 25),
        "bg_bottom": (5, 5, 15),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 180, 190),
        "accent": (0, 212, 255),
        "accent2": (74, 108, 247),
        "card_bg": (30, 30, 45, 200),
        "badge_bg": (0, 212, 255),
        "badge_text": (0, 0, 0),
    },
    "light": {
        "bg_top": (245, 245, 250),
        "bg_bottom": (230, 230, 240),
        "text_primary": (30, 30, 40),
        "text_secondary": (100, 100, 110),
        "accent": (74, 108, 247),
        "accent2": (155, 89, 182),
        "card_bg": (255, 255, 255, 220),
        "badge_bg": (74, 108, 247),
        "badge_text": (255, 255, 255),
    },
    "amazon_white": {
        "bg_top": (255, 255, 255),
        "bg_bottom": (245, 245, 245),
        "text_primary": (17, 17, 17),
        "text_secondary": (85, 85, 85),
        "accent": (255, 153, 0),
        "accent2": (19, 25, 33),
        "card_bg": (250, 250, 250, 230),
        "badge_bg": (255, 153, 0),
        "badge_text": (0, 0, 0),
    },
}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load DejaVu font, fallback to default if not found."""
    path = FONT_BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except (OSError, IOError):
            return ImageFont.load_default()


def create_gradient_bg(top: Tuple, bottom: Tuple) -> Image.Image:
    """Create vertical gradient background."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return img


def draw_text_centered(draw: ImageDraw.Draw, text: str, y: int, font: ImageFont.FreeTypeFont, fill: Tuple) -> int:
    """Draw text centered horizontally. Returns bottom y coordinate."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + th


def draw_text_wrapped(draw: ImageDraw.Draw, text: str, x: int, y: int, max_width: int,
                       font: ImageFont.FreeTypeFont, fill: Tuple, line_spacing: int = 10) -> int:
    """Draw wrapped text. Returns bottom y coordinate."""
    # WHY: Estimate chars per line from font size and max_width
    avg_char_w = font.size * 0.6
    chars_per_line = max(10, int(max_width / avg_char_w))
    lines = textwrap.wrap(text, width=chars_per_line)
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        current_y += (bbox[3] - bbox[1]) + line_spacing
    return current_y


def draw_rounded_rect(draw: ImageDraw.Draw, xy: Tuple, radius: int, fill: Tuple):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def load_product_image(image_bytes: bytes, target_size: Tuple[int, int] = (500, 500)) -> Optional[Image.Image]:
    """Load and resize product image from bytes."""
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def fetch_image_from_url(url: str, target_size: Tuple[int, int] = (500, 500)) -> Optional[Image.Image]:
    """Fetch product image from URL and resize."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return load_product_image(resp.content, target_size)
    except Exception:
        return None
