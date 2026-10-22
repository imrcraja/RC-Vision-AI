# Three-part training plan

This project has three distinct contributors. They are not three unlimited AI brains, and none can guarantee uninterrupted 24/7 work.

## 1. Training directed by the owner through ChatGPT

You give a concrete task in chat. I can help author and review code, datasets, evaluation plans, and workflow changes, then use the connected GitHub tools when available. A GitHub Actions run must be started by an eligible workflow trigger; I cannot secretly keep sending commands to your phone or run indefinitely between messages. Review changes and training results before relying on them.

## 2. Gemini API as an optional synthetic-data teacher

The workflow `.github/workflows/gemini-assisted-training.yml` asks Gemini for short educational text, combines it with the checked-in seed corpus, and trains the repository's own randomly initialized Transformer on that text. This is **data generation followed by local model training**, not Gemini directly modifying model weights.

Setup:
1. Open the GitHub repository settings.
2. Go to **Secrets and variables → Actions → New repository secret**.
3. Name the secret `GEMINI_API_KEY` and paste your key there. Never commit it, put it in source code, or embed it in the Android APK.
4. Open **Actions → Gemini-assisted incremental LLM research training → Run workflow** to start a manual run. A daily scheduled run is also configured.
5. Download the run artifact and inspect the checkpoint metadata, training/validation loss, generated corpus, and smoke-test output.

The workflow is intentionally bounded: 1–5 text sections and 500–4000 training steps per manual run, up to the workflow's 45-minute job limit. The daily schedule is not a 24/7 process. Gemini free-tier availability, quotas, model access, rate limits, and billing are controlled by Google and may change. If the secret is missing or the API quota is exhausted, the run can fail; it does not bypass quotas.

The workflow attempts to continue from a cached checkpoint. GitHub cache is best-effort storage, not a permanent model database. Download artifacts you want to keep; artifacts currently expire after 14 days. Do not assume every run will find a prior checkpoint.

## 3. The local training engine

The current Python trainer is a research prototype that uses PyTorch only for tensor/autograd operations and initializes the model from scratch. It is **not yet integrated into the Android app**, and it is not a useful general-purpose assistant yet. The current native app shell is not a finished on-device training engine.

The next engineering stage is a small, cancellable on-device engine with explicit Start/Pause/Stop controls, checkpoint storage, measured progress, and an Android foreground notification while active. Android may stop or throttle background work due to battery, thermal, memory, or OS policy. A persistent notification improves transparency but cannot guarantee 24/7 execution. Training on a phone will be much smaller and slower than training on a computer runner.

## What "training" means here

- Gemini creates candidate text examples.
- The original Transformer learns next-byte prediction from the corpus using gradient descent.
- The model does not automatically learn every skill, verify facts, or rewrite its own source code.
- Loss going down is not proof of useful conversation ability. Evaluation and safety tests are still required.
- Image generation is a separate model and training pipeline; this workflow does not train an image generator.

## Credential and data safety

Keep the Gemini key only in GitHub Actions secrets. Never print it in logs. Generated text is treated as data, not executable code. Do not send private information to the API. Before using generated text for longer training runs, review its quality and remove errors or unwanted content.
