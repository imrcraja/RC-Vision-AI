# Original model design plan

This document defines the research path for two separate model families. No pretrained weights or borrowed open-source AI engine is included. An optional Gemini API workflow may generate synthetic text for training, but Gemini is not the app's inference engine and does not provide the model weights.

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

The first implementation is `training/image/train_autoencoder.py`: a tiny convolutional autoencoder that reconstructs fixed-size images. It is not text-conditioned and must not be marketed as prompt-based image generation. The scheduled workflow only trains it when at least two permitted images exist in `training/images/`.

## 3. Android constraints

- The APK is a native Kotlin app using Android platform APIs, without AndroidX or third-party runtime libraries in this starter.
- The app currently includes no Internet permission and performs no network calls. Gemini API credentials are used only by the GitHub Actions training workflow and must never be embedded in the APK.
- A trained image model plus an LLM may be too large or slow for many phones. We must benchmark the actual target device before choosing quantization, model size, or training features.
- Android's app UI and the model runtime should be separated. Heavy tasks run off the UI thread and must be cancellable.
- Training directly on a phone is a later experiment, not a promise of unlimited compute.

## 4. Daily learning export

`training/package_daily_learning.py` creates a versioned ZIP containing available model artifacts, metrics/metadata, the selected training corpus, a SHA-256 manifest, and empty templates for memory, knowledge, skills, and evaluation records. It does not have access to Android private storage and does not invent or automatically import phone memories. A future Android export/import feature must explicitly transfer user-approved local state and validate hashes/configuration before loading checkpoints.

## 5. Non-negotiable integrity rules

- Never label a random or untrained network as a functioning image generator or assistant.
- Never show invented progress percentages. Use measured steps, batches, or explicit stage states.
- Never silently download or execute model code.
- Gemini-generated text is untrusted training data: review/evaluate it, do not execute it as code.
- The local training engine is a separate project component; GitHub Actions does not run forever and Android background work is subject to OS limits.
- Any future optional dependencies must be reviewed and disclosed; no third-party AI model or inference API may be introduced.
