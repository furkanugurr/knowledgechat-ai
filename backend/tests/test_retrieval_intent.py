"""Tests for deterministic question-intent classification."""

import unittest

from app.retrieval.intent import IntentClassifier, QuestionIntent


class IntentClassifierTests(unittest.TestCase):
    CASES = (
        ("Güvenlik Kuralları ekranına nasıl giderim?", QuestionIntent.NAVIGATION),
        ("SSL VPN ayarları hangi menü altında?", QuestionIntent.NAVIGATION),
        ("Dinamik NAT nasıl oluşturulur?", QuestionIntent.PROCEDURE),
        ("Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?", QuestionIntent.FIRST_ACTION),
        ("Hangi alanları doldurmalıyım?", QuestionIntent.FIELD_LISTING),
        ("Hedef Adres ne işe yarar?", QuestionIntent.FIELD_PURPOSE),
        ("Kaydet butonu ne işe yarar?", QuestionIntent.CONTROL_PURPOSE),
        ("IPSec VPN ile SSL VPN arasındaki fark nedir?", QuestionIntent.COMPARISON),
        ("Antikor nedir?", QuestionIntent.GENERAL_INFORMATION),
    )

    def test_classifies_supported_intents(self) -> None:
        for question, expected in self.CASES:
            with self.subTest(question=question):
                self.assertEqual(expected, IntentClassifier.classify(question))


if __name__ == "__main__":
    unittest.main()
