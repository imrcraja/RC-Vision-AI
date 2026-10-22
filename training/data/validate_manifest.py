"""Validate a JSONL dataset manifest without loading or uploading dataset contents."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

REQUIRED = {"path", "sha256", "source", "license", "permission", "split"}
ALLOWED_SPLITS = {"train", "validation", "test"}

def validate(root: Path, manifest: Path) -> list[str]:
    errors: list[str] = []
    seen_hashes: set[str] = set()
    root = root.resolve()
    if not manifest.is_file(): return [f"Manifest not found: {manifest}"]
    for line_no, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"): continue
        try: row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}"); continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: each row must be a JSON object"); continue
        missing = REQUIRED - row.keys()
        if missing: errors.append(f"line {line_no}: missing fields: {sorted(missing)}"); continue
        if not all(isinstance(row[k], str) and row[k].strip() for k in REQUIRED):
            errors.append(f"line {line_no}: required fields must be non-empty strings"); continue
        if row["permission"].lower() not in {"owned", "licensed", "public-domain", "explicit-consent"}:
            errors.append(f"line {line_no}: permission must document owned/licensed/public-domain/explicit-consent"); continue
        if row["split"] not in ALLOWED_SPLITS:
            errors.append(f"line {line_no}: split must be one of {sorted(ALLOWED_SPLITS)}"); continue
        digest = row["sha256"].lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"line {line_no}: sha256 must be 64 hexadecimal characters"); continue
        if digest in seen_hashes:
            errors.append(f"line {line_no}: duplicate content hash (possible duplicate data)")
        seen_hashes.add(digest)
        item = (root / row["path"]).resolve()
        if item != root and root not in item.parents:
            errors.append(f"line {line_no}: path escapes dataset root"); continue
        if not item.is_file():
            errors.append(f"line {line_no}: file not found: {row[chr(112)+chr(97)+chr(116)+chr(104)]}"); continue
        actual = hashlib.sha256(item.read_bytes()).hexdigest()
        if actual != digest: errors.append(f"line {line_no}: SHA-256 mismatch for {row[chr(112)+chr(97)+chr(116)+chr(104)]}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="root directory containing dataset files")
    parser.add_argument("--manifest", type=Path, required=True, help="JSONL manifest path")
    args = parser.parse_args()
    errors = validate(args.root, args.manifest)
    if errors:
        print("Dataset manifest INVALID:")
        for error in errors: print(f"- {error}")
        return 1
    print("Dataset manifest valid: required metadata and file hashes checked.")
    print("Note: this validates declared metadata, not whether a license claim is legally correct.")
    return 0

if __name__ == "__main__": raise SystemExit(main())