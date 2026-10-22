# Original model design plan

This document defines the research path for two separate model families. No pretrained weights, borrowed open-source AI engine, or third-party inference API is included in this repository.

## 1. Language model (LLM)

The first goal is a tiny experimental decoder-only Transformer trained from random initialization on a small, permission-cleared text corpus. It is a research prototype, not a capable general assistant.

Planned components:
- byte/token encoding with a documented reversible format
- embedding table and positional representation
- causal self-attention and feed-forward blocks
- next-token training objective and deterministic seed
- checkpoint format with version, tensor shapes, checksum, and training metadata
- small held-out evaluation set and honest loss/perplexity reporting

## 2. Image-generation model

The first goal is a small image model trained from random initialization on a carefully documented, permission-cleared dataset. Quality will be limited by dataset scale, model size, and available compute.

Candidate research path:
- image loader and dataset manifest with provenance/permission metadata
- fixed-size image normalization and train/validation split
- compact convolutional autoencoder as an initial experiment
- later investigate a small conditional generative model trained from scratch
- save and validate checkpoints with explicit schema and checksums
- measure reconstruction/generation quality, memory use, speed, and thermal behavior

## 3. Android constraints

- The APK is a native Kotlin app using Android platform APIs, without AndroidX or third-party runtime libraries in this starter.
- The app currently includes no Internet permission and performs no network calls.
- A trained image model plus an LLM may be too large or slow for many phones. We must benchmark the actual target device before choosing quantization, model size, or training features.
- Android's app UI and the model runtime should be separated. Heavy tasks run off the UI thread and must be cancellable.
- Training directly on a phone is a later experiment, not a promise of unlimited compute.

## 4. Non-negotiable integrity rules

- Never label a random or untrained network as a functioning image generator or assistant.
- Never show invented progress percentages. Use measured steps, batches, or explicit stage states.
- Never silently download or execute model code.
- Any future optional dependencies must be reviewed and disclosed; no third-party AI model or inference API may be introduced.
