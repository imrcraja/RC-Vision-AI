"""Sample text from an RC Vision AI checkpoint created by train.py.

This is a tiny byte-level research model. Expect low-quality/random text unless
it has been trained sufficiently on a suitable corpus. Only load checkpoints
you created or trust.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import torch
from torch.nn import functional as F

from train import ByteTokenizer, RCVisionLM


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--new-bytes", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if args.new_bytes < 0:
        parser.error("--new-bytes must be non-negative")
    if args.temperature <= 0:
        parser.error("--temperature must be greater than zero")
    if args.top_k < 1 or args.top_k > 256:
        parser.error("--top-k must be between 1 and 256")
    if not args.checkpoint.is_file():
        parser.error(f"checkpoint not found: {args.checkpoint}")

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # weights_only avoids unrestricted pickle object loading in supported PyTorch versions.
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=True)
    if checkpoint.get("format") != "rc-vision-ai-byte-transformer-v1":
        parser.error("unsupported checkpoint format")
    cfg = checkpoint["model_config"]
    model = RCVisionLM(
        width=cfg["width"], layers=cfg["layers"], heads=cfg["heads"],
        context=cfg["context"], dropout=0.0
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    tokenizer = ByteTokenizer()
    prompt_tokens = tokenizer.encode(args.prompt)
    if not prompt_tokens:
        parser.error("prompt must not be empty")
    generated = torch.tensor([prompt_tokens], dtype=torch.long, device=device)
    with torch.no_grad():
        for _ in range(args.new_bytes):
            context = generated[:, -cfg["context"]:]
            logits = model(context)[:, -1, :] / args.temperature
            values, indices = torch.topk(logits, min(args.top_k, logits.shape[-1]), dim=-1)
            filtered = torch.full_like(logits, float("-inf"))
            filtered.scatter_(1, indices, values)
            next_token = torch.multinomial(F.softmax(filtered, dim=-1), num_samples=1)
            generated = torch.cat((generated, next_token), dim=1)
    print(tokenizer.decode(generated[0].tolist()))
    print(
        f"\n[research checkpoint step={checkpoint['step']} "
        f"train_loss={checkpoint['train_loss']:.4f} "
        f"validation_loss={checkpoint['validation_loss']:.4f}; "
        "not a general-purpose assistant]",
        file=__import__("sys").stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
