# Image research dataset

Keep only images you own or have explicit permission to use under this directory. Supported formats: PNG, JPG/JPEG, WebP, BMP. Avoid private images in this public repository.

## Preferred: prompt-conditioned image research

For original conditional diffusion training, add at least two image/caption pairs to `captions.jsonl`:

```json
{"image":"example1.png","caption":"a red square on a plain background"}
{"image":"example2.png","caption":"a blue circle on a plain background"}
```

Each image path must stay inside this directory. The daily workflow uses `training/image/train_diffusion.py` when this manifest has at least two caption rows. It trains an original byte-level text encoder and denoiser from random initialization and then smoke-tests sampling. This is a tiny research experiment; a small dataset will not produce a capable image generator.

## Fallback: image reconstruction

If there are at least two images but no usable caption manifest, the workflow trains `training/image/train_autoencoder.py` to reconstruct 64×64 RGB images. Reconstruction is not prompt-based image generation.

Document source, creator, permission/license, collection date, and content hashes for real datasets. Never commit secrets or private photos without consent.
