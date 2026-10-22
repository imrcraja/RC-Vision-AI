# RC Vision AI device API

## Intended use

One Android device can act as the host and another device can call its API. LAN mode is intended for devices on the same trusted Wi-Fi network or hotspot. The host app must remain running while serving requests; Android battery/background limits can stop it.

## Current prototype endpoints

Default port: 8765. A random bearer token is created and saved in app-private preferences.

- `GET /health` — service status and whether inference is ready.
- `GET /v1/models` — reports the local model runtime status.
- `POST /v1/chat/completions` — currently returns HTTP 503 because the trained original LLM is not yet integrated into Android inference.

Every endpoint requires `Authorization: Bearer <token>`. The server is opt-in and starts only when the user taps Start in Settings. Stop it when finished.

Example LAN check:

```sh
curl -H "Authorization: Bearer YOUR_TOKEN" http://HOST_LAN_IP:8765/health
```

## Online access and security

The current prototype uses plain HTTP. **Do not expose port 8765 directly to the public internet or router-port-forward it.** Bearer tokens can be intercepted on untrusted networks. For online use, add an HTTPS reverse proxy or a reputable authenticated tunnel, rate limiting, request limits, key rotation and abuse controls. Do not put the API token in public source code or screenshots.

## What is not done yet

This is API transport scaffolding, not functioning LLM inference. The chat endpoint deliberately returns 503 until the original RC Vision AI checkpoint can be loaded and run locally. The API server currently handles small request bodies and basic endpoints; it is not a production-grade internet service. It does not use any third-party LLM API.
