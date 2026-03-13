# backend/services/comfyui_service.py
# Purpose: ComfyUI pipeline — build workflow, upload image, queue, poll, return video
# NOT for: HTTP endpoints (that's video_routes.py) or image fetching (product_image_fetcher.py)

import base64
import httpx
import time
import uuid
import structlog

from pydantic import BaseModel
from typing import Optional

logger = structlog.get_logger()

# WHY: ComfyUI via Tailscale — only accessible from Tailscale peers
COMFYUI_URL = "http://100.99.20.51:8188"


class VideoStatusResponse(BaseModel):
    status: str
    progress: Optional[float] = None
    video_base64: Optional[str] = None
    error: Optional[str] = None
    prompt_id: Optional[str] = None


def build_wan_workflow(image_name: str, positive_prompt: str) -> dict:
    """Build ComfyUI API workflow for Wan 2.2 5B image-to-video.

    WHY: Optimized settings based on community research:
    - denoise=0.4 preserves text/labels on products (1.0 destroys them)
    - steps=14 is sweet spot (>14 no quality gain)
    - cfg=5.5 balances prompt adherence and stability
    - euler+simple matches WAN training schedule
    - Prompt should describe MOTION only (image already shows subject)
    """
    # WHY: For I2V, wrap user prompt with motion + quality instructions.
    # Research: WAN 2.2 prompts work best at 80-120 words.
    # TESTED: denoise 0.25 + minimal motion = sharpest text on products.
    # Static zoom preserves labels better than orbit/dolly.
    motion_prefix = (
        "Static product shot, very subtle gentle zoom in. "
    )
    motion_suffix = (
        ". Clean product realism, studio softbox lighting from above. "
        "All text, logos and labels remain perfectly sharp and undistorted. "
        "No camera rotation. Minimal movement. Product stays perfectly still."
    )
    full_prompt = motion_prefix + positive_prompt + motion_suffix

    return {
        "37": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "default"},
        },
        "38": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"},
        },
        "39": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "wan2.2_vae.safetensors"},
        },
        "48": {
            "class_type": "ModelSamplingSD3",
            "inputs": {"model": ["37", 0], "shift": 8.0},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["38", 0], "text": full_prompt},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            # WHY: WAN 2.2 obeys negatives aggressively. Product-specific bans
            # per community research: geometry distortion, text warping, phantom objects.
            "inputs": {"clip": ["38", 0], "text": (
                "low quality, blurry, morphing, flickering, text distortion, label warping, "
                "shaky camera, geometry distortion, edges bending, surface reflections unstable, "
                "phantom duplicate objects, painterly texture, text smearing, motion blur"
            )},
        },
        "57": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        "55": {
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "vae": ["39", 0], "start_image": ["57", 0],
                # WHY: 960x544 = more pixels for small text. 1024x576 OOM on Beast.
                "width": 960, "height": 544,
                # WHY: 33 frames = ~2 sec at 16fps
                "length": 33, "batch_size": 1,
            },
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["48", 0], "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["55", 0], "seed": int(time.time()) % (2**32),
                "control_after_generate": "randomize",
                # WHY: 14 steps = sweet spot, euler+simple matches training
                "steps": 14, "cfg": 5.5,
                "sampler_name": "euler", "scheduler": "simple",
                # WHY: 0.20 denoise = maximum preservation of text/labels.
                # TESTED: 0.15/0.20/0.25/0.30/0.35 — 0.20 at 960x544 gives sharpest small text.
                "denoise": 0.20,
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["39", 0]},
        },
        # WHY: Real-ESRGAN 4x upscale sharpens text/labels that WAN softens.
        # Runs per-frame after VAEDecode, before saving. Adds ~30s to pipeline.
        "60": {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": "RealESRGAN_x4plus.pth"},
        },
        "61": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"upscale_model": ["60", 0], "image": ["8", 0]},
        },
        # WHY: Downscale back to 1280x720 (production resolution per WAN 2.2 guide).
        # 4x upscale of 832x480 = 3328x1920 — too large for WEBP delivery.
        "62": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["61", 0], "width": 1280, "height": 720,
                "upscale_method": "lanczos", "crop": "center",
            },
        },
        "28": {
            "class_type": "SaveAnimatedWEBP",
            "inputs": {
                "images": ["62", 0], "filename_prefix": "video_output",
                "fps": 16, "lossless": False, "quality": 90, "method": "default",
            },
        },
    }


def run_comfyui_pipeline(image_bytes: bytes, filename: str, prompt_text: str) -> dict:
    """Upload image to ComfyUI, queue Wan 2.2 workflow, wait for result."""
    # WHY: Single client reused for upload + queue + all poll iterations (avoids resource leak)
    with httpx.Client(timeout=600.0) as client:
        upload_name = f"input_{uuid.uuid4().hex[:8]}_{filename}"
        resp = client.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (upload_name, image_bytes, "image/png")},
            data={"overwrite": "true"},
        )
        resp.raise_for_status()
        image_name = resp.json().get("name", upload_name)

        workflow = build_wan_workflow(image_name, prompt_text)

        resp = client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        resp.raise_for_status()
        prompt_id = resp.json().get("prompt_id")
        if not prompt_id:
            raise RuntimeError("ComfyUI nie zwrocilo prompt_id")

        max_wait = 600
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(5)
            status = check_comfyui_status(prompt_id, client)
            if status.status == "completed" and status.video_base64:
                return status.model_dump()
            if status.status == "error":
                raise RuntimeError(status.error or "ComfyUI error")

        raise RuntimeError("Timeout — generowanie trwa za dlugo")


def check_comfyui_status(prompt_id: str, client: httpx.Client | None = None) -> VideoStatusResponse:
    """Check ComfyUI history for prompt completion."""
    # WHY: Accept optional client to reuse connection from polling loop
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=30.0)

    try:
        resp = client.get(f"{COMFYUI_URL}/history/{prompt_id}")
        resp.raise_for_status()
        history = resp.json()

        if prompt_id not in history:
            return VideoStatusResponse(status="processing", prompt_id=prompt_id)

        entry = history[prompt_id]
        status_info = entry.get("status", {})
        if status_info.get("status_str") == "error":
            msgs = status_info.get("messages", [])
            error_msg = str(msgs[-1]) if msgs else "Unknown error"
            return VideoStatusResponse(status="error", error=error_msg, prompt_id=prompt_id)

        outputs = entry.get("outputs", {})
        for _node_id, node_output in outputs.items():
            # WHY: SaveAnimatedWEBP puts results in "images" key
            images = node_output.get("images", []) + node_output.get("gifs", [])
            for img in images:
                fname = img.get("filename")
                subfolder = img.get("subfolder", "")
                if fname:
                    params = {"filename": fname}
                    if subfolder:
                        params["subfolder"] = subfolder
                    video_resp = client.get(f"{COMFYUI_URL}/view", params=params)
                    video_resp.raise_for_status()
                    b64 = base64.b64encode(video_resp.content).decode()
                    return VideoStatusResponse(status="completed", video_base64=b64, prompt_id=prompt_id)

        return VideoStatusResponse(status="processing", prompt_id=prompt_id)
    finally:
        if own_client:
            client.close()
