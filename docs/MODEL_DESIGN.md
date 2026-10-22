# Original model design plan

RC Vision AI is intended to be its own model and engine. **No third-party LLM inference API, pretrained model weights, borrowed tokenizer, or borrowed AI inference engine may be introduced.** The model is trained from random initialization. PyTorch is used only for tensor/autograd primitives in the research trainer.

## 1. Current language model
Current implementation: training/llm/train.py, training/llm/generate.py, and training/corpus/rc_vision_original.txt. It is a tiny byte-level decoder-only Transformer research prototype, not a ChatGPT-equivalent assistant. The scheduled workflow uses only the repository-owned seed corpus and bounded training steps. Checkpoints and train/validation metrics must be inspected before claiming progress.

## 2. Next LLM milestones
- Establish a larger, permission-cleared original corpus with provenance and quality checks.
- Add evaluation tasks for instruction following, code correctness, hallucination rate and regression.
- Version checkpoint schema, checksum, tokenizer format, model config and training metadata.
- Build a checkpoint import path into the Android app.
- Implement local inference without a remote fallback; measure peak memory, latency, thermal impact and battery.
- Add code generation and only run generated code in an explicit restricted sandbox with no automatic file/network access.

## 3. Original image-generation model
The image pipeline is a separate randomly initialized model. It needs a permitted image/caption dataset, training, and evaluation before prompt-based generation can be claimed. A reconstruction autoencoder is not a text-to-image generator.

## 4. Android constraints
- Native Kotlin app; no third-party AI inference runtime is currently integrated.
- No Internet permission is required for the current local-only UI.
- A trained checkpoint is not bundled and Android inference is not implemented yet.
- Heavy work must run off the UI thread, be cancellable, and report measured progress.
- Model size and speed must be benchmarked on target hardware; the planned 1–1.5 GB local model is not yet available.

## 5. Integrity rules
- Never label random or untrained weights as a working assistant or image generator.
- Never fabricate progress percentages or test results.
- Never silently download or execute model code.
- Never add an external LLM API as an inference or training-data shortcut.
