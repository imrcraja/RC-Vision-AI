from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "training" / "package_daily_learning.py"


class DailyPackageTests(unittest.TestCase):
    def test_zip_contains_learning_schemas_hashes_and_selected_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            llm = root / "llm"; llm.mkdir()
            (llm / "checkpoint-test.pt").write_bytes(b"test-checkpoint")
            (llm / "latest.json").write_text('{"step": 3}', encoding="utf-8")
            (llm / ".env").write_text("SECRET=must-not-export", encoding="utf-8")
            corpus = root / "corpus.txt"; corpus.write_text("permitted seed corpus", encoding="utf-8")
            output = root / "daily.zip"
            subprocess.run([
                sys.executable, str(SCRIPT), "--output", str(output),
                "--llm-dir", str(llm), "--image-dir", str(root / "missing-images"),
                "--corpus", str(corpus), "--state-dir", str(root / "missing-state"),
            ], check=True, capture_output=True, text=True)
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                prefix = "RC-Vision-AI-Learning/"
                for required in ("memory.json", "knowledge.json", "skills.json", "evaluation.json", "manifest.json"):
                    self.assertIn(prefix + required, names)
                self.assertIn(prefix + "models/llm/checkpoint-test.pt", names)
                self.assertIn(prefix + "training-data/seed-corpus.txt", names)
                self.assertFalse(any(name.endswith("/.env") for name in names))
                manifest = json.loads(archive.read(prefix + "manifest.json"))
                entries = {item["path"]: item for item in manifest["files"]}
                payload = archive.read(prefix + "models/llm/checkpoint-test.pt")
                self.assertEqual(entries["models/llm/checkpoint-test.pt"]["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertTrue(manifest["model_status"]["llm_checkpoint_included"])
                self.assertFalse(manifest["model_status"]["image_checkpoint_included"])

    def test_empty_artifact_dirs_still_create_valid_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "empty.zip"
            subprocess.run([
                sys.executable, str(SCRIPT), "--output", str(output),
                "--llm-dir", str(root / "none-llm"), "--image-dir", str(root / "none-image"),
                "--corpus", str(root / "none-corpus"), "--state-dir", str(root / "none-state"),
            ], check=True, capture_output=True, text=True)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("RC-Vision-AI-Learning/manifest.json", archive.namelist())


if __name__ == "__main__":
    unittest.main()
