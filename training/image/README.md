# Original image model research

This directory contains an original, randomly initialized conditional denoiser architecture and a small research training/sampling pipeline. It includes no pretrained weights, borrowed inference engine, or pretrained text encoder.

## Conditional diffusion pipeline

- `model.py`: original tiny conditional denoiser architecture.
- `train_diffusion.py`: trains a byte-level text encoder and denoiser jointly from random initialization on permitted image/caption pairs.
- `generate_image.py`: samples a low-resolution image from a trained checkpoint and a text prompt.
- `train_autoencoder.py`: fallback reconstruction baseline when images exist but a caption manifest does not.
- `test_research.py`: checks tensor shapes, finite outputs, image loading, and path-traversal rejection.

For conditional training, put images you own or have permission to use under `training/images/`, and create `training/images/captions.jsonl` with one JSON object per line, for example:

```json
{"image":"example1.png","caption":"a red square on a plain background"}
{"image":"example2.png","caption":"a blue circle on a plain background"}
```

The manifest must contain at least two valid image/caption pairs. Use a larger, diverse, permission-cleared dataset for any meaningful quality evaluation. Do not commit private photos or personal images without consent; public repository images can be viewed by others.

## Honest status

The training and sampling pipeline is implemented, but no suitable image-caption dataset is currently included and no useful image generator checkpoint is bundled. With only a few examples, outputs will likely be poor or meaningless. A successful shape/smoke test proves code paths work, not image quality or semantic understanding.
