"""Tests for deterministic out-of-domain settings and scoring."""

from app.core.config import Settings
from app.retrieval.domain_relevance import DomainRelevanceGate
from app.retrieval.models import RetrievedChunk


def chunk(text: str, similarity: float = 0.82) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_text=text,
        similarity_score=similarity,
        document_name="ssl-vpn-ayarlari.md",
        relative_path="guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
        section_title="Menü yolu",
        chunk_index=2,
        language="tr",
    )


def test_settings_accept_domain_gate_thresholds() -> None:
    settings = Settings(
        APP_NAME="KnowledgeChat", APP_VERSION="1", ENVIRONMENT="test",
        HOST="127.0.0.1", PORT=8000, LOG_LEVEL="INFO",
        OLLAMA_HOST="http://localhost:11434", CHAT_MODEL="gemma3:12b",
        EMBEDDING_MODEL="nomic-embed-text", VECTOR_DB_PATH="./data/chroma",
        VECTOR_COLLECTION_NAME="knowledgechat", REQUEST_TIMEOUT=60,
        OUT_OF_DOMAIN_MIN_SIMILARITY=0.71,
        OUT_OF_DOMAIN_MIN_LEXICAL_OVERLAP=0.13,
        OUT_OF_DOMAIN_MIN_GUIDE_CONFIDENCE=0.51,
    )
    assert settings.out_of_domain_min_similarity == 0.71
    assert settings.out_of_domain_min_lexical_overlap == 0.13
    assert settings.out_of_domain_min_guide_confidence == 0.51


def test_gate_rejects_semantically_near_but_lexically_unrelated_evidence() -> None:
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "hamburger faydalı mı",
        [chunk("- `VPN Yönetimi > SSL VPN Ayarları`")],
        {"guide_confidence": 0.8},
    )
    assert not decision.domain_relevant
    assert decision.reason == "no_antikor_domain_signal"
    assert decision.confidence_tier == "low_confidence_or_out_of_domain"


def test_gate_keeps_broad_antikor_question_with_strong_evidence() -> None:
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "bağlantıları nasıl izlerim",
        [chunk("Bağlantıları izlemek için Bağlantı Durumları ekranı kullanılır.", 0.88)],
        {"guide_entity_match": True, "guide_confidence": 1.0},
    )
    assert decision.domain_relevant
    assert decision.reason is None
    assert decision.confidence_tier == "high_confidence_in_domain"


def test_exact_guide_identity_overrides_low_semantic_score() -> None:
    item = chunk(
        "## Alanlar\n- `Hedef Adres`: Trafiğin hedef IP adresi.", 0.62
    )
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "Güvenlik Kuralları ekranında Hedef Adres hangi alandır?",
        [item],
        {
            "guide_entity_match": True,
            "resolved_guide": item.relative_path,
            "dominant_path": item.relative_path,
            "guide_confidence": 1.0,
        },
    )
    assert decision.domain_relevant
    assert decision.entity_signal
    assert decision.ui_label_signal
    assert not decision.semantic_signal
    assert decision.guide_agreement_signal


def test_exact_ui_label_overrides_low_semantic_score_with_guide_agreement() -> None:
    item = chunk("## Alanlar\n- `Hedef Adres`: IP değeri.", 0.61)
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "Hedef Adres alanı ne için kullanılır?",
        [item],
        {"dominant_path": item.relative_path, "guide_confidence": 0.8},
    )
    assert decision.domain_relevant
    assert decision.ui_label_signal
    assert decision.confidence_tier == "high_confidence_in_domain"


def test_category_and_retrieval_agreement_use_conservative_semantic_floor() -> None:
    item = chunk("Ethernet performans ayarları ve trafik değerleri.", 0.63)
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "ethernet performansı", [item],
        {"dominant_path": item.relative_path, "guide_confidence": 0.7},
    )
    assert decision.domain_relevant
    assert decision.confidence_tier == "medium_confidence_in_domain"


def test_ambiguous_generic_label_stays_out_of_domain_without_agreement() -> None:
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "adres alanı", [chunk("## Alanlar\n- `Adres`: Bir adres değeri.", 0.68)],
        {"guide_confidence": 0.2},
    )
    assert not decision.domain_relevant
    assert decision.reason == "retrieval_guide_agreement_missing"


def test_partial_document_overlap_does_not_make_wrong_guide_in_domain() -> None:
    item = chunk("Ethernet Atama ekranında port ataması yapılır.", 0.68)
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "ethernet performansı", [item],
        {"dominant_path": item.relative_path, "guide_confidence": 0.7},
    )
    assert not decision.domain_relevant
    assert decision.confidence_tier == "low_confidence_or_out_of_domain"


def test_high_guide_confidence_supports_short_domain_question() -> None:
    item = chunk("Dinamik NAT kaydı için Ekle kontrolü kullanılır.", 0.64)
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "Yeni NAT kaydında ilk buton hangisi?", [item],
        {"dominant_path": item.relative_path, "guide_confidence": 1.0},
    )
    assert decision.domain_relevant
    assert decision.confidence_tier == "medium_confidence_in_domain"


def test_two_guide_comparison_can_have_retrieval_agreement() -> None:
    first = chunk("IPSec VPN profili ve alanları.", 0.85)
    second = first.model_copy(update={
        "chunk_text": "SSL VPN ayarları ve alanları.",
        "relative_path": "guides/antikor_v2/vpn/ipsec-vpn-ayarlari.md",
        "similarity_score": 0.82,
    })
    decision = DomainRelevanceGate(0.70, 0.12, 0.50).evaluate(
        "IPSec VPN ile SSL VPN arasındaki fark nedir?", [first, second],
        {"dominant_path": first.relative_path, "guide_confidence": 1.0},
    )
    assert decision.domain_relevant
    assert decision.guide_agreement_signal
