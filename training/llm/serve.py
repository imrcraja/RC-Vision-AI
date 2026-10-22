"""Self-host the project's own trained RC Vision AI checkpoint over a small HTTP API.

No hosted AI provider or third-party model is called. This runs the checkpoint
created by training/llm/train.py using this repository's own model definition.
It is a research prototype; a tiny checkpoint is not a capable assistant.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from train import ByteTokenizer, RCVisionLM


MAX_BODY_BYTES = 1_048_576


def load_model(checkpoint_path: Path, device: torch.device):
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    # Checkpoints must be created by this project and must be trusted.
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    if checkpoint.get("format") != "rc-vision-ai-byte-transformer-v1":
        raise ValueError("Unsupported checkpoint format")
    cfg = checkpoint.get("model_config", {})
    required = {"width", "layers", "heads", "context", "vocab_size"}
    if not required.issubset(cfg) or cfg["vocab_size"] != 256:
        raise ValueError("Invalid model configuration")
    model = RCVisionLM(
        width=int(cfg["width"]), layers=int(cfg["layers"]),
        heads=int(cfg["heads"]), context=int(cfg["context"]), dropout=0.0,
    ).to(device)
    model.load_state_dict(checkpoint["model_state"], strict=True)
    model.eval()
    return model, checkpoint, ByteTokenizer(), device


def format_messages(messages: Any) -> str:
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty array")
    pieces = []
    for item in messages:
        if not isinstance(item, dict):
            raise ValueError("Each message must be an object")
        role = item.get("role")
        content = item.get("content")
        if role not in {"system", "user", "assistant"}:
            raise ValueError("Allowed roles: system, user, assistant")
        if not isinstance(content, str):
            raise ValueError("Message content must be text")
        pieces.append(f"{role}: {content.strip()}")
    pieces.append("assistant:")
    return "\n".join(pieces)


def generate(model, checkpoint, tokenizer, device, prompt: str,
             max_new_bytes: int = 160, temperature: float = 0.8,
             top_k: int = 40) -> str:
    if not prompt.strip():
        raise ValueError("Prompt must not be empty")
    if not 1 <= max_new_bytes <= 512:
        raise ValueError("max_tokens must be between 1 and 512 bytes")
    if not 0.05 <= temperature <= 2.0:
        raise ValueError("temperature must be between 0.05 and 2.0")
    if not 1 <= top_k <= 256:
        raise ValueError("top_k must be between 1 and 256")
    cfg = checkpoint["model_config"]
    prompt_ids = tokenizer.encode(prompt)
    if not prompt_ids:
        raise ValueError("Prompt must not be empty")
    # Keep the most recent context window so long prompts remain bounded.
    generated = torch.tensor([prompt_ids[-cfg["context"]:]], dtype=torch.long, device=device)
    initial_length = generated.shape[1]
    with torch.inference_mode():
        for _ in range(max_new_bytes):
            context = generated[:, -cfg["context"]:]
            logits = model(context)[:, -1, :] / temperature
            values, indices = torch.topk(logits, min(top_k, logits.shape[-1]), dim=-1)
            filtered = torch.full_like(logits, float("-inf"))
            filtered.scatter_(1, indices, values)
            next_id = torch.multinomial(F.softmax(filtered, dim=-1), num_samples=1)
            generated = torch.cat((generated, next_id), dim=1)
    all_text = tokenizer.decode(generated[0].tolist())
    # UTF-8 byte decoding can replace a partial multi-byte character; this is
    # expected for the deliberately simple byte-level research tokenizer.
    return all_text


def make_handler(runtime, bearer_token: str):
    model, checkpoint, tokenizer, device = runtime

    class Handler(BaseHTTPRequestHandler):
        server_version = "RCVisionAIResearch/0.1"

        def log_message(self, fmt, *args):
            # Avoid logging prompts or bearer tokens.
            print(f"{self.client_address[0]} - {fmt % args}")

        def _send(self, status: int, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _authorized(self) -> bool:
            header = self.headers.get("Authorization", "")
            prefix = "Bearer "
            supplied = header[len(prefix):] if header.startswith(prefix) else ""
            return bool(supplied) and secrets.compare_digest(supplied, bearer_token)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"status": "ok", "model_loaded": True,
                                 "inference": "research_checkpoint",
                                 "checkpoint_step": int(checkpoint.get("step", 0))})
                return
            if not self._authorized():
                self._send(401, {"error": {"message": "Bearer token required", "type": "authentication_error"}})
                return
            if self.path == "/v1/models":
                self._send(200, {"object": "list", "data": [{
                    "id": "rc-vision-local", "object": "model",
                    "owned_by": "rc-vision-ai",
                    "checkpoint_step": int(checkpoint.get("step", 0)),
                    "note": "Small original research model; not a general-purpose assistant."
                }]})
            else:
                self._send(404, {"error": {"message": "Not found", "type": "not_found"}})

        def do_POST(self):
            if not self._authorized():
                self._send(401, {"error": {"message": "Bearer token required", "type": "authentication_error"}})
                return
            if self.path != "/v1/chat/completions":
                self._send(404, {"error": {"message": "Not found", "type": "not_found"}})
                return
            try:
                raw_length = self.headers.get("Content-Length", "")
                if not raw_length.isdigit():
                    raise ValueError("Content-Length is required")
                length = int(raw_length)
                if length < 1 or length > MAX_BODY_BYTES:
                    self._send(413, {"error": {"message": "Request body must be 1 byte to 1 MiB", "type": "invalid_request_error"}})
                    return
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("Request must be a JSON object")
                prompt = format_messages(body.get("messages"))
                result = generate(
                    model, checkpoint, tokenizer, device, prompt,
                    max_new_bytes=int(body.get("max_tokens", 160)),
                    temperature=float(body.get("temperature", 0.8)),
                    top_k=int(body.get("top_k", 40)),
                )
                self._send(200, {
                    "id": "rcvision-local-research",
                    "object": "chat.completion",
                    "model": "rc-vision-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": result},
                                 "finish_reason": "length"}],
                    "usage": {"prompt_tokens": len(tokenizer.encode(prompt)),
                              "completion_tokens": int(body.get("max_tokens", 160)),
                              "total_tokens": len(tokenizer.encode(prompt)) + int(body.get("max_tokens", 160))},
                    "research_notice": "Original byte-level research checkpoint; outputs may be incoherent.",
                })
            except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self._send(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})
            except Exception as exc:
                self._send(500, {"error": {"message": f"Inference failed: {type(exc).__name__}", "type": "server_error"}})

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1", help="Defaults to loopback for safety")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be 1..65535")
    token = os.environ.get("RC_VISION_API_TOKEN", "").strip()
    if len(token) < 24:
        parser.error("Set RC_VISION_API_TOKEN to a random secret of at least 24 characters")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    runtime = load_model(args.checkpoint, device)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(runtime, token))
    print(f"RC Vision AI own-checkpoint API listening on {args.host}:{args.port}")
    print(f"Loaded checkpoint step={runtime[1].get('step', 0)} on {device}")
    print("No third-party LLM API is used. Outputs are research quality only.")
    print("Use loopback by default; do not expose plain HTTP directly to the public internet.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server…")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
