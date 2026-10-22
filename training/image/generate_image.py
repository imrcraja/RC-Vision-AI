"""Sample a low-resolution image from an RC Vision AI conditional diffusion checkpoint."""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from PIL import Image

from model import RCConditionalDenoiser
from train_diffusion import ByteTextEncoder, MAX_TEXT_BYTES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/image/sample.png"))
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if not args.checkpoint.is_file():
        parser.error(f"checkpoint not found: {args.checkpoint}")
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=True)
    if checkpoint.get("format") != "rc-vision-ai-conditional-diffusion-v1":
        parser.error("unsupported checkpoint format")
    config = checkpoint["model_config"]
    text_encoder = ByteTextEncoder(width=config["condition_width"]).to(device)
    denoiser = RCConditionalDenoiser(width=config["denoiser_width"], condition_width=config["condition_width"]).to(device)
    text_encoder.load_state_dict(checkpoint["text_encoder_state"])
    denoiser.load_state_dict(checkpoint["denoiser_state"])
    text_encoder.eval(); denoiser.eval()
    encoded = list(args.prompt.encode("utf-8"))[:MAX_TEXT_BYTES] or [32]
    tokens = torch.zeros(1, MAX_TEXT_BYTES, dtype=torch.long, device=device)
    tokens[0, :len(encoded)] = torch.tensor(encoded, dtype=torch.long, device=device)
    lengths = torch.tensor([len(encoded)], dtype=torch.long, device=device)
    with torch.no_grad():
        condition = text_encoder(tokens, lengths)
        size, steps = config["image_size"], config["diffusion_steps"]
        betas = torch.linspace(1e-4, 0.02, steps, device=device)
        alphas = 1.0 - betas
        alpha_bars = torch.cumprod(alphas, dim=0)
        sample = torch.randn(1, 3, size, size, device=device)
        for index in reversed(range(steps)):
            timestep = torch.tensor([index], device=device)
            predicted_noise = denoiser(sample, timestep, condition)
            sample = (sample - betas[index] / torch.sqrt(1.0 - alpha_bars[index]) * predicted_noise) / torch.sqrt(alphas[index])
            if index > 0:
                sample = sample + torch.sqrt(betas[index]) * torch.randn_like(sample)
        pixels = sample[0].clamp(-1, 1).add(1).mul(127.5).byte().permute(1, 2, 0).cpu().numpy()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, mode="RGB").save(args.output)
    print(f"Saved {args.output}. Inspect visually; a small research checkpoint may produce poor or meaningless results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
