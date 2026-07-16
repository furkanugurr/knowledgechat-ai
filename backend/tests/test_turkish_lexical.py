"""Tests for deterministic Turkish retrieval normalization."""

import unittest

from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


class TurkishLexicalNormalizerTests(unittest.TestCase):
    def test_preserves_known_multi_word_entities_after_normalization(self) -> None:
        entities = TurkishLexicalNormalizer.entities(
            "Yeni Güvenlik Kuralı için Hedef Adres alanına girin."
        )

        self.assertIn("guvenlik kural", entities)
        self.assertIn("hedef adres", entities)
        self.assertIn(
            "yonetim panel kullanici",
            TurkishLexicalNormalizer.entities(
                "Yönetim paneline yeni kullanıcı ekleyin."
            ),
        )

    def test_normalizes_plural_and_case_suffixes_conservatively(self) -> None:
        self.assertEqual("kural", TurkishLexicalNormalizer.token("Kuralları"))
        self.assertEqual("adres", TurkishLexicalNormalizer.token("Adresi"))

    def test_detects_procedural_action_roots(self) -> None:
        actions = TurkishLexicalNormalizer.actions(
            "Kaynak adresi girin, yapılandırmayı kaydedin."
        )

        self.assertEqual({"gir", "kaydet", "yapilandir"}, actions)


if __name__ == "__main__":
    unittest.main()
