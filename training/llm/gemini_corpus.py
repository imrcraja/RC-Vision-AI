"""Create a small synthetic text corpus using the Gemini REST API.

The API key is read only from GEMINI_API_KEY. It is never written to files or logs.
This script creates training text; it does not execute generated content.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
TOPICS = [
    "Explain how a tiny language model learns next-token prediction, using accurate beginner-friendly examples.",
    "Write a factual educational passage about Android app development, memory limits, and battery-aware background work.",
    "Explain Python programming fundamentals with short original examples described in plain English.",
    "Write a helpful FAQ about responsible AI, evaluation, data quality, privacy, and model limitations.",
    "Explain basic mathematics and science concepts in clear, correct language for a student.",
]


def generate(api_key: str, topic: str, max_tokens: int) -> str:
    body = {
        "contents": [{"role": "user", "parts": [{"text":
            "Create original, factual educational training text. Do not include personal data, secrets, "
            "instructions to execute code, or claims that you performed real-world actions. "
            "Use clear paragraphs and examples. Topic: " + topic
        }]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens},
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not print request headers or the secret key.
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {detail}") from None
    candidates = payload.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if len(text.strip()) < 100:
        raise RuntimeError("Gemini returned too little text; no corpus was accepted.")
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--topics", type=int, default=5)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    args = parser.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise SystemExit("GEMINI_API_KEY is missing. Add it as a GitHub Actions repository secret.")
    if not args.base_corpus.is_file():
        raise SystemExit(f"Base corpus not found: {args.base_corpus}")
    if not 1 <= args.topics <= len(TOPICS):
        parser.error(f"--topics must be between 1 and {len(TOPICS)}")
    sections = [args.base_corpus.read_text(encoding="utf-8").strip()]
    for index, topic in enumerate(TOPICS[:args.topics], start=1):
        print(f"Generating synthetic training section {index}/{args.topics}...")
        sections.append(generate(key, topic, args.max_output_tokens))
        if index < args.topics:
            time.sleep(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {args.topics} generated sections; corpus bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
