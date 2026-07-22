from app.retrieval.field_coverage import FieldCoveragePlan
from app.retrieval.models import RetrievedChunk


def _fields(text: str) -> RetrievedChunk:
    return RetrievedChunk(
        document_name="Web Sunucu Güvenliği",
        relative_path="guides/web-sunucu-guvenligi.md",
        section_title="Alanlar",
        chunk_index=1,
        chunk_text=text,
        similarity_score=0.9,
        language="tr",
    )


def test_web_security_fields_are_grouped_without_omission():
    plan = FieldCoveragePlan.build("Web Sunucu Güvenliği", [_fields(
        "- `İstek Gövdesi Boyut Limiti`: İstek sınırını belirler.\n"
        "- `REQUEST-942-APPLICATION-ATTACK-SQLI`: SQLI denetimidir.\n"
        "- `REQUEST-911-METHOD-ENFORCEMENT`: Yöntem denetimidir.\n"
        "- `REQUEST-913-SCANNER-DETECTION`: Tarayıcı tespitidir.\n"
        "- `RESPONSE-950-DATA-LEAKAGES`: Veri sızıntısı denetimidir."
    )])
    assert plan is not None
    assert {group.key for group in plan.important_field_groups} == {
        "body_limits", "application_attacks", "protocol_controls",
        "detection_reputation", "response_data_protection",
    }
    assert not plan.omitted_fields
    assert all(label in plan.render_evidence() for label in plan.all_discovered_fields)


def test_missing_group_detection_and_deterministic_render():
    plan = FieldCoveragePlan.build("Rapor Ayarları", [_fields(
        "- `İmza Algoritması`: İmza yöntemini belirler.\n"
        "- `Sunucu`: Yedekleme sunucusunu belirler."
    )])
    assert plan is not None
    assert plan.missing_answer_groups("Log imzalama ve saklama ayarları açıklanır.") == [
        "server_backup"
    ]
    assert "Sunucuya yedekleme" in plan.render_answer()


def test_attack_options_exclude_only_body_limit_group():
    plan = FieldCoveragePlan.build("Web Sunucu Güvenliği", [_fields(
        "- `İstek Gövdesi Boyut Limiti`: İstek sınırını belirler.\n"
        "- `REQUEST-942-APPLICATION-ATTACK-SQLI`: SQLI denetimidir.\n"
        "- `REQUEST-911-METHOD-ENFORCEMENT`: Yöntem denetimidir.\n"
        "- `REQUEST-913-SCANNER-DETECTION`: Tarayıcı tespitidir.\n"
        "- `RESPONSE-950-DATA-LEAKAGES`: Veri sızıntısı denetimidir."
    )], "Web Sunucu Güvenliği ekranındaki saldırı koruma seçenekleri nelerdir?")
    assert plan is not None
    keys = {group.key for group in plan.important_field_groups}
    assert "body_limits" not in keys
    assert keys == {
        "application_attacks", "protocol_controls",
        "detection_reputation", "response_data_protection",
    }
