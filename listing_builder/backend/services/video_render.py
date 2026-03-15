# backend/services/video_render.py
# Purpose: Video rendering entry point — dispatch to template, encode MP4 via FFmpeg pipe
# NOT for: Template logic (video_templates.py), core utils (video_core.py)

import base64
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

from services.video_core import WIDTH, HEIGHT, FPS, DURATION_PER_SLIDE
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

    slides = renderer(**kwargs)
    video_b64 = _encode_mp4_streaming(slides)

    return {
        "video_base64": video_b64,
        "template": template,
        "format": "mp4",
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": FPS,
    }


def _encode_mp4_streaming(slides: List[Image.Image]) -> str:
    """Encode PIL slides to MP4 via FFmpeg pipe — streams frames, ~12MB RAM instead of ~3.6GB.

    WHY: MoviePy ImageSequenceClip loads ALL frames into memory. With 1080x1920x3 bytes x 600 frames
    = ~3.6GB, which OOMs in 768MB container. Piping raw frames to FFmpeg uses only 2 frames at a time.
    """
    crossfade_frames = FPS // 2  # 0.5s crossfade
    hold_frames = DURATION_PER_SLIDE * FPS - crossfade_frames
    frame_size = WIDTH * HEIGHT * 3

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    # WHY: stderr to file, not PIPE — avoids deadlock when FFmpeg outputs
    # progress info faster than 64KB buffer allows while we write frames to stdin
    stderr_path = tmp_path + ".log"

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "pipe:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-preset", "ultrafast",
            "-threads", "1",
            "-an",
            tmp_path,
        ]

        with open(stderr_path, "w") as stderr_file:
            # WHY: bufsize = 1 frame avoids small-buffer stdin blocking
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=stderr_file, bufsize=WIDTH * HEIGHT * 3)

            for i, slide in enumerate(slides):
                arr = np.array(slide.convert("RGB"))

                # WHY: Write hold frames (same frame repeated)
                raw = arr.tobytes()
                for _ in range(hold_frames):
                    proc.stdin.write(raw)

                # WHY: Crossfade to next slide (skip for last)
                if i < len(slides) - 1:
                    next_arr = np.array(slides[i + 1].convert("RGB"))
                    for f in range(crossfade_frames):
                        alpha = f / crossfade_frames
                        blended = (arr * (1 - alpha) + next_arr * alpha).astype(np.uint8)
                        proc.stdin.write(blended.tobytes())
                    del next_arr

                del arr

            proc.stdin.close()
            proc.wait(timeout=120)

        if proc.returncode != 0:
            with open(stderr_path, "r") as f:
                err = f.read()[-500:]
            raise RuntimeError(f"FFmpeg error: {err}")

        with open(tmp_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    finally:
        import os
        for p in (tmp_path, stderr_path):
            try:
                os.unlink(p)
            except OSError:
                pass
