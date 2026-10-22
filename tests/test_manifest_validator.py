import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'training' / 'data'))
from validate_manifest import validate

class ManifestValidatorTests(unittest.TestCase):
    def test_valid_manifest_checks_file_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / 'corpus.txt'
            payload.write_text('permission-cleared sample', encoding='utf-8')
            row = {'path':'corpus.txt','sha256':hashlib.sha256(payload.read_bytes()).hexdigest(),
                   'source':'author-created','license':'owned','permission':'owned','split':'train'}
            manifest = root / 'manifest.jsonl'
            manifest.write_text(json.dumps(row) + '\n', encoding='utf-8')
            self.assertEqual(validate(root, manifest), [])

    def test_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'corpus.txt').write_text('changed data', encoding='utf-8')
            row = {'path':'corpus.txt','sha256':'0' * 64,'source':'author-created',
                   'license':'owned','permission':'owned','split':'train'}
            manifest = root / 'manifest.jsonl'
            manifest.write_text(json.dumps(row) + '\n', encoding='utf-8')
            self.assertTrue(any('SHA-256 mismatch' in e for e in validate(root, manifest)))

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'dataset'
            root.mkdir()
            outside = Path(tmp) / 'outside.txt'
            outside.write_text('not inside root', encoding='utf-8')
            row = {'path':'../outside.txt','sha256':hashlib.sha256(outside.read_bytes()).hexdigest(),
                   'source':'author-created','license':'owned','permission':'owned','split':'train'}
            manifest = root / 'manifest.jsonl'
            manifest.write_text(json.dumps(row) + '\n', encoding='utf-8')
            self.assertTrue(any('escapes dataset root' in e for e in validate(root, manifest)))

if __name__ == '__main__':
    unittest.main()