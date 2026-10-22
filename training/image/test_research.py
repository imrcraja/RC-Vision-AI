from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import torch
from PIL import Image

from model import RCConditionalDenoiser
from train_diffusion import ByteTextEncoder, CaptionedImages, MAX_TEXT_BYTES


class ImageResearchTests(unittest.TestCase):
    def test_conditioned_denoiser_preserves_image_shape(self):
        encoder = ByteTextEncoder(width=128)
        model = RCConditionalDenoiser(width=32, condition_width=128)
        tokens = torch.randint(0, 256, (2, MAX_TEXT_BYTES))
        lengths = torch.tensor([12, 27])
        condition = encoder(tokens, lengths)
        images = torch.randn(2, 3, 32, 32)
        timesteps = torch.tensor([2, 10])
        predicted_noise = model(images, timesteps, condition)
        self.assertEqual(tuple(predicted_noise.shape), (2, 3, 32, 32))
        self.assertTrue(torch.isfinite(predicted_noise).all().item())

    def test_caption_dataset_loads_pairs_and_blocks_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "images"
            root.mkdir()
            Image.new("RGB", (8, 8), (20, 40, 60)).save(root / "a.png")
            Image.new("RGB", (8, 8), (80, 100, 120)).save(root / "b.png")
            manifest = root / "captions.jsonl"
            manifest.write_text(
                json.dumps({"image": "a.png", "caption": "blue square"}) + "\n" +
                json.dumps({"image": "b.png", "caption": "dark rectangle"}) + "\n",
                encoding="utf-8",
            )
            dataset = CaptionedImages(root, manifest, 32)
            pixels, tokens, length = dataset[0]
            self.assertEqual(tuple(pixels.shape), (3, 32, 32))
            self.assertEqual(tuple(tokens.shape), (MAX_TEXT_BYTES,))
            self.assertGreater(length, 0)
            manifest.write_text(json.dumps({"image": "../outside.png", "caption": "unsafe"}) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                CaptionedImages(root, manifest, 32)


if __name__ == "__main__":
    unittest.main()
