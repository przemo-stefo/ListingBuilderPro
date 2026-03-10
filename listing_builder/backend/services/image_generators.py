# backend/services/image_generators.py
# Purpose: Pillow-based image generators for Amazon A+ Content infographics
# NOT for: Gemini API calls (image_gemini.py) or orchestration (image_service.py)

from __future__ import annotations

import io
import math
from typing import Dict, List

from PIL import Image, ImageDraw

from services.image_core import (
    font, hex_to_rgb, get_palette, wrap_text, rounded_rect,
    draw_check, draw_cross,
)

# WHY: Amazon A+ Content standard module width
W = 970


def generate_feature_grid(product_name: str, features: List[Dict[str, str]],
                          theme: str = "dark_premium") -> bytes:
    """2x3 feature grid with numbered badges and accent stripes.

    WHY: #1 most used Amazon A+ module. 80% visual, 20% text.
    """
    p = get_palette(theme)
    n = min(len(features), 6)
    rows = math.ceil(n / 2)
    card_h, gap, header_h = 140, 16, 90
    h = header_h + rows * (card_h + gap) + 50
    img = Image.new("RGB", (W, h), hex_to_rgb(p["bg"]))
    draw = ImageDraw.Draw(img)

    # Header
    title_f = font(32, bold=True)
    draw.text((W // 2, 35), product_name[:55], fill=hex_to_rgb(p["text"]),
              font=title_f, anchor="mt")
    bar_w = min(280, draw.textbbox((0, 0), product_name[:55], font=title_f)[2])
    draw.rounded_rectangle(
        [(W // 2 - bar_w // 2, 72), (W // 2 + bar_w // 2, 77)],
        radius=3, fill=hex_to_rgb(p["accent"]),
    )

    # Cards
    card_w = (W - gap * 3) // 2
    head_f, body_f, num_f = font(17, True), font(13, False), font(16, True)

    for i, feat in enumerate(features[:6]):
        col, row = i % 2, i // 2
        x = gap + col * (card_w + gap)
        y = header_h + row * (card_h + gap)

        rounded_rect(draw, (x, y, x + card_w, y + card_h), r=10,
                     fill=hex_to_rgb(p["card"]), outline=hex_to_rgb(p["border"]))
        # Left accent stripe
        draw.rounded_rectangle([(x, y + 12), (x + 4, y + card_h - 12)],
                               radius=2, fill=hex_to_rgb(p["accent"]))
        # Number badge (ring + filled circle)
        bcx, bcy = x + 30, y + 36
        draw.ellipse([(bcx - 18, bcy - 18), (bcx + 18, bcy + 18)],
                     outline=hex_to_rgb(p["accent"]), width=2)
        draw.ellipse([(bcx - 14, bcy - 14), (bcx + 14, bcy + 14)],
                     fill=hex_to_rgb(p["accent"]))
        draw.text((bcx, bcy), str(i + 1), fill=(255, 255, 255), font=num_f, anchor="mm")
        # Headline + description
        draw.text((x + 58, y + 22), feat.get("headline", f"Feature {i+1}")[:35],
                  fill=hex_to_rgb(p["text"]), font=head_f)
        for li, line in enumerate(wrap_text(draw, feat.get("description", "")[:180], body_f, card_w - 70)[:4]):
            draw.text((x + 58, y + 50 + li * 20), line,
                      fill=hex_to_rgb(p["muted"]), font=body_f)

    draw.text((W // 2, h - 18), "Amazon A+ Content",
              fill=hex_to_rgb(p["border"]), font=font(10), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def generate_comparison_chart(product_name: str, brand: str,
                              points: List[Dict[str, str]],
                              theme: str = "dark_premium") -> bytes:
    """Comparison chart: brand vs competition with check/cross icons.

    WHY: #1 conversion driver in A+ Content according to Amazon seller research.
    """
    p = get_palette(theme)
    n = min(len(points), 8)
    row_h, header_h = 56, 120
    h = header_h + 48 + n * row_h + 40
    img = Image.new("RGB", (W, h), hex_to_rgb(p["bg"]))
    draw = ImageDraw.Draw(img)

    title_f, sub_f = font(28, True), font(13, False)
    col_f, row_f, val_f = font(15, True), font(14, False), font(13, True)

    # Header
    draw.text((W // 2, 30), f"Dlaczego {brand}?", fill=hex_to_rgb(p["text"]),
              font=title_f, anchor="mt")
    draw.text((W // 2, 65), product_name[:60], fill=hex_to_rgb(p["muted"]),
              font=sub_f, anchor="mt")
    draw.rounded_rectangle([(W // 2 - 40, 88), (W // 2 + 40, 92)], radius=2,
                           fill=hex_to_rgb(p["accent"]))

    feat_x, ours_x, them_x = 50, 620, 830
    table_y = header_h

    # Column header
    rounded_rect(draw, (30, table_y, W - 30, table_y + 44), r=8,
                 fill=hex_to_rgb(p["accent2"]))
    draw.text((feat_x, table_y + 22), "Cecha", fill=(255, 255, 255), font=col_f, anchor="lm")
    draw.text((ours_x, table_y + 22), brand[:20], fill=(255, 255, 255), font=col_f, anchor="mm")
    draw.text((them_x, table_y + 22), "Inni", fill=(255, 255, 255), font=col_f, anchor="mm")

    for i, pt in enumerate(points[:n]):
        y = table_y + 48 + i * row_h
        if i % 2 == 0:
            rounded_rect(draw, (30, y, W - 30, y + row_h - 4), r=6,
                         fill=hex_to_rgb(p["card"]))
        cy = y + row_h // 2 - 2
        draw.text((feat_x, cy), pt.get("feature", "")[:40],
                  fill=hex_to_rgb(p["text"]), font=row_f, anchor="lm")

        # WHY: Check/cross for boolean, wrapped text for specific values
        _draw_value_cell(draw, ours_x, cy, pt.get("ours", "yes"),
                         hex_to_rgb(p["success"]), val_f, is_positive=True)
        _draw_value_cell(draw, them_x, cy, pt.get("others", "no"),
                         hex_to_rgb(p["danger"]), val_f, is_positive=False)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def _draw_value_cell(draw: ImageDraw.ImageDraw, cx: int, cy: int, value: str,
                     color: tuple, fnt, is_positive: bool) -> None:
    """Draw a check/cross icon or wrapped text value in a comparison cell."""
    positive_words = {"yes", "tak", "true"}
    negative_words = {"no", "nie", "false"}
    low = value.lower()

    if is_positive and low in positive_words:
        draw_check(draw, cx, cy, color, 13)
    elif not is_positive and low in negative_words:
        draw_cross(draw, cx, cy, color, 13)
    else:
        lines = wrap_text(draw, value[:30], fnt, 180)
        for li, line in enumerate(lines[:2]):
            offset_y = cy - 7 * (len(lines) - 1) + li * 16
            draw.text((cx, offset_y), line, fill=color, font=fnt, anchor="mm")


def generate_specs_card(product_name: str, specs: List[Dict[str, str]],
                        theme: str = "dark_premium") -> bytes:
    """Technical specifications with accent dots and alternating rows."""
    p = get_palette(theme)
    n = min(len(specs), 10)
    row_h, header_h = 48, 90
    h = header_h + n * row_h + 30
    img = Image.new("RGB", (W, h), hex_to_rgb(p["bg"]))
    draw = ImageDraw.Draw(img)

    draw.text((W // 2, 30), "Specyfikacja techniczna", fill=hex_to_rgb(p["text"]),
              font=font(26, True), anchor="mt")
    draw.text((W // 2, 62), product_name[:55], fill=hex_to_rgb(p["muted"]),
              font=font(12), anchor="mt")

    label_f, value_f = font(15, True), font(15, False)
    for i, spec in enumerate(specs[:n]):
        y = header_h + i * row_h
        if i % 2 == 0:
            rounded_rect(draw, (40, y, W - 40, y + row_h - 4), r=6,
                         fill=hex_to_rgb(p["card"]))
        cy = y + row_h // 2 - 2
        draw.ellipse([(60, cy - 5), (70, cy + 5)], fill=hex_to_rgb(p["accent"]))
        draw.text((85, cy), spec.get("label", "")[:30],
                  fill=hex_to_rgb(p["text"]), font=label_f, anchor="lm")
        draw.text((W - 60, cy), spec.get("value", "")[:40],
                  fill=hex_to_rgb(p["accent"]), font=value_f, anchor="rm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def generate_hero_banner(product_name: str, headline: str,
                         subheadline: str = "",
                         theme: str = "dark_premium") -> bytes:
    """970x300 A+ Content header banner with diagonal stripes and gradient."""
    p = get_palette(theme)
    h = 300
    img = Image.new("RGB", (W, h), hex_to_rgb(p["bg"]))
    draw = ImageDraw.Draw(img)

    bg = hex_to_rgb(p["bg"])
    accent = hex_to_rgb(p["accent"])
    a2 = hex_to_rgb(p["accent2"])

    # WHY: Full-height gradient gives depth
    for y in range(h):
        t = y / h
        r = int(bg[0] + (a2[0] - bg[0]) * t * 0.15)
        g = int(bg[1] + (a2[1] - bg[1]) * t * 0.15)
        b = int(bg[2] + (a2[2] - bg[2]) * t * 0.15)
        draw.line([(0, y), (W, y)], fill=(r, g, min(255, b)))

    # Diagonal stripes (subtle, overlaid at 92% bg opacity)
    for i in range(4):
        x_off = 120 + i * 220
        draw.polygon([(x_off, 0), (x_off + 60, 0), (x_off - 40, h), (x_off - 100, h)],
                     fill=accent)
    overlay = Image.new("RGBA", (W, h), (*bg, 235))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent bars (top, bottom, left)
    draw.rectangle([(0, 0), (W, 4)], fill=accent)
    draw.rectangle([(0, h - 2), (W, h)], fill=accent)
    draw.rectangle([(0, 0), (6, h)], fill=accent)

    # Headline + underline
    hf = font(40, bold=True)
    draw.text((W // 2, h // 2 - 35), headline[:70], fill=hex_to_rgb(p["text"]),
              font=hf, anchor="mm")
    hl_w = min(300, draw.textbbox((0, 0), headline[:70], font=hf)[2])
    draw.rounded_rectangle(
        [(W // 2 - hl_w // 2, h // 2 - 8), (W // 2 + hl_w // 2, h // 2 - 4)],
        radius=2, fill=accent,
    )

    if subheadline:
        draw.text((W // 2, h // 2 + 20), subheadline[:100], fill=hex_to_rgb(p["muted"]),
                  font=font(18, False), anchor="mm")

    draw.text((W // 2, h - 22), product_name[:55], fill=accent,
              font=font(12, True), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()
