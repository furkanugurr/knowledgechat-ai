"""Regression coverage for deterministic multi-part question plans."""

import unittest

from app.retrieval.intent import QuestionIntent
from app.retrieval.question_plan import (
    AnswerCompletenessValidator,
    AnswerComponent,
    QuestionPlanner,
)


class QuestionPlannerTests(unittest.TestCase):
    CASES = (
        ("Antikor nedir ve temel olarak hangi amaçlarla kullanılır?", "Antikor", QuestionIntent.PRODUCT_OVERVIEW, ("definition", "purpose"), ("product_document",)),
        ("IPS nedir, ne işe yarar ve Antikor’da nasıl kullanılır?", "IPS", QuestionIntent.CONCEPT_DEFINITION, ("definition", "purpose", "product_usage"), ("product_document", "ips")),
        ("VLAN nedir ve Antikor’da VLAN yapılandırması hangi amaçla yapılır?", "VLAN", QuestionIntent.CONCEPT_DEFINITION, ("definition", "purpose"), ("vlan",)),
        ("Dinamik NAT nedir ve Statik NAT’tan farkı nedir?", "Dinamik NAT", QuestionIntent.COMPARISON, ("definition", "comparison"), ("dinamik-nat", "statik-nat")),
        ("SSL VPN ayarları hangi menü altında bulunur ve ne amaçla kullanılır?", "SSL VPN", QuestionIntent.NAVIGATION, ("purpose", "navigation"), ("ssl-vpn-ayarlari",)),
        ("Yeni bir güvenlik kuralı oluştururken Kaynak Adres ile Hedef Adres arasındaki fark nedir?", "Kaynak Adres ve Hedef Adres", QuestionIntent.COMPARISON, ("comparison",), ("guvenlik-kurallari",)),
        ("Yeni bir yönetim paneli kullanıcısı nasıl oluşturulur? Adımları sırayla açıklar mısın?", "yönetim paneli kullanıcısı", QuestionIntent.PROCEDURE, ("procedure",), ("yonetim-paneli-kullanicilari",)),
        ("Web Sunucu Güvenliği ekranında hangi alanlar bulunur ve bu alanlar ne işe yarar?", "Web Sunucu Güvenliği", QuestionIntent.FIELD_LISTING, ("purpose", "field_listing", "field_purpose"), ("web-sunucu-guvenligi",)),
        ("Rapor Ayarları ekranına nasıl gidilir ve burada hangi ayarlar yapılabilir?", "Rapor Ayarları", QuestionIntent.NAVIGATION, ("navigation", "field_listing"), ("rapor-ayarlari",)),
        ("OSPF nedir ve Antikor’da OSPF yapılandırması nasıl yapılır?", "OSPF", QuestionIntent.PROCEDURE, ("definition", "procedure"), ("ospf",)),
    )

    def test_plans_all_ten_compound_questions(self) -> None:
        for question, entity, intent, components, families in self.CASES:
            with self.subTest(question=question):
                plan = QuestionPlanner.plan(question)
                self.assertEqual(plan.primary_entity, entity)
                self.assertEqual(plan.primary_intent, intent)
                self.assertEqual(tuple(item.value for item in plan.requested_components), components)
                self.assertEqual(plan.preferred_source_families, families)

    def test_completeness_reports_missing_component(self) -> None:
        plan = QuestionPlanner.plan(
            "SSL VPN ayarları hangi menü altında bulunur ve ne amaçla kullanılır?"
        )
        answered = AnswerCompletenessValidator.answered_components(
            plan, "Menü yolu: VPN > SSL VPN Ayarları"
        )
        self.assertIn(AnswerComponent.NAVIGATION, answered)
        self.assertNotIn(AnswerComponent.PURPOSE, answered)

    def test_procedure_requires_ordered_steps(self) -> None:
        plan = QuestionPlanner.plan(
            "OSPF nedir ve Antikor’da OSPF yapılandırması nasıl yapılır?"
        )
        answered = AnswerCompletenessValidator.answered_components(
            plan,
            "OSPF, dinamik yönlendirme protokolüdür.\n\n"
            "1. Router ID alanını doldurun.\n"
            "2. Network ID ve Area alanlarını doldurup Kaydet'e tıklayın.",
        )
        self.assertEqual(set(answered), set(plan.requested_components))

    def test_report_settings_requires_both_field_groups(self) -> None:
        plan = QuestionPlanner.plan(
            "Rapor Ayarları ekranına nasıl gidilir ve burada hangi ayarlar yapılabilir?"
        )
        partial = AnswerCompletenessValidator.answered_components(
            plan, "Menü yolu: Raporlar > Rapor Ayarları\n- İmza Programı: seçilir.\n- Algoritma: seçilir."
        )
        self.assertNotIn(AnswerComponent.FIELD_LISTING, partial)
        complete = AnswerCompletenessValidator.answered_components(
            plan,
            "Menü yolu: Raporlar > Rapor Ayarları\n- İmza Programı: seçilir.\n"
            "- Algoritma: seçilir.\n- Sunucuya Yedekleme: etkinleştirilir.\n- Sunucu Adresi: girilir.",
        )
        self.assertIn(AnswerComponent.FIELD_LISTING, complete)

    def test_antikor_capabilities_use_product_overview_intent(self) -> None:
        plan = QuestionPlanner.plan(
            "Antikor’un temel güvenlik özellikleri nelerdir?"
        )
        self.assertEqual(plan.primary_intent, QuestionIntent.PRODUCT_OVERVIEW)
        self.assertEqual(plan.requested_components, (AnswerComponent.PURPOSE,))


if __name__ == "__main__":
    unittest.main()
