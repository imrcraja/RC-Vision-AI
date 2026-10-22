"""Estimate parameter count and storage for this repo's byte-level Transformer."""
from __future__ import annotations
import argparse

def count_parameters(width: int, layers: int, context: int) -> int:
    # Token embedding + positional embedding + tied output weights + final LayerNorm.
    # Per block: QKV (3w²), attention projection (w²), MLP (8w²),
    # two LayerNorms (4w), and MLP biases (5w).
    return 256 * width + context * width + 2 * width + layers * (12 * width * width + 9 * width)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--layers", type=int, default=16)
    parser.add_argument("--context", type=int, default=1024)
    args = parser.parse_args()
    if min(args.width, args.layers, args.context) <= 0:
        parser.error("width, layers and context must be positive")
    if args.width % 8:
        parser.error("width should be divisible by 8 for the standard target configurations")
    params = count_parameters(args.width, args.layers, args.context)
    print(f"Configuration: width={args.width}, layers={args.layers}, context={args.context}")
    print(f"Parameters: {params:,}")
    print(f"FP32 raw weights: {params * 4 / 1_000_000:.1f} MB ({params * 4 / 1_048_576:.1f} MiB)")
    print(f"FP16 raw weights: {params * 2 / 1_000_000:.1f} MB ({params * 2 / 1_048_576:.1f} MiB)")
    print(f"Adam training state lower-bound (weights + 2 FP32 moments): {params * 12 / 1_000_000:.1f} MB, before gradients/activations/overhead")
    print("This is a size estimate, not a training run or quality guarantee.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
