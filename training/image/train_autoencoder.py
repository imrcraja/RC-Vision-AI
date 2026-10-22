"""Train a tiny convolutional autoencoder from scratch on permitted local images.

This is an image-reconstruction research baseline, not a text-conditioned image generator.
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

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class ImageFolderDataset(Dataset):
    def __init__(self, root: Path, size: int) -> None:
        self.root, self.size = root, size
        self.files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
        if len(self.files) < 2:
            raise ValueError(f"Need at least 2 supported images in {root}; found {len(self.files)}")
    def __len__(self) -> int:
        return len(self.files)
    def __getitem__(self, index: int) -> torch.Tensor:
        with Image.open(self.files[index]) as im:
            im = im.convert("RGB").resize((self.size, self.size), Image.Resampling.BILINEAR)
            values = torch.tensor(list(im.tobytes()), dtype=torch.float32).reshape(self.size, self.size, 3)
        return values.permute(2, 0, 1).div_(127.5).sub_(1.0)


class TinyAutoencoder(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(16, 32, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(32, 64, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(64, 64, 4, 2, 1), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(64, 64, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(32, 16, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(16, 3, 4, 2, 1), nn.Tanh(),
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True, help="Directory of permitted images")
    parser.add_argument("--output", type=Path, default=Path("artifacts/image"))
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    if args.image_size < 32 or args.image_size > 256 or args.image_size % 16:
        parser.error("--image-size must be a multiple of 16 from 32 to 256")
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive")
    random.seed(args.seed); torch.manual_seed(args.seed)
    dataset = ImageFolderDataset(args.dataset, args.image_size)
    val_count = max(1, round(len(dataset) * 0.2))
    train_count = len(dataset) - val_count
    if train_count < 1:
        raise ValueError("Need at least 2 images for train/validation split")
    train_set, val_set = random_split(dataset, [train_count, val_count], generator=torch.Generator().manual_seed(args.seed))
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TinyAutoencoder().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    started = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train(); total = 0.0; batches = 0
        for batch in train_loader:
            batch = batch.to(device)
            loss = F.mse_loss(model(batch), batch)
            optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
            total += float(loss.detach().cpu()); batches += 1
        model.eval(); val_total = 0.0; val_batches = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                val_total += float(F.mse_loss(model(batch), batch).cpu()); val_batches += 1
        train_loss = total / max(1, batches)
        val_loss = val_total / max(1, val_batches)
        print(f"epoch={epoch}/{args.epochs} train_mse={train_loss:.6f} validation_mse={val_loss:.6f}")
    digest = hashlib.sha256()
    for path in dataset.files:
        digest.update(path.name.encode("utf-8")); digest.update(path.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "format": "rc-vision-ai-tiny-autoencoder-v1",
        "model_config": {"image_size": args.image_size, "channels": 3, "architecture": "tiny-convolutional-autoencoder"},
        "model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
        "seed": args.seed, "dataset_images": len(dataset.files), "train_images": train_count,
        "validation_images": val_count, "dataset_sha256": digest.hexdigest(),
        "train_mse": train_loss, "validation_mse": val_loss,
        "elapsed_seconds": round(time.time() - started, 2),
        "limitation": "Reconstruction research baseline only; not a prompt-conditioned image generator.",
    }
    target = args.output / "image-autoencoder.pt"
    torch.save(checkpoint, target)
    (args.output / "metrics.json").write_text(json.dumps({k: v for k, v in checkpoint.items() if k not in {"model_state", "optimizer_state"}}, indent=2), encoding="utf-8")
    print(f"Saved {target}; this model reconstructs images and does not generate prompt-aligned images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
