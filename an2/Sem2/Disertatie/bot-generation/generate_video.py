"""
generate_video.py
-----------------
Generate short videos using LTX-Video 2B for bot simulation research.

Usage:
    python generate_video.py --prompt "A person reacting to news on their phone"
    python generate_video.py --prompt "..." --num_videos 5 --output_dir outputs/videos
    python generate_video.py --prompts_file prompts.txt
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import imageio
import torch
from diffusers import LTXPipeline

# ── Constants ────────────────────────────────────────────────────────────────
SEED = 42
MODEL_PATH = r"N:/huggingface/cache/LTX-Video"
DEFAULT_OUTPUT_DIR = "outputs/videos"
DEFAULT_NEGATIVE = (
    "worst quality, inconsistent motion, blurry, jittery, distorted, watermark"
)


# ── Model loading ─────────────────────────────────────────────────────────────
def load_pipeline(model_path: str) -> LTXPipeline:
    print(f"[*] Loading LTX-Video from {model_path} ...")
    pipe = LTXPipeline.from_pretrained(model_path, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()  # keeps VRAM under 8 GB
    print("[*] Pipeline ready.")
    return pipe


# ── Generation ────────────────────────────────────────────────────────────────
def generate_video(
    pipe: LTXPipeline,
    prompt: str,
    output_path: str,
    negative_prompt: str = DEFAULT_NEGATIVE,
    width: int = 512,
    height: int = 288,
    num_frames: int = 25,
    num_inference_steps: int = 20,
    fps: int = 8,
    seed: int = SEED,
) -> dict:
    """Generate a single video and save it. Returns metadata dict."""

    generator = torch.manual_seed(seed)

    print(f"[>] Generating: {prompt[:80]}...")
    t0 = time.time()

    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_frames=num_frames,
        num_inference_steps=num_inference_steps,
        generator=generator,
    )

    elapsed = round(time.time() - t0, 1)
    frames = result.frames[0]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    imageio.mimwrite(output_path, frames, fps=fps)
    print(f"[✓] Saved to {output_path}  ({elapsed}s)")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "output": output_path,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "fps": fps,
        "seed": seed,
        "generation_time_s": elapsed,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Generate bot-style videos with LTX-Video")

    # Input
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", type=str, help="Single text prompt")
    group.add_argument("--prompts_file", type=str, help="Path to .txt file with one prompt per line")

    # Output
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--num_videos", type=int, default=1, help="How many videos to generate per prompt")

    # Video settings
    parser.add_argument("--width", type=int, default=512, help="Must be divisible by 32")
    parser.add_argument("--height", type=int, default=288, help="Must be divisible by 32")
    parser.add_argument("--num_frames", type=int, default=25, help="Use 8k+1 values: 9,17,25,33,41...")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps (more = better quality)")
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--seed", type=int, default=SEED)

    # Model
    parser.add_argument("--model_path", type=str, default=MODEL_PATH)

    return parser.parse_args()


def main():
    args = parse_args()

    # Collect prompts
    if args.prompt:
        prompts = [args.prompt]
    else:
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    print(f"[*] {len(prompts)} prompt(s) × {args.num_videos} video(s) = {len(prompts) * args.num_videos} total")

    # Load model once
    pipe = load_pipeline(args.model_path)

    # Generate
    results = []
    for prompt_idx, prompt in enumerate(prompts):
        for vid_idx in range(args.num_videos):
            filename = f"video_{prompt_idx:03d}_{vid_idx:02d}.mp4"
            output_path = os.path.join(args.output_dir, filename)
            seed = args.seed + prompt_idx * 100 + vid_idx  # unique seed per video

            meta = generate_video(
                pipe=pipe,
                prompt=prompt,
                output_path=output_path,
                width=args.width,
                height=args.height,
                num_frames=args.num_frames,
                num_inference_steps=args.steps,
                fps=args.fps,
                seed=seed,
            )
            results.append(meta)

    # Save metadata
    os.makedirs(args.output_dir, exist_ok=True)
    metrics_path = os.path.join(args.output_dir, "metadata.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[✓] Done. Metadata saved to {metrics_path}")


if __name__ == "__main__":
    main()
