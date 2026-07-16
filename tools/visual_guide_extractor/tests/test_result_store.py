"""Tests for validated vision result persistence."""

import tempfile
import unittest
from pathlib import Path

from tools.visual_guide_extractor.schemas.extraction import VisionExtraction
from tools.visual_guide_extractor.vision.result_store import VisionResultStore


class VisionResultStoreTests(unittest.TestCase):
    def test_persists_result_under_page_directory(self) -> None:
        result = VisionExtraction(
            page_title="Dinamik NAT",
            image_index=1,
            screen_name="Yeni Kayıt",
            purpose="Formu gösterir.",
            visible_navigation_path="",
            controls=[],
            fields=[],
            ordered_steps=[],
            warnings=[],
            uncertainties=[],
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = VisionResultStore(Path(temporary)).save("simple_text", result)
            restored = VisionExtraction.model_validate_json(
                path.read_text(encoding="utf-8")
            )

        self.assertEqual(path.name, "image-1.json")
        self.assertEqual(restored, result)


if __name__ == "__main__":
    unittest.main()
