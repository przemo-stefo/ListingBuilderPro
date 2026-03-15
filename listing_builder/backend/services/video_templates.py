# backend/services/video_templates.py
# Purpose: TikTok 9:16 video templates — PIL frame sequences for each template type
# NOT for: Encoding (video_render.py), core utils (video_core.py)

from typing import List, Optional
from PIL import Image, ImageDraw

from services.video_core import (
    WIDTH, HEIGHT, FPS, DURATION_PER_SLIDE, THEMES,
    get_font, create_gradient_bg, draw_text_centered, draw_text_wrapped,
    draw_rounded_rect, fetch_image_from_url,
)


def render_product_highlight(product_name: str, brand: str, features: List[str],
                              theme: str, image_url: Optional[str] = None) -> List[Image.Image]:
    """5 slides: hero+brand, title+image, 2x features, CTA. Returns PIL Images."""
    t = THEMES.get(theme, THEMES["dark_premium"])
    product_img = fetch_image_from_url(image_url) if image_url else None
    slides = []

    # Slide 1: Hero + brand
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, brand.upper(), 700, get_font(48, bold=True), t["accent"])
    draw_text_centered(draw, "PREZENTUJE", 770, get_font(36), t["text_secondary"])
    draw_text_wrapped(draw, product_name, 100, 870, WIDTH - 200, get_font(56, bold=True), t["text_primary"])
    slides.append(bg)

    # Slide 2: Product image + title
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    if product_img:
        img_w, img_h = product_img.size
        x = (WIDTH - img_w) // 2
        bg.paste(product_img, (x, 400), product_img if product_img.mode == "RGBA" else None)
    draw_text_wrapped(draw, product_name, 80, 1050, WIDTH - 160, get_font(44, bold=True), t["text_primary"])
    slides.append(bg)

    # Slides 3-4: Features (2 per slide)
    for i in range(0, min(len(features), 4), 2):
        bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
        draw = ImageDraw.Draw(bg)
        y = 500
        for j in range(2):
            idx = i + j
            if idx < len(features):
                draw_rounded_rect(draw, (60, y, WIDTH - 60, y + 250), 20, t["card_bg"])
                num = f"0{idx + 1}"
                draw.text((100, y + 30), num, font=get_font(64, bold=True), fill=t["accent"])
                draw_text_wrapped(draw, features[idx], 100, y + 120, WIDTH - 220, get_font(36), t["text_primary"])
                y += 300
        slides.append(bg)

    # Slide 5: CTA
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, "ZAMOW TERAZ", 750, get_font(64, bold=True), t["accent"])
    draw_text_centered(draw, product_name, 850, get_font(36), t["text_secondary"])
    draw_rounded_rect(draw, (200, 1000, WIDTH - 200, 1100), 25, t["badge_bg"])
    draw_text_centered(draw, "SPRAWDZ OFERTE", 1025, get_font(36, bold=True), t["badge_text"])
    slides.append(bg)

    return slides


def render_feature_breakdown(product_name: str, brand: str, features: List[str],
                              theme: str, image_url: Optional[str] = None) -> List[Image.Image]:
    """Intro + individual feature slides with large numbers + CTA. Returns PIL Images."""
    t = THEMES.get(theme, THEMES["dark_premium"])
    slides = []

    # Intro slide
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, brand.upper(), 650, get_font(42, bold=True), t["accent"])
    draw_text_wrapped(draw, product_name, 80, 750, WIDTH - 160, get_font(52, bold=True), t["text_primary"])
    count_text = f"{min(len(features), 5)} KLUCZOWYCH CECH"
    draw_text_centered(draw, count_text, 950, get_font(36), t["text_secondary"])
    slides.append(bg)

    # Individual feature slides
    for i, feat in enumerate(features[:5]):
        bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
        draw = ImageDraw.Draw(bg)
        num = f"{i + 1}"
        draw_text_centered(draw, num, 500, get_font(200, bold=True), t["accent"])
        draw_rounded_rect(draw, (60, 800, WIDTH - 60, 1200), 20, t["card_bg"])
        draw_text_wrapped(draw, feat, 100, 850, WIDTH - 220, get_font(40, bold=True), t["text_primary"])
        slides.append(bg)

    # CTA
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, "WSZYSTKIE CECHY", 700, get_font(48, bold=True), t["text_primary"])
    draw_text_centered(draw, "W JEDNYM PRODUKCIE", 780, get_font(48, bold=True), t["accent"])
    draw_rounded_rect(draw, (200, 950, WIDTH - 200, 1050), 25, t["badge_bg"])
    draw_text_centered(draw, "KUP TERAZ", 975, get_font(36, bold=True), t["badge_text"])
    slides.append(bg)

    return slides


def render_sale_promo(product_name: str, brand: str, features: List[str], theme: str,
                      image_url: Optional[str] = None, original_price: Optional[str] = None,
                      sale_price: Optional[str] = None) -> List[Image.Image]:
    """4 slides: product+price, PROMOCJA+discount, features with checks, urgency CTA. Returns PIL Images."""
    t = THEMES.get(theme, THEMES["dark_premium"])
    product_img = fetch_image_from_url(image_url) if image_url else None
    slides = []

    # Slide 1: Product + price
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    if product_img:
        img_w, img_h = product_img.size
        x = (WIDTH - img_w) // 2
        bg.paste(product_img, (x, 350), product_img if product_img.mode == "RGBA" else None)
    draw_text_wrapped(draw, product_name, 80, 950, WIDTH - 160, get_font(44, bold=True), t["text_primary"])
    if original_price:
        draw_text_centered(draw, original_price, 1150, get_font(48), t["text_secondary"])
    slides.append(bg)

    # Slide 2: PROMOCJA + discount
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, "PROMOCJA", 600, get_font(80, bold=True), t["accent"])
    if original_price and sale_price:
        draw_text_centered(draw, original_price, 750, get_font(48), t["text_secondary"])
        draw.line([(340, 775), (740, 775)], fill=(255, 80, 80), width=4)
        draw_text_centered(draw, sale_price, 830, get_font(72, bold=True), t["accent"])
    else:
        draw_text_centered(draw, "SPRAWDZ CENE", 800, get_font(56, bold=True), t["text_primary"])
    slides.append(bg)

    # Slide 3: Features with checkmarks
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, "DLACZEGO WARTO?", 400, get_font(48, bold=True), t["text_primary"])
    y = 550
    for feat in features[:5]:
        draw.text((100, y), "✓", font=get_font(40, bold=True), fill=t["accent"])
        draw_text_wrapped(draw, feat, 160, y, WIDTH - 260, get_font(34), t["text_primary"])
        y += 120
    slides.append(bg)

    # Slide 4: Urgency CTA
    bg = create_gradient_bg(t["bg_top"], t["bg_bottom"])
    draw = ImageDraw.Draw(bg)
    draw_text_centered(draw, "OFERTA", 650, get_font(72, bold=True), t["accent"])
    draw_text_centered(draw, "OGRANICZONA CZASOWO", 750, get_font(48, bold=True), t["text_primary"])
    draw_rounded_rect(draw, (150, 900, WIDTH - 150, 1020), 30, t["badge_bg"])
    draw_text_centered(draw, "KUP TERAZ", 930, get_font(44, bold=True), t["badge_text"])
    draw_text_centered(draw, brand.upper(), 1100, get_font(32), t["text_secondary"])
    slides.append(bg)

    return slides
