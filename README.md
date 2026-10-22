# RC Vision AI

**An independent, local-first Android AI app and original-model research project by RC RAJA GAMER 2.0.**

RC Vision AI is being built from the ground up. The project does not import pretrained AI models or borrowed inference engines. An optional remote API workflow can be configured as a bounded synthetic-text teacher; the original model is still trained from random initialization. The first milestone is a transparent, testable local runtime foundation; image generation will require developing and training our own model and dataset pipeline.

## Project principles

- **Original model weights and training code:** no pretrained model or borrowed inference engine. Remote APIs are optional helpers, not the original model's inference engine.
- **No borrowed open-source AI model/engine.** All project code is authored for this repository.
- **Local-first app:** the starter Android runtime remains offline; Gemini access is confined to a GitHub Actions secret and workflow.
- **Honest progress:** report known task states and real measurements; never fabricate a percentage.
- **Resource-aware:** detect available system information where supported and degrade gracefully on Android.
- **Sequential heavy work:** one scheduled heavy task at a time.
- **User-owned learning:** future feedback/preferences and training artifacts stay local unless the user explicitly exports them.

## Current status

This is an early engineering foundation. A native Android app shell now exists with Create, Chat, Train, and Settings screens plus device-local prompt saving. **It is not yet a working LLM or image generator**: those original models still need architecture implementation, training data, training, and evaluation. The app intentionally does not fake AI responses.

## Quick start

Requires Python 3.10 or newer. No third-party Python packages are required for the starter runtime.

```bash
PYTHONPATH=src python -m rc_vision_ai status
PYTHONPATH=src python -m rc_vision_ai monitor
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run from the repository root. These commands use the Python standard library at runtime; the optional packaging metadata is for future installation workflows. On Android, use a Python environment such as Termux; available telemetry varies by device and OS.

## Android app

The native Kotlin Android module is in `app/`. It has animated liquid-glass-inspired panels, screen entrance transitions, local prompt saving, a best-effort daily JobScheduler export into app-private storage, and a user-triggered ZIP export of saved prompts plus empty learning templates. Android may delay scheduled jobs, and the ZIP does not include trained model weights or automatically inferred memories. The Chat screen now has an opt-in OpenRouter API client; the user enters a rotated key at runtime, the app keeps it in memory only, and the key is not stored in the repository or app preferences. This requires Internet permission. The OpenRouter chat client does not execute generated code in a sandbox and does not itself train the local model. Build requirements are in [`docs/ANDROID_BUILD.md`](docs/ANDROID_BUILD.md). GitHub Actions is configured to build a debug APK and upload it as a 14-day artifact when the workflow succeeds; verify the run before treating the APK as available.

Model research for the original LLM and image pipeline is documented in [`docs/MODEL_DESIGN.md`](docs/MODEL_DESIGN.md). The optional Gemini-assisted training workflow and its limits are described in [`docs/GEMINI_TRAINING.md`](docs/GEMINI_TRAINING.md). A scheduled hybrid workflow now builds a versioned daily learning ZIP via [`training/package_daily_learning.py`](training/package_daily_learning.py). The image research pipeline now includes an original conditional diffusion training/sampling prototype (`training/image/train_diffusion.py` and `training/image/generate_image.py`) plus an autoencoder reconstruction fallback. It is not a useful image generator until trained and evaluated on a suitable permitted image-caption dataset. See [`training/images/README.md`](training/images/README.md) before adding data.

## Planned milestones

1. **Runtime foundation:** CLI, sequential task scheduler, resource telemetry, tests. (In progress)
2. **Local workspace:** prompt/history/preferences storage with explicit user controls.
3. **Original data pipeline:** dataset manifests, validation, deduplication reports, consent/licensing metadata.
4. **Original model research:** document architecture decisions and implement components in-house.
5. **Training and evaluation:** reproducible configs, checkpoints, honest metrics, safety checks.
6. **Image generation UI:** prompt input, reference-image workflow, task progress and output gallery once a trained model is usable.
7. **Daily learning export:** a GitHub Actions workflow can package its own checkpoints, metrics, seed/generated corpus, and empty memory/knowledge/skills/evaluation templates into a versioned ZIP. Phone-local state is not yet connected to this export.
8. **Android integration:** implement local model runtime, background-safe training, and explicit phone ZIP export/import. This remains future work.

## Safety and privacy

The starter runtime makes no network requests, does not execute downloaded code, and does not upload files. Future network or export features must be opt-in and clearly described. Never commit credentials, private images, or personal datasets.

## License

No license has been selected yet. Until one is added, assume normal copyright applies; do not treat this repository as permission to redistribute its contents.
