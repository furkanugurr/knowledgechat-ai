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
    {"title": "Global NAT", "relative_path": "guides/global.md", "category": "nat"},
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
    assert catalog.resolve("Dinamik NAT nasıl oluşturulur?")[0].relative_path == "guides/dynamic.md"
    assert catalog.resolve("Global NAT nasıl oluşturulur?")[0].relative_path == "guides/global.md"
    assert catalog.resolve("IPSec VPN Profilleri nasıl oluşturulur?")[0].relative_path == "guides/profiles.md"
    assert catalog.resolve("SSL VPN Ayarları hangi menü altında?")[0].relative_path == "guides/ssl.md"


def test_catalog_preserves_duplicate_titles_and_uses_category_context() -> None:
    catalog = GuideEntityCatalog([
        {"title": "Ethernet Bant Genişlikleri", "relative_path": "guides/anlik/ethernet.md", "category": "anlik gozlem", "available_sections": "Menü yolu|Alanlar"},
        {"title": "Ethernet Bant Genişlikleri", "relative_path": "guides/performans/ethernet.md", "category": "performans", "available_sections": "Alanlar"},
    ])
    result = catalog.resolve(
        "Performans bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?",
        intent=QuestionIntent.FIELD_LISTING,
    )
    assert [item.relative_path for item in result] == ["guides/performans/ethernet.md"]


def test_catalog_does_not_arbitrarily_choose_an_ambiguous_duplicate_title() -> None:
    catalog = GuideEntityCatalog([
        {"title": "Ethernet Bant Genişlikleri", "relative_path": "guides/anlik/ethernet.md", "category": "anlik gozlem"},
        {"title": "Ethernet Bant Genişlikleri", "relative_path": "guides/performans/ethernet.md", "category": "performans"},
    ])
    assert catalog.resolve("Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?") == []


def test_catalog_removes_site_suffix_and_keeps_full_guide_identity() -> None:
    catalog = GuideEntityCatalog([
        {"title": "Hotspot Açık Hedefler - ePati Siber Güvenlik", "relative_path": "guides/hotspot/open.md", "category": "hotspot"},
        {"title": "Hotspot Ayarları", "relative_path": "guides/hotspot/settings.md", "category": "hotspot"},
        {"title": "Kullanıcı Grup Atama", "relative_path": "guides/hotspot/groups.md", "category": "hotspot"},
        {"title": "Kullanıcı Grupları", "relative_path": "guides/users/groups.md", "category": "users"},
    ])
    assert catalog.resolve("Hotspot Açık Hedefler ekranında hangi alanlar bulunur?")[0].relative_path == "guides/hotspot/open.md"
    assert catalog.resolve("Kullanıcı Grup Atama için menü yolu nedir?")[0].relative_path == "guides/hotspot/groups.md"


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


def test_navigation_fallback_keeps_supported_path_with_context_prefix() -> None:
    answer = GroundedAnswerGuard().ensure_grounded(
        "Kullanıcı Grup Atama için kaynakta verilen menü yolu nedir?",
        QuestionIntent.NAVIGATION,
        [chunk("Menü yolu", "- "+T+"Antikor > hotspot islemleri > hotspot kullanici grup atama"+T)],
        "Bilgi bulunamadı.", navigation_hint="Kullanıcı Grup Atama",
    )
    assert answer == "Antikor > hotspot islemleri > hotspot kullanici grup atama"


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


def test_generic_nat_creation_prefers_dynamic_nat_evidence() -> None:
    candidates = [
        RetrievedChunk(chunk_text="## Görünür kontroller\n- `+ Ekle`", similarity_score=0.91,
                       document_name="statik-nat.md", relative_path="guides/antikor_v2/nat/statik-nat.md",
                       section_title="Görünür kontroller", chunk_index=4, language="tr"),
        RetrievedChunk(chunk_text="## Görünür kontroller\n- `+ Ekle`", similarity_score=0.82,
                       document_name="dinamik-nat.md", relative_path="guides/antikor_v2/nat/dinamik-nat.md",
                       section_title="Görünür kontroller", chunk_index=4, language="tr"),
    ]
    ranked = DocumentAwareReranker().rank(
        "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?",
        candidates, QuestionIntent.FIRST_ACTION,
    )
    assert ranked[0].chunk.relative_path.endswith("/dinamik-nat.md")
    assert DocumentAwareReranker().hinted_path(
        "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?"
    ).endswith("/dinamik-nat.md")


def test_valid_grounded_answer_is_preserved() -> None:
    original = "Hedef adres "+T+"Hedef Adres"+T+" alanına girilir."
    answer = GroundedAnswerGuard().ensure_grounded(
        "Hedef Adres ne işe yarar?", QuestionIntent.FIELD_PURPOSE,
        [chunk("Alanlar", "- "+T+"Hedef Adres"+T+": hedef IP adresini belirler.")],
        original,
    )
    assert answer == original
