"""Build a daily, versioned ZIP of explicitly provided learning artifacts.

The script only packages files present in the selected directories. It does not infer
memories from chat, create model weights, or include credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/daily-learning.zip"))
    parser.add_argument("--llm-dir", type=Path, default=Path("artifacts/llm"))
    parser.add_argument("--image-dir", type=Path, default=Path("artifacts/image"))
    parser.add_argument("--corpus", type=Path, default=Path("training/corpus/rc_vision_original.txt"))
    parser.add_argument("--state-dir", type=Path, default=Path("learning-state"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    with tempfile.TemporaryDirectory(prefix="rc-vision-learning-") as temporary:
        root = Path(temporary) / "RC-Vision-AI-Learning"
        root.mkdir()
        write_json(root / "memory.json", {"schema_version": 1, "memories": [], "note": "Empty template. Add only user-approved memories."})
        write_json(root / "knowledge.json", {"schema_version": 1, "topics": [], "note": "Record known facts, evidence, confidence, and gaps."})
        write_json(root / "skills.json", {"schema_version": 1, "skills": [], "note": "Record tested skills with reproducible evidence."})
        write_json(root / "evaluation.json", {"schema_version": 1, "tests": [], "note": "Add actual test results; do not infer success from training loss."})
        write_json(root / "session.json", {
            "schema_version": 1, "created_utc": stamp, "project": "RC Vision AI",
            "python": platform.python_version(), "platform": platform.platform(),
            "privacy": "This package includes only explicitly selected project artifacts and learning-state JSON. No API keys are included by design.",
        })

        copied = []
        def add_file(source: Path, relative: str) -> None:
            if not source.is_file():
                return
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(destination)

        if args.corpus.is_file():
            add_file(args.corpus, "training-data/seed-corpus.txt")
        for source_dir, prefix in ((args.llm_dir, "models/llm"), (args.image_dir, "models/image"), (args.state_dir, "learning-state")):
            if source_dir.is_dir():
                for source in sorted(source_dir.rglob("*")):
                    if source.is_file() and not source.is_symlink():
                        # Exclude likely secret/config files even if accidentally placed in artifact dirs.
                        if source.name.lower() in {".env", "credentials.json", "secrets.json"}:
                            continue
                        add_file(source, f"{prefix}/{source.relative_to(source_dir).as_posix()}")

        manifest_files = []
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"):
            manifest_files.append({
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
        write_json(root / "manifest.json", {
            "schema_version": 1, "package": "RC Vision AI Daily Learning",
            "created_utc": stamp, "files": manifest_files,
            "model_status": {
                "llm_checkpoint_included": any(item["path"].startswith("models/llm/") and item["path"].endswith(".pt") for item in manifest_files),
                "image_checkpoint_included": any(item["path"].startswith("models/image/") and item["path"].endswith(".pt") for item in manifest_files),
                "image_model_note": "The included autoencoder, if present, is for image reconstruction research, not text-conditioned image generation.",
            },
            "important": "This ZIP does not automatically contain a phone's private memory or device checkpoint. Those must be explicitly exported by the Android app in a future integration.",
        })
        temporary_zip = output.with_suffix(output.suffix + ".tmp")
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(p for p in root.rglob("*") if p.is_file()):
                archive.write(path, path.relative_to(root.parent).as_posix())
        os.replace(temporary_zip, output)
    print(f"Created {output} ({output.stat().st_size} bytes)")
    print("Note: a ZIP export is not proof of model improvement; inspect its manifest and measured metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
