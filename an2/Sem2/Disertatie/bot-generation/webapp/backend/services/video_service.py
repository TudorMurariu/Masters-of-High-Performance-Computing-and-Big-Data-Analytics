"""
video_service.py
----------------
Short video generation using LTX-Video (requires CUDA).

Fallback chain:
  1. LTX-Video (CUDA only)   → real AI video
  2. PIL + imageio-ffmpeg    → styled "GPU required" placeholder card (5 s)
  3. imageio black frames    → plain black placeholder
  4. system ffmpeg           → plain black placeholder
  Returns False only if nothing at all could be written.
"""
import logging
import os
import random
import subprocess
import threading
from pathlib import Path

import torch

log = logging.getLogger("video_service")

_pipeline        = None
_pipeline_loaded = False
_pipeline_error  = None
_pipeline_lock   = threading.Lock()

LTX_VIDEO_PATH = os.environ.get("LTX_VIDEO_PATH", r"N:/huggingface/cache/LTX-Video")

# ── Persona prompt templates ──────────────────────────────────────────────────

VIDEO_PROMPTS = {
    "general": [
        "A person sitting at a café table, scrolling a phone, morning light, cinematic",
        "A quiet neighbourhood street, people walking, golden hour, realistic",
        "Someone cooking in a bright modern kitchen, natural light, slice-of-life",
    ],
    "political": [
        "A politician giving a speech at a podium in front of a crowd, news-style footage",
        "City hall building exterior, flag waving in the wind, documentary style",
        "People holding signs at a peaceful rally, daytime, handheld camera",
    ],
    "sports": [
        "A football match in a stadium, crowd cheering, wide-angle, broadcast quality",
        "A sprinter crossing the finish line, slow motion, athletic event",
        "Friends playing basketball on an outdoor court, sunny afternoon",
    ],
    "news": [
        "A news anchor behind a desk in a modern TV studio, broadcast footage",
        "Aerial drone shot of a busy city intersection at rush hour, documentary",
        "A reporter standing outside with a microphone, city background",
    ],
    "influencer": [
        "A stylish person walking down a colourful urban street, warm tones, vlog style",
        "Flat lay of cosmetics and coffee on a marble table, soft daylight",
        "Rooftop party with city skyline at sunset, bokeh lights, lifestyle footage",
    ],
    "conspiracy": [
        "Dark room with computer screens, hands typing, blue light, hacker aesthetic",
        "Newspaper headlines scattered on a table, close-up, documentary style",
        "Empty government building hallway, security cameras, eerie atmosphere",
    ],
}


# ── Placeholder helpers ───────────────────────────────────────────────────────

def _pil_placeholder(output_path: str, persona: str = "general") -> bool:
    """
    Create a styled 5-second placeholder card using PIL + imageio-ffmpeg.
    Much more informative than solid black frames.
    """
    try:
        import numpy as np
        import imageio
        from PIL import Image, ImageDraw, ImageFont

        W, H = 512, 288
        PERSONA_COLORS = {
            "general":    (30, 40, 60),
            "political":  (40, 25, 25),
            "sports":     (20, 40, 25),
            "news":       (25, 35, 50),
            "influencer": (45, 25, 45),
            "conspiracy": (20, 20, 20),
        }
        PERSONA_LABELS = {
            "general":    "General",
            "political":  "Political",
            "sports":     "Sports",
            "news":       "News",
            "influencer": "Influencer",
            "conspiracy": "Conspiracy",
        }

        bg = PERSONA_COLORS.get(persona, (25, 30, 45))
        img = Image.new("RGB", (W, H), color=bg)
        draw = ImageDraw.Draw(img)

        # Subtle gradient overlay
        for y in range(H):
            alpha = y / H * 0.4
            r = int(bg[0] + (255 - bg[0]) * alpha * 0.05)
            g = int(bg[1] + (255 - bg[1]) * alpha * 0.05)
            b = int(bg[2] + (255 - bg[2]) * alpha * 0.08)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Try to load a readable font
        font_large = font_small = None
        for font_path in ("C:/Windows/Fonts/segoeui.ttf",
                          "C:/Windows/Fonts/arial.ttf",
                          "C:/Windows/Fonts/calibri.ttf",
                          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            try:
                font_large = ImageFont.truetype(font_path, 22)
                font_small = ImageFont.truetype(font_path, 14)
                break
            except Exception:
                continue
        if font_large is None:
            font_large = font_small = ImageFont.load_default()

        # Draw "video" icon rectangle
        icon_x, icon_y = W // 2 - 28, H // 2 - 40
        draw.rectangle([icon_x, icon_y, icon_x + 56, icon_y + 40],
                       outline=(120, 120, 160), width=2)
        draw.polygon([
            (icon_x + 18, icon_y + 8),
            (icon_x + 18, icon_y + 32),
            (icon_x + 44, icon_y + 20),
        ], fill=(120, 120, 160))

        # Labels
        label  = PERSONA_LABELS.get(persona, persona.capitalize()) + " Bot Video"
        sublbl = "GPU required for AI video generation"

        bbox = draw.textbbox((0, 0), label, font=font_large)
        lw   = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, H // 2 + 10), label,
                  fill=(180, 180, 210), font=font_large)

        bbox2 = draw.textbbox((0, 0), sublbl, font=font_small)
        sw    = bbox2[2] - bbox2[0]
        draw.text(((W - sw) // 2, H // 2 + 38), sublbl,
                  fill=(100, 100, 130), font=font_small)

        arr = np.array(img)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(
            output_path,
            fps=1,
            codec="libx264",
            quality=5,
            pixelformat="yuv420p",
            macro_block_size=8,
        )
        for _ in range(5):   # 5 frames = 5 s @ 1 fps
            writer.append_data(arr)
        writer.close()
        log.info(f"PIL placeholder video saved → {output_path}")
        return True
    except Exception as exc:
        log.warning(f"PIL placeholder failed: {exc}")
        return False


def _imageio_black(output_path: str) -> bool:
    """Plain black frames — last resort before ffmpeg subprocess."""
    try:
        import numpy as np
        import imageio
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        frame  = np.zeros((256, 256, 3), dtype=np.uint8)
        writer = imageio.get_writer(
            output_path, fps=4, codec="libx264",
            quality=5, pixelformat="yuv420p", macro_block_size=8,
        )
        for _ in range(8):   # 2 s
            writer.append_data(frame)
        writer.close()
        log.info(f"Black placeholder video saved → {output_path}")
        return True
    except Exception as exc:
        log.warning(f"imageio black placeholder failed: {exc}")
        return False


def _ffmpeg_placeholder(output_path: str) -> bool:
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", "color=c=black:s=256x256:r=4",
             "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path],
            capture_output=True, timeout=30,
        )
        if r.returncode == 0:
            log.info(f"ffmpeg placeholder → {output_path}")
            return True
        log.warning(f"ffmpeg exited {r.returncode}: {r.stderr[:200]}")
        return False
    except Exception as exc:
        log.warning(f"ffmpeg not available: {exc}")
        return False


