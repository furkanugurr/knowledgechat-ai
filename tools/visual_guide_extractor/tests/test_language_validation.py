import unittest

from tools.visual_guide_extractor.quality import LanguageValidator


class LanguageValidatorTests(unittest.TestCase):
    def test_detects_english_sentence_but_allows_technical_terms(self):
        validator = LanguageValidator()
        self.assertEqual(["Click the Save button"], validator.english_sentences(["IP, DNS ve NAT ayarları", "Click the Save button"]))

    def test_detects_translated_source_ui_label(self):
        self.assertEqual(1, len(LanguageValidator().translated_ui_labels(["Save"], ["Kaydet"])))


if __name__ == "__main__":
    unittest.main()
