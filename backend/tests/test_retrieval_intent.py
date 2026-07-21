"""Tests for deterministic question-intent classification."""

import unittest

from app.retrieval.intent import IntentClassifier, QuestionIntent


class IntentClassifierTests(unittest.TestCase):
    CASES = (
        ("Güvenlik Kuralları ekranına nasıl giderim?", QuestionIntent.NAVIGATION),
        ("SSL VPN ayarları hangi menü altında?", QuestionIntent.NAVIGATION),
        ("Kaynakta verilen ilk menü yolu nedir?", QuestionIntent.NAVIGATION),
        ("Dinamik NAT nasıl oluşturulur?", QuestionIntent.PROCEDURE),
        ("Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?", QuestionIntent.FIRST_ACTION),
        ("Hangi alanları doldurmalıyım?", QuestionIntent.FIELD_LISTING),
        ("Hedef Adres ne işe yarar?", QuestionIntent.FIELD_PURPOSE),
        ("Kaydet butonu ne işe yarar?", QuestionIntent.CONTROL_PURPOSE),
        ("IPSec VPN ile SSL VPN arasındaki fark nedir?", QuestionIntent.COMPARISON),
        ("IPS nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("WAN ne demek?", QuestionIntent.CONCEPT_DEFINITION),
        ("NAT ne işe yarar?", QuestionIntent.CONCEPT_DEFINITION),
        ("VPN açılımı nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("Antispam nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("VLAN nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("DHCP nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("OSPF nedir?", QuestionIntent.CONCEPT_DEFINITION),
        ("Antikor nedir?", QuestionIntent.PRODUCT_OVERVIEW),
        ("Antikor ne işe yarar?", QuestionIntent.PRODUCT_OVERVIEW),
    )

    def test_classifies_supported_intents(self) -> None:
        for question, expected in self.CASES:
            with self.subTest(question=question):
                self.assertEqual(expected, IntentClassifier.classify(question))


if __name__ == "__main__":
    unittest.main()
