"""Generate educational training text through OpenRouter's OpenAI-compatible chat API.

Read OPENROUTER_API_KEY from the environment. Never write the credential to files or logs.
Generated text is untrusted synthetic data and is not executed as code.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/chat/completions"
TOPICS = [
    "Explain how a tiny language model learns next-token prediction, with accurate beginner-friendly examples.",
    "Write a factual educational passage about Android development, memory limits, and battery-aware background work.",
    "Explain Python programming fundamentals with short original examples described in plain English.",
    "Write a helpful FAQ about AI evaluation, data quality, privacy, and model limitations.",
    "Explain basic mathematics and science concepts in clear, correct language for a student.",
]


def generate(api_key: str, model: str, topic: str, max_tokens: int) -> str:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": (
                "Create original, factual educational training text. Do not include personal data or secrets. "
                "Do not claim to have performed real-world actions. Use clear paragraphs and examples."
            )},
            {"role": "user", "content": "Topic: " + topic},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
            "HTTP-Referer": "https://github.com/imrcraja/RC-Vision-AI",
            "X-Title": "RC Vision AI training corpus builder",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        # Error payloads should not contain the request authorization header.
        raise RuntimeError(f"OpenRouter API returned HTTP {exc.code}: {detail}") from None
    choices = payload.get("choices", [])
    message = choices[0].get("message", {}) if choices else {}
    text = message.get("content", "")
    if isinstance(text, list):
        text = "\n".join(p.get("text", "") for p in text if isinstance(p, dict))
    if not isinstance(text, str) or len(text.strip()) < 100:
        raise RuntimeError("OpenRouter returned too little text; no section was accepted.")
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--topics", type=int, default=2)
    parser.add_argument("--max-output-tokens", type=int, default=1000)
    parser.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", "openrouter/auto"))
    args = parser.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing; configure it as a GitHub Actions secret.")
    if not args.base_corpus.is_file():
        raise SystemExit(f"Base corpus not found: {args.base_corpus}")
    if not 1 <= args.topics <= len(TOPICS):
        parser.error(f"--topics must be between 1 and {len(TOPICS)}")
    sections = [args.base_corpus.read_text(encoding="utf-8").strip()]
    for index, topic in enumerate(TOPICS[:args.topics], start=1):
        print(f"Generating OpenRouter synthetic training section {index}/{args.topics} using model {args.model}...")
        sections.append(generate(key, args.model, topic, args.max_output_tokens))
        if index < args.topics:
            time.sleep(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {args.topics} generated sections; corpus bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
