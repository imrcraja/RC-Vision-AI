"""Train an original tiny text-conditioned diffusion model from scratch.

Requires a permission-cleared JSONL image/caption dataset. No pretrained text encoder
or image model is loaded. Small datasets will produce very poor samples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset, random_split

from model import RCConditionalDenoiser

MAX_TEXT_BYTES = 128


class ByteTextEncoder(nn.Module):
    """Small original byte embedding encoder; initialized randomly and trained jointly."""
    def __init__(self, width: int = 128) -> None:
        super().__init__()
        self.embedding = nn.Embedding(256, width)
        self.position = nn.Embedding(MAX_TEXT_BYTES, width)
        self.norm = nn.LayerNorm(width)
        self.projection = nn.Sequential(nn.Linear(width, width), nn.Tanh(), nn.Linear(width, width))

    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(tokens.shape[1], device=tokens.device)
        x = self.embedding(tokens) + self.position(positions)[None, :, :]
        mask = torch.arange(tokens.shape[1], device=tokens.device)[None, :] < lengths[:, None]
        pooled = (x * mask[:, :, None]).sum(dim=1) / lengths.clamp(min=1)[:, None]
        return self.projection(self.norm(pooled))


class CaptionedImages(Dataset):
    def __init__(self, root: Path, manifest: Path, size: int) -> None:
        self.root, self.size = root.resolve(), size
        if not manifest.is_file():
            raise FileNotFoundError(f"Caption manifest not found: {manifest}")
        self.rows = []
        for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            image_name, caption = row.get("image"), row.get("caption")
            if not isinstance(image_name, str) or not isinstance(caption, str) or not caption.strip():
                raise ValueError(f"Line {line_number} needs string fields 'image' and non-empty 'caption'")
            image_path = (self.root / image_name).resolve()
            if not image_path.is_relative_to(self.root):
                raise ValueError(f"Image path escapes dataset root at line {line_number}")
            if not image_path.is_file():
                raise FileNotFoundError(f"Image from line {line_number} not found: {image_name}")
            self.rows.append((image_path, caption.strip()))
        if len(self.rows) < 2:
            raise ValueError("Need at least 2 image/caption pairs for training and validation.")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        path, caption = self.rows[index]
        with Image.open(path) as image:
            image = image.convert("RGB").resize((self.size, self.size), Image.Resampling.BILINEAR)
            pixels = torch.tensor(list(image.tobytes()), dtype=torch.float32).reshape(self.size, self.size, 3)
        pixels = pixels.permute(2, 0, 1).div_(127.5).sub_(1.0)
        encoded = list(caption.encode("utf-8"))[:MAX_TEXT_BYTES]
        encoded = encoded or [32]
        tokens = torch.zeros(MAX_TEXT_BYTES, dtype=torch.long)
        tokens[:len(encoded)] = torch.tensor(encoded, dtype=torch.long)
        return pixels, tokens, len(encoded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True, help="Folder containing images and captions.jsonl")
    parser.add_argument("--manifest", type=Path, default=None, help="Defaults to DATASET/captions.jsonl")
    parser.add_argument("--output", type=Path, default=Path("artifacts/image"))
    parser.add_argument("--image-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--diffusion-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    if args.image_size < 16 or args.image_size > 128 or args.image_size % 8:
        parser.error("--image-size must be a multiple of 8 from 16 to 128")
    if args.epochs < 1 or args.batch_size < 1 or args.diffusion_steps < 2:
        parser.error("epochs/batch-size must be positive and diffusion-steps at least 2")
    random.seed(args.seed); torch.manual_seed(args.seed)
    manifest = args.manifest or (args.dataset / "captions.jsonl")
    dataset = CaptionedImages(args.dataset, manifest, args.image_size)
    val_count = max(1, round(len(dataset) * 0.2))
    train_count = len(dataset) - val_count
    train_set, val_set = random_split(dataset, [train_count, val_count], generator=torch.Generator().manual_seed(args.seed))
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    text_encoder = ByteTextEncoder().to(device)
    denoiser = RCConditionalDenoiser(width=32, condition_width=128).to(device)
    optimizer = torch.optim.AdamW(list(text_encoder.parameters()) + list(denoiser.parameters()), lr=2e-4)
    betas = torch.linspace(1e-4, 0.02, args.diffusion_steps, device=device)
    alphas = 1.0 - betas
    alpha_bars = torch.cumprod(alphas, dim=0)
    started = time.time()

    def run_epoch(loader, training):
        text_encoder.train(training); denoiser.train(training)
        total = 0.0; count = 0
        for images, tokens, lengths in loader:
            images, tokens, lengths = images.to(device), tokens.to(device), lengths.to(device)
            timesteps = torch.randint(0, args.diffusion_steps, (images.shape[0],), device=device)
            noise = torch.randn_like(images)
            alpha_bar = alpha_bars[timesteps].view(-1, 1, 1, 1)
            noisy = alpha_bar.sqrt() * images + (1.0 - alpha_bar).sqrt() * noise
            condition = text_encoder(tokens, lengths)
            predicted = denoiser(noisy, timesteps, condition)
            loss = F.mse_loss(predicted, noise)
            if training:
                optimizer.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(list(text_encoder.parameters()) + list(denoiser.parameters()), 1.0)
                optimizer.step()
            total += float(loss.detach().cpu()); count += 1
        return total / max(1, count)

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(train_loader, True)
        with torch.no_grad():
            validation_loss = run_epoch(val_loader, False)
        print(f"epoch={epoch}/{args.epochs} train_noise_mse={train_loss:.6f} validation_noise_mse={validation_loss:.6f}")

    digest = hashlib.sha256(manifest.read_bytes())
    for image_path, _ in dataset.rows:
        digest.update(image_path.name.encode("utf-8")); digest.update(image_path.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "format": "rc-vision-ai-conditional-diffusion-v1",
        "model_config": {"image_size": args.image_size, "condition_width": 128, "denoiser_width": 32, "diffusion_steps": args.diffusion_steps, "max_text_bytes": MAX_TEXT_BYTES},
        "text_encoder_state": text_encoder.state_dict(), "denoiser_state": denoiser.state_dict(),
        "optimizer_state": optimizer.state_dict(), "seed": args.seed, "dataset_pairs": len(dataset),
        "dataset_sha256": digest.hexdigest(), "train_noise_mse": train_loss,
        "validation_noise_mse": validation_loss, "elapsed_seconds": round(time.time() - started, 2),
        "limitation": "Research prototype; quality depends on a sufficiently large, licensed image-caption dataset.",
    }
    torch.save(checkpoint, args.output / "conditional-diffusion.pt")
    (args.output / "diffusion-metrics.json").write_text(json.dumps({k: v for k, v in checkpoint.items() if not k.endswith("_state")}, indent=2), encoding="utf-8")
    print("Saved original conditional diffusion checkpoint. Evaluate sample quality before claiming useful image generation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
