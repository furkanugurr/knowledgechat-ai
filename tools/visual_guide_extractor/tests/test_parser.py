"""Tests for order-preserving static HTML extraction."""

import unittest

from tools.visual_guide_extractor.crawler.parser import GuidePageParser


HTML = """
<html><body><main>
<h1>Güvenlik Kuralı</h1>
<p>Önce açıklamayı okuyun.</p>
<h2>Yeni Kayıt</h2>
<ol><li>Ekle düğmesine basın.</li><li>Kaydedin.</li></ol>
<p><img src="/images/form.png" alt="Yeni kayıt formu"></p>
<p>İşlem tamamlandı.</p>
</main></body></html>
"""


class GuidePageParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = GuidePageParser().parse(HTML, "https://example.test/guide/")

    def test_extracts_html_content_in_source_order(self) -> None:
        self.assertEqual(self.page.page_title, "Güvenlik Kuralı")
        self.assertEqual(
            [block.kind for block in self.page.blocks],
            ["heading", "paragraph", "heading", "ordered_list", "image", "paragraph"],
        )
        self.assertEqual(self.page.blocks[3].items, ["Ekle düğmesine basın.", "Kaydedin."])

    def test_discovers_and_resolves_images(self) -> None:
        self.assertEqual(len(self.page.image_blocks), 1)
        self.assertEqual(
            self.page.image_blocks[0].image_url,
            "https://example.test/images/form.png",
        )
        self.assertEqual(self.page.image_blocks[0].image_index, 0)


if __name__ == "__main__":
    unittest.main()
