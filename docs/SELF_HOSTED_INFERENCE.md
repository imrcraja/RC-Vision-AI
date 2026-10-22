# Self-hosted inference API (original RC Vision model)

This server runs **this repository's own checkpoint** using `training/llm/train.py`. It does not call OpenAI, Gemini, OpenRouter, or another hosted LLM. It is separate from the Android APK's port-8765 transport prototype.

## Reality check

The included model is a tiny byte-level Transformer trained from random initialization. A smoke-test checkpoint may produce incoherent text. This API makes inference available; it does not make the model capable or well-trained. The Android app still does not load this checkpoint directly.

## 1. Install and train a checkpoint

Use Python 3.10+ in a supported Linux/desktop environment. Install PyTorch using its official instructions for your platform, then run:

```bash
python training/llm/train.py \
  --corpus training/corpus/rc_vision_original.txt \
  --output artifacts/llm \
  --steps 100
```

The included corpus is only a small pipeline smoke test. For useful learning, supply a larger, diverse UTF-8 corpus you have permission to use. Training needs real CPU/GPU time and memory.

## 2. Start the API

Set a random bearer token of at least 24 characters. Do not commit it to Git:

```bash
export RC_VISION_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python training/llm/serve.py \
  --checkpoint artifacts/llm/checkpoint-0000100.pt \
  --host 127.0.0.1 \
  --port 8766
```

Change the checkpoint path to the checkpoint actually created by your training run. The default bind address is loopback-only for safety. Do not expose plain HTTP directly to the public internet.

## 3. Check it

Health does not require a token:

```bash
curl http://127.0.0.1:8766/health
```

List models:

```bash
curl -H "Authorization: Bearer $RC_VISION_API_TOKEN" \
  http://127.0.0.1:8766/v1/models
```

Generate a response locally:

```bash
curl http://127.0.0.1:8766/v1/chat/completions \
  -H "Authorization: Bearer $RC_VISION_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Introduce RC Vision AI"}],"max_tokens":120}'
```

The `max_tokens` field is a compatibility name; this byte tokenizer generates UTF-8 bytes, not conventional subword tokens. Generation is capped at 512 bytes per request. Requests are capped at 1 MiB.

## API routes

- `GET /health`: server and checkpoint status.
- `GET /v1/models`: authenticated model metadata.
- `POST /v1/chat/completions`: authenticated local inference.

The service uses a bearer token, constant-time token comparison, bounded request bodies, and trusted-checkpoint loading. It is still a small research server, not production hardened; add HTTPS, network access controls, rate limiting, and operational monitoring before remote use. Never send the token to an untrusted host.
