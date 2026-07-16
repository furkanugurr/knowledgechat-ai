import unittest

from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, VisionExtraction


class DeterministicMarkdownTests(unittest.TestCase):
    def test_copies_only_qwen_evidence(self):
        page = GuidePage(page_title="Kural", source_url="https://example.test", blocks=[])
        vision = VisionExtraction.model_validate({
            "page_title": "Kural", "image_index": 0, "screen_name": "Kural",
            "purpose": "", "visible_navigation_path": "Kurallar",
            "controls": [{"kind": "button", "name": "Ekle", "description": "Düğme"}],
            "fields": [], "ordered_steps": ["Ekle düğmesine tıklayın."],
            "warnings": [], "uncertainties": [],
        })
        guide = MarkdownGenerator().build_deterministic_guide(page, [vision])
        self.assertEqual(["Ekle düğmesine tıklayın."], guide.ordered_steps)
        self.assertEqual(["Ekle"], [item.name for item in guide.controls])
        self.assertEqual("", guide.overview)
        self.assertNotIn("Kaydet", str(guide.model_dump()))

    def test_approved_markdown_omits_english_qwen_description(self):
        page = GuidePage(page_title="Kural", source_url="https://example.test", blocks=[])
        vision = VisionExtraction.model_validate({
            "page_title": "Kural", "image_index": 0, "screen_name": "", "purpose": "",
            "visible_navigation_path": "", "controls": [{"kind": "button", "name": "Ekle", "description": "Click this button to add a new item"}],
            "fields": [], "ordered_steps": [], "warnings": [], "uncertainties": [],
        })
        formatter = MarkdownGenerator()
        guide = formatter.build_deterministic_guide(page, [vision])
        markdown = formatter.generate_approved(guide, 0.90)
        self.assertIn("- `Ekle`", markdown)
        self.assertNotIn("Click this button", markdown)

    def test_pilot_markdown_has_required_sections(self):
        page = GuidePage(page_title="Kural", source_url="https://example.test", blocks=[])
        guide = MarkdownGenerator().build_deterministic_guide(page, [])
        markdown = MarkdownGenerator().generate_pilot_approved(guide, 1.0)
        for heading in ("Kapsam", "Menü yolu", "Kullanım adımları", "Alanlar", "Görünür kontroller", "Uyarılar", "Kaynak bilgisi"):
            self.assertIn(f"## {heading}", markdown)


if __name__ == "__main__":
    unittest.main()
