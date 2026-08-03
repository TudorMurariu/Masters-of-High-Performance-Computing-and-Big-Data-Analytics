"""
generate_profile_pics.py
------------------------
Generate realistic fake social media profile pictures using FLUX.1-schnell.

Model is downloaded automatically on first run into N:\\huggingface\\cache
(HF_HOME is already set to N:\\huggingface, so no extra config needed).

Download size: ~27 GB  |  VRAM usage: ~8 GB with CPU offloading

Usage
-----
    # Generate the full default set (50 images, 10 prompts x 5 seeds each)
    python generate_profile_pics.py

    # Quick test: one image per prompt
    python generate_profile_pics.py --per_prompt 1

    # Custom number of images
    python generate_profile_pics.py --per_prompt 3 --output_dir outputs/profile_pics

    # Download / cache the model without generating (first-run pre-warm)
    python generate_profile_pics.py --download_only
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import torch
from diffusers import FluxPipeline

# ── Config ────────────────────────────────────────────────────────────────────
SEED            = 42
MODEL_ID        = "black-forest-labs/FLUX.1-schnell"
DEFAULT_OUT_DIR = "outputs/profile_pics"
IMAGE_SIZE      = 512           # square, good for profile pictures
NUM_STEPS       = 4             # schnell is designed for 4 steps
GUIDANCE_SCALE  = 0.0           # schnell uses 0.0 (distilled, CFG-free)

# Negative prompts are ignored by FLUX but kept for future compatibility
NEGATIVE = (
    "cartoon, anime, illustration, painting, CGI, 3d render, "
    "watermark, text, logo, distorted, deformed, ugly"
)

# ── Prompt library ────────────────────────────────────────────────────────────
# Diverse demographic coverage for a realistic bot population.
# Each prompt generates NUM_PER_PROMPT images with different seeds.
PROMPTS = [
    # --- Women ---
    "portrait photo of a young woman in her mid-20s, natural daylight, "
    "casual outfit, genuine smile, shallow depth of field, photorealistic, "
    "high quality, social media profile picture",

    "candid outdoor portrait of a woman aged 28, park background, "
    "golden hour light, natural makeup, DSLR photograph, photorealistic",

    "portrait photo of a Black woman in her late 20s, natural hair, "
    "warm smile, outdoor background, soft sunlight, photorealistic",

    "portrait photo of an East Asian woman aged 25, coffee shop background, "
    "casual style, happy expression, photorealistic, high quality",

    "portrait photo of a Hispanic woman aged 30, beach background, "
    "summer clothes, relaxed expression, photorealistic",

    # --- Men ---
    "portrait photo of a young man in his mid-20s, casual t-shirt, "
    "natural light indoors, friendly expression, photorealistic, "
    "high quality, social media profile picture",

    "portrait photo of a man aged 32, light beard, urban street background, "
    "casual jacket, confident expression, photorealistic",

    "portrait photo of a Black man in his late 20s, city background, "
    "casual outfit, genuine smile, photorealistic, high quality",

    "portrait photo of a South Asian man aged 35, glasses, "
    "office background, smart casual, photorealistic",

    "portrait photo of an East Asian man aged 28, outdoor background, "
    "hoodie, relaxed smile, natural lighting, photorealistic",
]


# ── Pipeline loading ──────────────────────────────────────────────────────────
def load_pipeline() -> FluxPipeline:
    """Load FLUX.1-schnell with bfloat16 + CPU offloading for 8 GB VRAM."""
    print(f"[*] Loading FLUX.1-schnell  (model id: {MODEL_ID})")
    print(f"    First run will download ~27 GB to your HF cache on N:\\")
    print(f"    Subsequent runs load from cache instantly.\n")

    pipe = FluxPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
    )
    # Offload each sub-model to CPU when not in use -> fits in 8 GB VRAM
    pipe.enable_model_cpu_offload()

    print("[OK] Pipeline ready.\n")
    return pipe


# ── Generation ────────────────────────────────────────────────────────────────
def generate_image(
    pipe: FluxPipeline,
    prompt: str,
    output_path: str,
    seed: int = SEED,
    size: int = IMAGE_SIZE,
    steps: int = NUM_STEPS,
) -> dict:
    """Generate one image and save it as PNG. Returns a metadata dict."""
    generator = torch.Generator(device="cpu").manual_seed(seed)

    t0 = time.time()
    result = pipe(
        prompt=prompt,
        width=size,
        height=size,
        num_inference_steps=steps,
        guidance_scale=GUIDANCE_SCALE,
        generator=generator,
        output_type="pil",
    )
    elapsed = round(time.time() - t0, 1)

    image = result.images[0]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "output": output_path,
        "seed": seed,
        "width": size,
        "height": size,
        "steps": steps,
        "generation_time_s": elapsed,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Generate fake profile pictures with FLUX.1-schnell")
    p.add_argument("--per_prompt",   type=int, default=5,
                   help="Images to generate per prompt (default: 5)")
    p.add_argument("--output_dir",   type=str, default=DEFAULT_OUT_DIR)
    p.add_argument("--size",         type=int, default=IMAGE_SIZE,
                   help="Square image size in pixels (default: 512)")
    p.add_argument("--steps",        type=int, default=NUM_STEPS,
                   help="Inference steps (default: 4, schnell optimum)")
    p.add_argument("--seed",         type=int, default=SEED)
    p.add_argument("--download_only", action="store_true",
                   help="Download and cache the model then exit without generating")
    return p.parse_args()


def main():
    args = parse_args()

    pipe = load_pipeline()

    if args.download_only:
        print("[OK] Model downloaded and cached. Run without --download_only to generate images.")
        return

    total = len(PROMPTS) * args.per_prompt
    print(f"[*] Generating {total} images  "
          f"({len(PROMPTS)} prompts × {args.per_prompt} seeds each)")
    print(f"    Output dir: {args.output_dir}\n")

    results = []
    img_idx = 0
    for p_idx, prompt in enumerate(PROMPTS):
        for s_idx in range(args.per_prompt):
            seed = args.seed + p_idx * 1000 + s_idx
            filename = f"profile_{img_idx:04d}_p{p_idx:02d}_s{s_idx:02d}.png"
            out_path = os.path.join(args.output_dir, filename)

            print(f"[{img_idx+1:3d}/{total}] prompt {p_idx} | seed {seed}")
            print(f"         {prompt[:80]}...")

            meta = generate_image(
                pipe=pipe,
                prompt=prompt,
                output_path=out_path,
                seed=seed,
                size=args.size,
                steps=args.steps,
            )
            print(f"         Saved: {filename}  ({meta['generation_time_s']}s)\n")
            results.append(meta)
            img_idx += 1

    # Save metadata
    os.makedirs(args.output_dir, exist_ok=True)
    meta_path = os.path.join(args.output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    total_time = sum(r["generation_time_s"] for r in results)
    print(f"[OK] Done. {img_idx} images in {total_time:.0f}s "
          f"({total_time/img_idx:.1f}s/image avg)")
    print(f"[OK] Metadata -> {meta_path}")


if __name__ == "__main__":
    main()