# ── LTX-Video pipeline ────────────────────────────────────────────────────────

def _get_pipeline():
    global _pipeline, _pipeline_loaded, _pipeline_error
    with _pipeline_lock:
        if _pipeline_loaded:
            return _pipeline

        if not torch.cuda.is_available():
            _pipeline_error = "CUDA not available (CPU-only PyTorch detected)"
            log.warning(
                "LTX-Video requires CUDA — skipping AI video generation. "
                "Placeholder videos will be used instead. "
                "To enable: pip install torch --index-url "
                "https://download.pytorch.org/whl/cu121"
            )
            _pipeline = None
            _pipeline_loaded = True
            return None

        try:
            log.info(f"Loading LTX-Video from {LTX_VIDEO_PATH} …")
            from diffusers import LTXPipeline
            _pipeline = LTXPipeline.from_pretrained(
                LTX_VIDEO_PATH,
                torch_dtype=torch.bfloat16,
                local_files_only=True,
            )
            _pipeline.enable_model_cpu_offload()
            log.info("LTX-Video pipeline ready.")
        except Exception as exc:
            _pipeline_error = str(exc)
            log.error(f"Could not load LTX-Video: {exc}")
            _pipeline = None

        _pipeline_loaded = True
    return _pipeline


# ── Public API ────────────────────────────────────────────────────────────────

def generate_video(persona: str, topic: str, output_path: str) -> bool:
    """
    Generate a video for this post.  Falls back gracefully through the
    placeholder chain.  Returns True if a playable file was written.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pipe = _get_pipeline()

    # ── 1. LTX-Video (CUDA only) ──────────────────────────────────────────────
    if pipe is not None:
        base   = random.choice(VIDEO_PROMPTS.get(persona, VIDEO_PROMPTS["general"]))
        snippet = (topic or "")[:80]
        prompt  = f"{base}, related to: {snippet}" if snippet else base
        neg     = ("worst quality, inconsistent motion, blurry, jittery, distorted, "
                   "nsfw, cartoon, anime")
        seed      = random.randint(0, 2**32 - 1)
        generator = torch.Generator().manual_seed(seed)

        try:
            log.info(f"LTX-Video generating (persona={persona}) …")
            result = pipe(
                prompt=prompt, negative_prompt=neg,
                width=512, height=512,
                num_frames=49, num_inference_steps=30,
                generator=generator,
            )
            import imageio, numpy as np
            writer = imageio.get_writer(
                output_path, fps=16, codec="libx264",
                quality=6, pixelformat="yuv420p",
            )
            for frame in result.frames[0]:
                writer.append_data(np.array(frame))
            writer.close()
            log.info(f"LTX-Video saved → {output_path}")
            return True
        except Exception as exc:
            log.error(f"LTX-Video generation error: {exc}")
            # fall through to placeholders

    # ── 2–4. Placeholder chain ────────────────────────────────────────────────
    if _pil_placeholder(output_path, persona):
        return True
    if _imageio_black(output_path):
        return True
    if _ffmpeg_placeholder(output_path):
        return True

    log.error(f"All video fallbacks exhausted — no file written for {output_path}")
    return False
