"""Tests for the review-only Markdown placeholder."""

import unittest

from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.schemas.extraction import ContentBlock, GuidePage, NormalizedGuide


class MarkdownGeneratorTests(unittest.TestCase):
    def test_generates_draft_placeholder_without_image_markup(self) -> None:
        page = GuidePage(
            page_title="Dinamik NAT",
            source_url="https://example.test/dynamic-nat/",
            blocks=[
                ContentBlock(kind="heading", text="Yeni Kayıt", level=2),
                ContentBlock(kind="paragraph", text="Durum alanını seçin."),
                ContentBlock(
                    kind="image",
                    image_url="https://example.test/image.png",
                    image_index=0,
                ),
            ],
        )

        markdown = MarkdownGenerator().generate(page, [])

        self.assertIn("DRAFT: Review required", markdown)
        self.assertIn("Durum alanını seçin.", markdown)
        self.assertNotIn("![", markdown)
        self.assertNotIn("knowledge_base", markdown)

    def test_approved_markdown_uses_turkish_headings(self) -> None:
        guide = NormalizedGuide.model_validate({"page_title": "Örnek", "source_url": "https://example.test", "overview": "Açıklama", "navigation_paths": [], "controls": [], "fields": [], "ordered_steps": ["İşlemi uygulayın."], "warnings": [], "uncertainties": []})
        markdown = MarkdownGenerator().generate_approved(guide, 0.95)
        self.assertIn("## Kaynak", markdown)
        self.assertIn("## Adımlar", markdown)
        self.assertNotIn("## Steps", markdown)


if __name__ == "__main__":
    unittest.main()
