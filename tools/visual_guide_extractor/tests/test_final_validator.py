import unittest

from tools.visual_guide_extractor.quality import FinalQualityValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction


class FinalQualityValidatorTests(unittest.TestCase):
    def setUp(self):
        self.page = GuidePage(page_title="Kural", source_url="https://example.test", blocks=[])
        self.vision = VisionExtraction.model_validate({"page_title": "Kural", "image_index": 0, "screen_name": "Kural", "purpose": "Kural ekleme ekranı.", "visible_navigation_path": "Kurallar", "controls": [{"kind": "button", "name": "Ekle", "description": "Yeni kayıt düğmesi."}], "fields": [], "ordered_steps": ["Ekle düğmesine tıklayın."], "warnings": [], "uncertainties": []})

    def guide(self, steps):
        return NormalizedGuide.model_validate({"page_title": "Kural", "source_url": "https://example.test", "overview": "", "navigation_paths": ["Kurallar"], "controls": [{"kind": "button", "name": "Ekle", "description": "Yeni kayıt düğmesi."}], "fields": [], "ordered_steps": steps, "warnings": [], "uncertainties": []})

    def test_rejects_step_with_unknown_control_and_guide(self):
        result = FinalQualityValidator().validate(self.page, [self.vision], self.guide(["İleri butonuna basın."]))
        self.assertFalse(result.approved)
        self.assertEqual([], result.sanitized_guide.ordered_steps)
        self.assertIn("İleri butonuna basın.", result.rejected_sentences)

    def test_approves_supported_step_with_high_confidence(self):
        result = FinalQualityValidator().validate(self.page, [self.vision], self.guide(["Ekle düğmesine tıklayın."]))
        self.assertTrue(result.approved)
        self.assertGreaterEqual(result.confidence_score, 0.8)

    def test_removes_english_ui_translation(self):
        guide = self.guide(["Ekle düğmesine tıklayın."])
        guide.controls[0].name = "Add"
        result = FinalQualityValidator().validate(self.page, [self.vision], guide)
        self.assertFalse(any(item.name == "Add" for item in result.sanitized_guide.controls))


if __name__ == "__main__":
    unittest.main()
