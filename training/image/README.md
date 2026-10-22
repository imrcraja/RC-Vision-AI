# Original image model research

This directory contains an original, randomly initialized conditional denoiser architecture. It does not include pretrained weights, a pretrained text encoder, a diffusion scheduler, or an image dataset.

## Status

**Architecture prototype only; not a working image generator.** The model expects an embedding from a separately trained original text encoder. That encoder, licensed image-caption corpus, noise schedule, diffusion loss loop, sampler, and quality evaluation still need implementation. Do not label outputs from untrained weights as generated images.

## Why it is not being trained automatically

A meaningful conditional image model needs a substantial collection of rights-cleared image/text pairs. The repository does not currently contain such a dataset. Inventing image-caption pairs or using random noise would not constitute meaningful image-model training. The model is kept small for architecture tests, not intended to create production-quality images.
