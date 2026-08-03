"""
flux_service.py
---------------
Profile picture generation using Lykon/dreamshaper-8 (SD 1.5, ~2 GB).

GPU  → float16, 25 steps, ~5-10 s/image
CPU  → float32,  5 steps, ~2-3 min/image  (much slower but functional)

Model is loaded from the local HuggingFace cache — no internet needed if
the model was downloaded previously.
"""
import logging
import random
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("flux_service")

_pipeline        = None
_pipeline_loaded = False
_pipeline_error  = None    # stores the exception string if load failed

NEGATIVE = (
    "blurry, deformed, ugly, bad anatomy, cartoon, anime, illustration, "
    "painting, watermark, text, logo, nsfw"
)

PORTRAIT_PROMPTS = {
    "general":    "RAW photo, portrait of a person in their late 20s, casual outfit, "
                  "natural light, friendly smile, sharp focus, photorealistic, 8k",
    "political":  "RAW photo, portrait of a professional in their 30s, business casual, "
                  "confident expression, sharp focus, photorealistic, 8k",
    "sports":     "RAW photo, portrait of a young person in their 20s, casual sportswear, "
                  "energetic expression, sharp focus, photorealistic, 8k",
    "news":       "RAW photo, portrait of a professional in their 30s, smart casual, "
                  "focused look, sharp focus, photorealistic, 8k",
    "influencer": "RAW photo, portrait of a stylish young person in their mid-20s, "
                  "fashionable outfit, warm smile, sharp focus, photorealistic, 8k",
    "conspiracy": "RAW photo, portrait of an ordinary person in their 30s, "
                  "casual clothes, thoughtful expression, sharp focus, photorealistic, 8k",
}

AVATAR_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#9b59b6",
    "#f39c12", "#1abc9c", "#e67e22", "#2c3e50",
]


# ── Public helpers ────────────────────────────────────────────────────────────

def get_pipeline_status() -> dict:
    if not _pipeline_loaded:
        return {"state": "not_loaded"}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if _pipeline is not None:
        return {"state": "ready", "device": device}
    return {"state": "failed", "error": _pipeline_error or "unknown error"}


# ── Pipeline loader ───────────────────────────────────────────────────────────

def _get_pipeline():
    global _pipeline, _pipeline_loaded, _pipeline_error

    if _pipeline_loaded:
        return _pipeline

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        log.warning(
            "No CUDA detected — dreamshaper-8 will run on CPU. "
            "Expect ~2-3 min/image (5 steps). "
            "For GPU speed install: pip install torch --index-url "
            "https://download.pytorch.org/whl/cu121"
        )
    else:
        log.info(f"CUDA available — dreamshaper-8 will run on {torch.cuda.get_device_name(0)}")

    try:
        from diffusers import StableDiffusionPipeline
        log.info("Loading Lykon/dreamshaper-8 from local HF cache …")

        dtype = torch.float16 if device == "cuda" else torch.float32
        _pipeline = StableDiffusionPipeline.from_pretrained(
            "Lykon/dreamshaper-8",
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True,   # model already in N:/huggingface/cache
        )
        _pipeline = _pipeline.to(device)
        if device == "cuda":
            _pipeline.enable_attention_slicing()   # save ~500 MB VRAM
        log.info(f"Dreamshaper-8 ready on {device} ({dtype})")
    except Exception as exc:
        _pipeline_error = str(exc)
        log.error(f"Could not load dreamshaper-8: {exc}")
        log.error("Falling back to initials placeholder for profile pictures.")
        _pipeline = None

    _pipeline_loaded = True
    return _pipeline


# ── Placeholder (coloured circle with initials) ───────────────────────────────

def _make_placeholder(display_name: str, output_path: str):
    size  = 512
    color = random.choice(AVATAR_COLORS)
    img   = Image.new("RGB", (size, size), color=color)
    draw  = ImageDraw.Draw(img)

    initials  = "".join(w[0].upper() for w in display_name.split()[:2]) or "?"
    font_size = 180
    font      = None
    for path in ("arial.ttf", "Arial.ttf",
                 "C:/Windows/Fonts/arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x    = (size - w) / 2 - bbox[0]
    y    = (size - h) / 2 - bbox[1]
    draw.text((x, y), initials, fill="white", font=font)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    log.info(f"Initials placeholder saved → {output_path}")


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_profile_pic(display_name: str, persona: str, output_path: str) -> bool:
    """
    Generate a photorealistic profile picture with Dreamshaper-8.
    Returns True if the AI model was used, False if initials placeholder was used.
    """
    pipe = _get_pipeline()

    if pipe is None:
        _make_placeholder(display_name, output_path)
        return False

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Fewer steps on CPU to keep time under ~3 minutes
    steps  = 25 if device == "cuda" else 5

    prompt    = PORTRAIT_PROMPTS.get(persona, PORTRAIT_PROMPTS["general"]) + " And your username is " + display_name
    seed      = random.randint(0, 2**32 - 1)
    generator = torch.Generator(device=device).manual_seed(seed)

    log.info(f"Generating profile pic for '{display_name}' on {device} "
             f"({steps} steps, persona={persona}) …")
    try:
        result = pipe(
            prompt              = prompt,
            negative_prompt     = NEGATIVE,
            width               = 512,
            height              = 512,
            num_inference_steps = steps,
            guidance_scale      = 7.0,
            generator           = generator,
        )
        image = result.images[0]
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        log.info(f"Profile pic saved → {output_path}")
        return True
    except Exception as exc:
        log.error(f"Dreamshaper generation failed: {exc}")
        _make_placeholder(display_name, output_path)
        return False
