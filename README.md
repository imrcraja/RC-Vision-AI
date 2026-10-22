# RC Vision AI

**An independent, local-first image AI research project by RC RAJA GAMER 2.0.**

RC Vision AI is being built from the ground up. The repository does not depend on third-party AI APIs or import an existing open-source image-generation model/engine. The first milestone is a transparent, testable local runtime foundation; image generation will require developing and training our own model and dataset pipeline.

## Project principles

- **No third-party AI APIs** and no remote inference requirement.
- **No borrowed open-source AI model/engine.** All project code is authored for this repository.
- **Local-first:** no network calls in the starter runtime.
- **Honest progress:** report known task states and real measurements; never fabricate a percentage.
- **Resource-aware:** detect available system information where supported and degrade gracefully on Android.
- **Sequential heavy work:** one scheduled heavy task at a time.
- **User-owned learning:** future feedback/preferences and training artifacts stay local unless the user explicitly exports them.

## Current status

This is an early engineering foundation, **not yet an image generator**. The starter CLI and scheduler help establish the runtime and tests. Producing high-quality images from scratch requires a substantial original model architecture, lawful training data, compute, and training time; no such trained model is included.

## Quick start

Requires Python 3.10 or newer. No third-party Python packages are required for the starter runtime.

```bash
PYTHONPATH=src python -m rc_vision_ai status
PYTHONPATH=src python -m rc_vision_ai monitor
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run from the repository root. These commands use the Python standard library at runtime; the optional packaging metadata is for future installation workflows. On Android, use a Python environment such as Termux; available telemetry varies by device and OS.

## Planned milestones

1. **Runtime foundation:** CLI, sequential task scheduler, resource telemetry, tests. (In progress)
2. **Local workspace:** prompt/history/preferences storage with explicit user controls.
3. **Original data pipeline:** dataset manifests, validation, deduplication reports, consent/licensing metadata.
4. **Original model research:** document architecture decisions and implement components in-house.
5. **Training and evaluation:** reproducible configs, checkpoints, honest metrics, safety checks.
6. **Image generation UI:** prompt input, reference-image workflow, task progress and output gallery once a trained model is usable.
7. **Export/import:** versioned ZIP packages for project settings and compatible training artifacts; verify manifests before import.

## Safety and privacy

The starter runtime makes no network requests, does not execute downloaded code, and does not upload files. Future network or export features must be opt-in and clearly described. Never commit credentials, private images, or personal datasets.

## License

No license has been selected yet. Until one is added, assume normal copyright applies; do not treat this repository as permission to redistribute its contents.
