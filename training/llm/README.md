# RC Vision AI — original LLM research prototype

This folder implements a small decoder-only Transformer from random initialization. It does **not** contain or download pretrained weights, an existing tokenizer, or an AI inference engine. PyTorch is used as a numerical/autograd library; the model layers, byte tokenizer, causal attention, training objective, and checkpoint metadata are authored here.

## What this is — and is not

- It is a first, small language-model training experiment.
- It is not a trained general assistant, and its output may be incoherent.
- A UTF-8 byte vocabulary (256 symbols) is intentionally simple and inefficient.
- The corpus must be supplied by you and must be content you have permission to use.
- Training does not happen inside the Android APK yet.
- No usage quota is coded into the trainer, but compute, RAM, disk, heat, and training time are real physical constraints.

## Run

Python 3.10+ and a suitable PyTorch build are required. On a computer or supported Linux environment:

```bash
python -m pip install -r training/llm/requirements.txt
python training/llm/train.py --corpus /path/to/permission-cleared-corpus.txt --steps 1000
```

The corpus should be UTF-8 plain text and at least a few thousand bytes for a useful experiment. Checkpoints and `latest.json` are written under `artifacts/llm/`. Keep generated artifacts out of Git unless intentionally sharing a small, safe research checkpoint.

## Reproducibility and honest evaluation

The script fixes random seeds, hashes the corpus, saves model configuration and optimizer state, reports measured training/validation cross-entropy, and periodically writes checkpoints. Validation is a random batch from a held-out suffix; for serious research, add a stable evaluation suite and document corpus provenance, splits, deduplication, and licensing. A decreasing loss alone does not mean the model is helpful, safe, or good at chat.

## Next engineering milestones

1. Add a robust corpus manifest/provenance validator and deterministic split.
2. Add resume-from-checkpoint and a separately tested sampling CLI.
3. Build a real evaluation suite and safety tests.
4. Implement the conditional image-generation model separately; an autoencoder alone is not a prompt-conditioned image generator.
5. Integrate only after model size, latency, memory, and thermal behavior are measured on target Android devices.