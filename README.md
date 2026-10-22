# RC Vision AI

**An independent, local-first Android AI and original-model research project by RC RAJA GAMER 2.0.**

## Non-negotiable project rules
- **No third-party LLM inference APIs.** RC Vision AI must use its own model; no OpenRouter/Gemini/other cloud LLM fallback.
- **No pretrained AI weights or borrowed AI inference engines.** PyTorch is used in the research trainer for tensor/autograd operations only.
- **Honest capability reporting.** The native Android app does not yet load the research checkpoint, so it must not claim local chat or image generation works.
- **Local privacy by default.** The current Android app does not need Internet permission.
- **Measured progress only.** Show actual steps, batches and task states; do not invent percentages.

## Current status
The repository contains an original, randomly initialized, byte-level decoder-only Transformer trainer (training/llm/train.py) and text sampler (training/llm/generate.py). It is an early research prototype, not yet a capable general-purpose assistant. The daily GitHub Actions workflow trains from the project-owned seed corpus and may resume a cached checkpoint. No third-party model is used to answer prompts or generate the training corpus.

The Android app has a native UI shell, local prompt saving/export, device telemetry, and an opt-in authenticated LAN API server prototype (port 8765). That Android server still returns 503 for chat until an Android runtime is integrated. Separately, training/llm/serve.py now provides a self-hosted Python API for a checkpoint trained by this repository, with bearer-token authentication and bounded requests; it requires a supported Python/PyTorch environment and is not bundled in the APK. Read docs/DEVICE_API.md and docs/SELF_HOSTED_INFERENCE.md before enabling either server. The Chat tab is a local-only research console. **Android inference is not integrated yet**, and no trained checkpoint is bundled in the APK. It reports this honestly rather than silently calling an external API. The original image model is a separate research pipeline and cannot produce useful prompt-based images until a suitable permitted dataset is added and the model is trained/evaluated.

## Run research training
Requires Python 3.10+. Install training/llm/requirements.txt, then run:

```bash
python -m pip install -r training/llm/requirements.txt
python training/llm/train.py --corpus training/corpus/rc_vision_original.txt --output artifacts/llm --steps 500
python training/llm/generate.py --checkpoint artifacts/llm/checkpoint-500.pt --prompt "Hello" --new-bytes 80
```

Checkpoint filenames depend on configured step/checkpoint intervals. Inspect artifacts/llm/latest.json and validation metrics; falling loss does not prove useful assistant behaviour.

## Self-hosted local inference API
The repository includes a small API server that loads an original RC Vision AI checkpoint and serves `/health`, `/v1/models`, and `/v1/chat/completions` without calling any hosted LLM. See [docs/SELF_HOSTED_INFERENCE.md](docs/SELF_HOSTED_INFERENCE.md). This runs in a Python/PyTorch environment; it does **not** mean Android inference is already integrated.

## Android app
The native Kotlin app is under app/. It includes Create, Chat, Train and Settings screens, local prompt storage, ZIP export, and on-demand RAM/battery-temperature/thermal/UI-frame estimates. Android inference and sandboxed code execution are future work. See docs/ANDROID_BUILD.md and docs/MODEL_DESIGN.md.

## Roadmap
1. Keep original model training reproducible and evaluate loss, samples, and regression tests.
2. Build a checkpoint import/version/checksum path.
3. Integrate a genuinely local Android inference runtime without a cloud fallback.
4. Add code editor, safe local preview, and isolated test runner as separately tested modules.
5. Continue the original image model only with a documented, permission-cleared image/caption dataset.
6. Benchmark model memory, latency, battery and thermal behaviour on real target phones before promising a 1–1.5 GB model.

The future model-size targets are goals, not currently available capabilities. GitHub Actions is a bounded scheduled/manual job, not a permanent server or a guarantee of continuous training.

## Privacy
Never commit API keys, secrets, private images or personal datasets. The Android local research console does not transmit prompts to a server. The optional Android LAN API and Python self-hosted API only handle requests when you explicitly start those services; protect their tokens and do not expose plain HTTP to the public internet.

## License
No license has been selected. Normal copyright applies until a license is added.
