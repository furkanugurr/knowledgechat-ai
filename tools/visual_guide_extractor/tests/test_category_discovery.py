import unittest

from tools.visual_guide_extractor.crawler import CriticalCategoryDiscovery


class CriticalCategoryDiscoveryTests(unittest.TestCase):
    def test_discovers_only_target_pages_and_deduplicates_urls(self):
        root = "https://example.test/guide/"
        html = """
        <a href="guvenlik-ayarlari/guvenlik-kurallari">Kurallar</a>
        <a href="guvenlik-ayarlari/guvenlik-kurallari/">Kurallar tekrar</a>
        <a href="nat-yapilandirmasi/dinamik-nat?x=1#top">Dinamik NAT</a>
        <a href="https://outside.test/guide/vpn-yonetimi/test">Dış</a>
        <a href="diger/sayfa">Diğer</a>
        """
        pages = CriticalCategoryDiscovery().discover(html, root)
        self.assertEqual(2, len(pages))
        self.assertEqual("guvenlik_kurallari", pages[0].category_key)
        self.assertTrue(all(page.url.endswith("/") for page in pages))

    def test_normalizes_query_fragment_and_duplicate_slashes(self):
        url = CriticalCategoryDiscovery.normalize_url("HTTPS://Example.Test//guide///page?x=1#y")
        self.assertEqual("https://example.test/guide/page/", url)


if __name__ == "__main__":
    unittest.main()
