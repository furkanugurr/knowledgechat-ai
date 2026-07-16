import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.visual_guide_extractor.normalization import GemmaNormalizer
from tools.visual_guide_extractor.schemas.extraction import GuidePage


class GemmaCompactRetryTests(unittest.TestCase):
    def make_normalizer(self, content):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"message": {"content": content}}
        client = Mock()
        client.post.return_value = response
        temporary = tempfile.TemporaryDirectory()
        prompt = Path(temporary.name) / "prompt.txt"
        prompt.write_text("Strict prompt", encoding="utf-8")
        with patch("tools.visual_guide_extractor.normalization.gemma_adapter.httpx.Client", return_value=client):
            normalizer = GemmaNormalizer("http://localhost", "gemma", prompt, 10)
        return temporary, normalizer, client

    def test_detects_truncated_compact_json(self):
        temporary, normalizer, _ = self.make_normalizer('{"page_title":"Eksik')
        self.addCleanup(temporary.cleanup)
        with self.assertRaisesRegex(ValueError, "truncated"):
            normalizer.normalize_compact(GuidePage(page_title="Sayfa", source_url="https://example.test", blocks=[]), [])

    def test_accepts_valid_compact_result(self):
        payload = {"page_title":"x","source_url":"x","overview":"","navigation_paths":[],"controls":[],"fields":[],"ordered_steps":[],"warnings":[],"uncertainties":[]}
        temporary, normalizer, client = self.make_normalizer(json.dumps(payload))
        self.addCleanup(temporary.cleanup)
        result = normalizer.normalize_compact(GuidePage(page_title="Sayfa", source_url="https://example.test", blocks=[]), [])
        self.assertEqual("Sayfa", result.page_title)
        request = client.post.call_args.kwargs["json"]
        self.assertEqual(8192, request["options"]["num_ctx"])


if __name__ == "__main__":
    unittest.main()
