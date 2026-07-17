"""Regression coverage for reusable Sprint 22 recovery patterns."""
from app.retrieval.answer_grounding import GroundedAnswerGuard
from app.retrieval.guide_catalog import GuideEntityCatalog
from app.retrieval.intent import QuestionIntent
from app.retrieval.models import RetrievedChunk
from app.retrieval.reranker import DocumentAwareReranker

T = chr(96)
CATALOG = [
    {"title": "Yönetim Paneli Kullanıcıları", "relative_path": "guides/users.md", "category": "users"},
    {"title": "Yönetim Paneli Ayarları", "relative_path": "guides/settings.md", "category": "users"},
    {"title": "Dinamik NAT", "relative_path": "guides/dynamic.md", "category": "nat"},
    {"title": "Statik NAT", "relative_path": "guides/static.md", "category": "nat"},
    {"title": "IPSec VPN Profilleri", "relative_path": "guides/profiles.md", "category": "vpn"},
    {"title": "IPSec VPN Ayarları", "relative_path": "guides/ipsec.md", "category": "vpn"},
    {"title": "SSL VPN Ayarları", "relative_path": "guides/ssl.md", "category": "vpn"},
]


def chunk(section: str, text: str, index: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_text=text, similarity_score=0.9, document_name="guide.md",
        relative_path="guides/guide.md", section_title=section,
        chunk_index=index, language="tr",
    )


def test_catalog_disambiguates_same_category_guides() -> None:
    catalog = GuideEntityCatalog(CATALOG)
    assert catalog.resolve("Yönetim Paneli Kullanıcıları nasıl eklenir?")[0].relative_path == "guides/users.md"
    assert catalog.resolve("Yönetim Paneli Ayarları nasıl yapılır?")[0].relative_path == "guides/settings.md"


def test_catalog_disambiguates_nat_and_vpn_entities() -> None:
    catalog = GuideEntityCatalog(CATALOG)
    assert catalog.resolve("Statik NAT nasıl yapılandırılır?")[0].relative_path == "guides/static.md"
    assert catalog.resolve("IPSec VPN Profilleri nasıl oluşturulur?")[0].relative_path == "guides/profiles.md"
    assert catalog.resolve("SSL VPN Ayarları hangi menü altında?")[0].relative_path == "guides/ssl.md"


def test_navigation_selects_only_menu_section() -> None:
    result = DocumentAwareReranker().select_siblings(
        "SSL VPN Ayarları hangi menü altında?", [],
        [chunk("Kapsam", "genel", 1), chunk("Menü yolu", "- VPN Yönetimi > SSL VPN Ayarları", 2)],
        5, QuestionIntent.NAVIGATION,
    )
    assert [item.section_title for item in result] == ["Menü yolu"]


def test_field_listing_selects_only_field_sections() -> None:
    result = DocumentAwareReranker().select_siblings(
        "hangi alanlar bulunur?", [],
        [chunk("Alanlar", "- "+T+"Hedef Adres"+T+": hedef", 2), chunk("Görünür kontroller", "- "+T+"Kaydet"+T, 3)],
        5, QuestionIntent.FIELD_LISTING,
    )
    assert [item.section_title for item in result] == ["Alanlar"]


def test_procedure_keeps_late_step_chunk_before_menu() -> None:
    result = DocumentAwareReranker().select_siblings(
        "PPP nasıl yapılandırılır?", [],
        [
            chunk("Menü yolu", "- PPP > Yeni Kayıt", 1),
            chunk("Kullanım adımları", "1. Başlatın.", 2),
            chunk("Kullanım adımları", "2. Doldurun.", 3),
            chunk("Kullanım adımları", "3. Kaydet.", 4),
            chunk("Alanlar", "- "+T+"Adı"+T, 5),
            chunk("Görünür kontroller", "- "+T+"Kaydet"+T, 6),
        ],
        5, QuestionIntent.PROCEDURE,
    )
    assert [item.chunk_index for item in result] == [2, 3, 4, 5, 6]


def test_false_limitation_uses_deterministic_field_fallback() -> None:
    evidence = "- "+T+"Kaynak Adres"+T+": kaynak\n- "+T+"Hedef Adres"+T+": hedef"
    answer = GroundedAnswerGuard().ensure_grounded(
        "Hangi alanlar bulunur?", QuestionIntent.FIELD_LISTING,
        [chunk("Alanlar", evidence)], "Bu bilgi mevcut değil.",
    )
    assert "Kaynak Adres" in answer and "Hedef Adres" in answer
    assert "mevcut değil" not in answer


def test_navigation_fallback_returns_supported_path() -> None:
    answer = GroundedAnswerGuard().ensure_grounded(
        "SSL VPN Ayarları hangi menü altında?", QuestionIntent.NAVIGATION,
        [chunk("Menü yolu", "- VPN Yönetimi > SSL VPN Ayarları")],
        "Bilgi bulunamadı.",
    )
    assert answer == "VPN Yönetimi > SSL VPN Ayarları"


def test_navigation_fallback_prefers_identity_hint_for_live_question() -> None:
    answer = GroundedAnswerGuard().ensure_grounded(
        "SSL VPN ayarları hangi menü altında?", QuestionIntent.NAVIGATION,
        [chunk("Menü yolu", "- Sertifika Yönetimi > Kullanıcılar")],
        "Bilgi bulunamadı.", navigation_hint="VPN Yönetimi > SSL VPN Ayarları",
    )
    assert answer == "VPN Yönetimi > SSL VPN Ayarları"


def test_procedure_fallback_preserves_source_order() -> None:
    evidence = "1. "+T+"+ Ekle"+T+" butonuna tıklayın.\n2. "+T+"Kaydet"+T+" butonuna tıklayın."
    answer = GroundedAnswerGuard().ensure_grounded(
        "Nasıl oluşturulur?", QuestionIntent.PROCEDURE,
        [chunk("Kullanım adımları", evidence)], "Bilgi bulunamadı.",
    )
    assert answer.index("+ Ekle") < answer.index("Kaydet")


def test_first_action_fallback_prefers_creation_hint() -> None:
    answer = GroundedAnswerGuard().ensure_grounded(
        "İlk hangi butona basmalıyım?", QuestionIntent.FIRST_ACTION,
        [chunk("Kullanım adımları", "1. Durum seçimi yapın.")],
        "Bilgi bulunamadı.", creation_hint="+ Ekle",
    )
    assert answer == "+ Ekle"


def test_valid_grounded_answer_is_preserved() -> None:
    original = "Hedef adres "+T+"Hedef Adres"+T+" alanına girilir."
    answer = GroundedAnswerGuard().ensure_grounded(
        "Hedef Adres ne işe yarar?", QuestionIntent.FIELD_PURPOSE,
        [chunk("Alanlar", "- "+T+"Hedef Adres"+T+": hedef IP adresini belirler.")],
        original,
    )
    assert answer == original
