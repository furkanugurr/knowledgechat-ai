"""Tests for retrieval-augmented chat orchestration."""

import unittest
from collections.abc import Sequence

from app.providers.base import LLMProvider, LLMProviderTimeoutError
from app.retrieval.models import RetrievalResult, RetrievedChunk
from app.retrieval.retriever import (
    EmptyCollectionError,
    RetrievalSearchError,
)
from app.services.chat_service import (
    GREETING_RESPONSE,
    INSUFFICIENT_CONCEPT_DEFINITION_RESPONSE,
    NO_RELEVANT_CONTEXT_RESPONSE,
    ChatPromptError,
    ChatRetrievalError,
    ChatService,
)


class RecordingProvider(LLMProvider):
    """LLM provider test double recording the final prompt."""

    def __init__(self, response: str = "Generated response") -> None:
        self.received_prompt: str | None = None
        self.call_count = 0
        self.response = response

    async def generate_response(self, prompt: str) -> str:
        self.call_count += 1
        self.received_prompt = prompt
        return self.response

    async def health_check(self) -> bool:
        return True


class TimeoutProvider(RecordingProvider):
    """LLM provider test double simulating an Ollama timeout."""

    async def generate_response(self, prompt: str) -> str:
        self.call_count += 1
        self.received_prompt = prompt
        raise LLMProviderTimeoutError


class RecordingPromptBuilder:
    """Prompt builder test double recording message and context."""

    def __init__(self, should_fail: bool = False) -> None:
        self.received_message: str | None = None
        self.received_context: Sequence[RetrievedChunk] | None = None
        self._should_fail = should_fail

    def build(
        self,
        user_message: str,
        retrieved_context: Sequence[RetrievedChunk] | None = None,
    ) -> str:
        if self._should_fail:
            raise ValueError("prompt failed")
        self.received_message = user_message
        self.received_context = retrieved_context
        return "Final RAG prompt"


class RetrievalServiceDouble:
    """Retrieval service test double."""

    def __init__(
        self,
        result: RetrievalResult | None = None,
        error: Exception | None = None,
        diagnostics: dict[str, object] | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.received_question: str | None = None
        self.last_diagnostics = diagnostics or {}

    async def retrieve(self, question: str) -> RetrievalResult:
        self.received_question = question
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def create_retrieval_result(
    chunks: list[RetrievedChunk],
) -> RetrievalResult:
    """Create a valid retrieval result fixture."""
    return RetrievalResult(
        chunks=chunks,
        total_results=len(chunks),
        top_k=5,
        duration_seconds=0.1,
    )


def create_retrieved_chunk(
    *,
    similarity_score: float = 0.9,
    document_name: str = "oop.md",
    relative_path: str = "python/oop.md",
    section_title: str = "Classes",
    chunk_index: int = 0,
    language: str = "en",
    chunk_text: str = "Classes define object behavior.",
    source_type: str = "knowledge_document",
    definition_evidence: bool = False,
    concept_evidence_level: str = "insufficient",
) -> RetrievedChunk:
    """Create one retrieved knowledge chunk."""
    return RetrievedChunk(
        chunk_text=chunk_text,
        similarity_score=similarity_score,
        document_name=document_name,
        relative_path=relative_path,
        section_title=section_title,
        chunk_index=chunk_index,
        language=language,
        source_type=source_type,
        definition_evidence=definition_evidence,
        concept_evidence_level=concept_evidence_level,
    )


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify RAG orchestration without external providers."""

    async def test_out_of_domain_questions_return_no_answer_without_llm(self) -> None:
        questions = (
            "hamburger faydalı mı",
            "yarın hava nasıl",
            "matematik sınavına nasıl çalışılır",
            "futbol maçı kaç kaç bitti",
            "bana yemek tarifi ver",
        )
        for question in questions:
            with self.subTest(question=question):
                provider = RecordingProvider()
                chunk = create_retrieved_chunk(
                    similarity_score=0.82,
                    document_name="ssl-vpn-ayarlari.md",
                    relative_path="guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
                    section_title="Menü yolu",
                    chunk_text="- `VPN Yönetimi > SSL VPN Ayarları`",
                )
                service = ChatService(
                    provider=provider,
                    prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
                    retrieval_service=RetrievalServiceDouble(
                        result=create_retrieval_result([chunk]),
                        diagnostics={"guide_confidence": 0.4},
                    ),
                    domain_gate_enabled=True,
                )

                response = await service.generate_response(question)

                self.assertEqual(response.response, NO_RELEVANT_CONTEXT_RESPONSE)
                self.assertEqual(response.sources, [])
                self.assertEqual(provider.call_count, 0)
                self.assertFalse(service.last_diagnostics["domain_relevant"])
                self.assertFalse(service.last_diagnostics["ollama_called"])

    async def test_known_concept_without_definition_returns_focused_limitation(self) -> None:
        chunk = create_retrieved_chunk(
            chunk_text="SD-WAN cihazları merkezi olarak yönetilir.",
            document_name="sdwan.docx", relative_path="sdwan.docx",
            section_title="Merkezi Yönetim", source_type="product_document",
            definition_evidence=False,
        )
        retrieval = RetrievalServiceDouble(
            create_retrieval_result([chunk]),
            diagnostics={
                "concept_match": True, "concept_term": "wan",
                "acronym_signal": True, "concept_definition_available": False,
            },
        )
        provider = RecordingProvider()
        service = ChatService(
            provider, RecordingPromptBuilder(), retrieval,
            domain_gate_enabled=True,
        )

        response = await service.generate_response("WAN nedir?")

        self.assertEqual(response.response, INSUFFICIENT_CONCEPT_DEFINITION_RESPONSE)
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(provider.call_count, 0)
        self.assertEqual(service.last_diagnostics["answer_mode"], "no_answer")
        self.assertTrue(service.last_diagnostics["domain_relevant"])
        self.assertEqual(
            service.last_diagnostics["detected_intent"], "concept_definition"
        )

    async def test_known_concept_definition_uses_exact_definition_evidence(self) -> None:
        chunk = create_retrieved_chunk(
            chunk_text="IPS, saldırı tespit ve önleme sistemidir.",
            document_name="antikor.docx", relative_path="antikor.docx",
            section_title="IDS/IPS: Tanım", source_type="product_document",
            definition_evidence=True,
        )
        retrieval = RetrievalServiceDouble(
            create_retrieval_result([chunk]),
            diagnostics={
                "concept_match": True, "concept_term": "ips",
                "acronym_signal": True, "concept_definition_available": True,
            },
        )
        provider = RecordingProvider(
            "IPS, saldırı tespit ve önleme sistemidir."
        )
        service = ChatService(
            provider, RecordingPromptBuilder(), retrieval,
            domain_gate_enabled=True,
        )

        response = await service.generate_response("IPS nedir?")

        self.assertEqual(
            response.response, "IPS, saldırı tespit ve önleme sistemidir."
        )
        self.assertEqual(response.sources[0].relative_path, "antikor.docx")
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(service.last_diagnostics["answer_mode"], "llm")
        self.assertTrue(service.last_diagnostics["concept_signal"])

    async def test_synthesis_sufficient_concept_calls_llm(self) -> None:
        path = "guides/antikor_v2/ag_yapilandirmasi/vlan-yapilandirmasi.md"
        chunks = [
            create_retrieved_chunk(
                chunk_text="VLAN yapılandırması ağ bölümlerini yönetir.",
                document_name="vlan-yapilandirmasi.md", relative_path=path,
                section_title="Kapsam", concept_evidence_level="synthesis_sufficient",
            ),
            create_retrieved_chunk(
                chunk_text="- `Etiket`: VLAN etiketi.\n- `Arayüz`: İlgili arayüz.",
                document_name="vlan-yapilandirmasi.md", relative_path=path,
                section_title="Alanlar", chunk_index=1,
                concept_evidence_level="synthesis_sufficient",
            ),
        ]
        retrieval = RetrievalServiceDouble(
            create_retrieval_result(chunks),
            diagnostics={
                "concept_match": True, "concept_term": "vlan",
                "acronym_signal": True,
                "concept_definition_available": False,
                "concept_evidence_level": "synthesis_sufficient",
                "concept_evidence_types": ["purpose_scope", "fields"],
            },
        )
        provider = RecordingProvider(
            "VLAN, Antikor üzerinde ağ bölümlerini etiket ve arayüz alanlarıyla yönetmek için kullanılan bir yapılandırmadır."
        )
        service = ChatService(
            provider, RecordingPromptBuilder(), retrieval,
            domain_gate_enabled=True,
        )

        response = await service.generate_response("VLAN nedir?")

        self.assertEqual(provider.call_count, 1)
        self.assertEqual(service.last_diagnostics["answer_mode"], "llm")
        self.assertEqual(
            service.last_diagnostics["concept_evidence_level"],
            "synthesis_sufficient",
        )
        self.assertNotEqual(
            response.response, INSUFFICIENT_CONCEPT_DEFINITION_RESPONSE
        )
        self.assertTrue(all(source.relative_path == path for source in response.sources))

    async def test_parenthetical_acronym_definition_is_focused(self) -> None:
        chunk = create_retrieved_chunk(
            chunk_text=(
                "Site-to-Site VPN, farklı şubeleri geniş alan ağları (WAN) "
                "üzerinden bağlamak için kullanılır."
            ),
            document_name="vpn.md", relative_path="vpn.md",
            section_title="Kapsam", definition_evidence=True,
        )
        retrieval = RetrievalServiceDouble(
            create_retrieval_result([chunk]),
            diagnostics={
                "concept_match": True, "concept_term": "wan",
                "acronym_signal": True, "concept_definition_available": True,
            },
        )
        provider = RecordingProvider(
            "WAN, geniş alan ağları anlamında kullanılır."
        )
        service = ChatService(
            provider, RecordingPromptBuilder(), retrieval,
            domain_gate_enabled=True,
        )

        response = await service.generate_response("WAN nedir?")

        self.assertEqual(
            response.response, "WAN, geniş alan ağları anlamında kullanılır."
        )
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(service.last_diagnostics["answer_mode"], "llm")
        self.assertEqual(response.sources[0].relative_path, "vpn.md")

    async def test_in_domain_and_borderline_questions_are_not_rejected(self) -> None:
        cases = (
            ("Dinamik NAT nasıl oluşturulur?", "dinamik-nat.md", "Kullanım adımları", "1. `+ Ekle` butonuna tıklayın."),
            ("SSL VPN ayarları hangi menü altında?", "ssl-vpn-ayarlari.md", "Menü yolu", "- `VPN Yönetimi > SSL VPN Ayarları`"),
            ("Yeni kullanıcı nasıl eklenir?", "yonetim-paneli-kullanicilari.md", "Kullanım adımları", "1. `+ Ekle` ile kullanıcı eklenir."),
            ("Kaynak Adres ne işe yarar?", "guvenlik-kurallari.md", "Alanlar", "- `Kaynak Adres`: Trafik kaynağı."),
            ("Rapor Ayarları ekranındaki alanlar", "rapor-ayarlari.md", "Alanlar", "- `Saklama Süresi`: Rapor ayarı."),
            ("erişim ayarları", "erisim-oturum-ayarlari.md", "Kapsam", "Erişim ayarları açıklanır."),
            ("bağlantıları nasıl izlerim", "baglanti-durumlari.md", "Kapsam", "Bağlantıları izlemek için kullanılır."),
            ("güvenlik profili nasıl eklenir", "ips-profilleri.md", "Kullanım adımları", "1. `+ Ekle` ile güvenlik profili eklenir."),
        )
        for question, document, section, text in cases:
            with self.subTest(question=question):
                provider = RecordingProvider()
                path = f"guides/antikor_v2/test/{document}"
                chunk = create_retrieved_chunk(
                    similarity_score=0.9, document_name=document,
                    relative_path=path, section_title=section,
                    chunk_text=text,
                )
                service = ChatService(
                    provider=provider,
                    prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
                    retrieval_service=RetrievalServiceDouble(
                        result=create_retrieval_result([chunk]),
                        diagnostics={
                            "guide_entity_match": True,
                            "guide_confidence": 1.0,
                        },
                    ),
                    domain_gate_enabled=True,
                )

                response = await service.generate_response(question)

                self.assertTrue(service.last_diagnostics["domain_relevant"])
                self.assertNotEqual(response.response, NO_RELEVANT_CONTEXT_RESPONSE)
                self.assertEqual(response.sources[0].relative_path, path)

    async def test_greeting_returns_friendly_response_without_retrieval(
        self,
    ) -> None:
        provider = RecordingProvider()
        retrieval_service = RetrievalServiceDouble()
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=retrieval_service,
        )

        response = await service.generate_response("merhaba")

        self.assertEqual(response.response, GREETING_RESPONSE)
        self.assertEqual(response.sources, [])
        self.assertIsNone(retrieval_service.received_question)
        self.assertIsNone(provider.received_prompt)

    async def test_retrieves_context_builds_prompt_and_calls_llm(self) -> None:
        provider = RecordingProvider()
        prompt_builder = RecordingPromptBuilder()
        chunk = create_retrieved_chunk()
        retrieval_service = RetrievalServiceDouble(
            result=create_retrieval_result([chunk])
        )
        service = ChatService(
            provider=provider,
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=retrieval_service,
        )

        response = await service.generate_response("Explain classes.")

        self.assertEqual(response.response, "Generated response")
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(
            response.sources[0].model_dump(),
            {
                "document_name": "oop.md",
                "relative_path": "python/oop.md",
                "section_title": "Classes",
                "chunk_index": 0,
                "similarity_score": 0.9,
                "language": "en",
            },
        )
        self.assertEqual(
            retrieval_service.received_question,
            "Explain classes.",
        )
        self.assertEqual(prompt_builder.received_message, "Explain classes.")
        self.assertEqual(prompt_builder.received_context, [chunk])
        self.assertEqual(provider.received_prompt, "Final RAG prompt")

    async def test_field_listing_uses_evidence_fast_path(self) -> None:
        provider = RecordingProvider()
        chunk = create_retrieved_chunk(
            document_name="web-sunucu-guvenligi.md",
            relative_path=(
                "guides/antikor_v2/guvenlik_ayarlari/"
                "web-sunucu-guvenligi.md"
            ),
            section_title="Alanlar",
            chunk_text=(
                "## Alanlar\n"
                "- `İstek Gövdesi Boyut Limiti`: Değer.\n"
                "- `Ek Dosyasız İstek Gövdesi Limiti`: Değer.\n"
                "- `Yanıt Gövdesi Boyut Limiti`: Değer."
            ),
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([chunk])
            ),
        )

        response = await service.generate_response(
            "Web Sunucu Güvenliği ekranında hangi alanlar bulunur?"
        )

        self.assertEqual(provider.call_count, 1)
        self.assertEqual(
            service.last_diagnostics["answer_mode"],
            "deterministic_post_validation_fallback",
        )
        self.assertTrue(service.last_diagnostics["ollama_called"])
        for label in (
            "İstek Gövdesi Boyut Limiti",
            "Ek Dosyasız İstek Gövdesi Limiti",
            "Yanıt Gövdesi Boyut Limiti",
        ):
            self.assertIn(label, response.response)
        self.assertEqual(response.sources[0].relative_path, chunk.relative_path)
        self.assertEqual(response.sources[0].section_title, "Alanlar")
        self.assertEqual(set(response.model_dump()), {"response", "sources"})

    async def test_navigation_uses_evidence_fast_path(self) -> None:
        provider = RecordingProvider()
        title_chunk = create_retrieved_chunk(
            document_name="ssl-vpn-ayarlari.md",
            relative_path="guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
            section_title="SSL VPN Ayarları",
            chunk_text="# SSL VPN Ayarları",
        )
        menu_chunk = create_retrieved_chunk(
            similarity_score=0.89,
            document_name="ssl-vpn-ayarlari.md",
            relative_path="guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
            section_title="Menü yolu",
            chunk_index=1,
            chunk_text="- `VPN Yönetimi > SSL VPN Ayarları`",
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([title_chunk, menu_chunk])
            ),
        )

        response = await service.generate_response(
            "SSL VPN ayarları hangi menü altında?"
        )

        self.assertEqual(response.response, "VPN Yönetimi > SSL VPN Ayarları")
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(
            service.last_diagnostics["answer_mode"],
            "deterministic_post_validation_fallback",
        )
        self.assertEqual(response.sources[0].section_title, "Menü yolu")

    async def test_first_action_uses_evidence_fast_path(self) -> None:
        provider = RecordingProvider()
        chunk = create_retrieved_chunk(
            document_name="dinamik-nat.md",
            relative_path="guides/antikor_v2/nat/dinamik-nat.md",
            section_title="Görünür kontroller",
            chunk_text="- `+ Ekle`: Yeni kayıt oluşturur.",
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([chunk])
            ),
        )

        response = await service.generate_response(
            "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?"
        )

        self.assertEqual(response.response, "+ Ekle")
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(
            service.last_diagnostics["answer_mode"],
            "deterministic_post_validation_fallback",
        )
        self.assertEqual(response.sources[0].section_title, "Görünür kontroller")

    async def test_procedure_and_comparison_still_call_llm(self) -> None:
        for question, section in (
            ("Dinamik NAT nasıl oluşturulur?", "Kullanım adımları"),
            ("IPSec VPN ile SSL VPN arasındaki fark nedir?", "Kapsam"),
        ):
            provider = RecordingProvider()
            chunk = create_retrieved_chunk(
                document_name="guide.md",
                relative_path="guides/guide.md",
                section_title=section,
                chunk_text="Desteklenen kaynak bilgisi.",
            )
            service = ChatService(
                provider=provider,
                prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
                retrieval_service=RetrievalServiceDouble(
                    result=create_retrieval_result([chunk])
                ),
            )
            await service.generate_response(question)
            self.assertEqual(provider.call_count, 1)
            self.assertTrue(service.last_diagnostics["ollama_called"])

    async def test_ollama_timeout_uses_post_validation_fallback(self) -> None:
        provider = TimeoutProvider()
        chunk = create_retrieved_chunk(
            document_name="ssl-vpn-ayarlari.md",
            relative_path="guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
            section_title="Menü yolu",
            chunk_text="- `VPN Yönetimi > SSL VPN Ayarları`",
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([chunk])
            ),
        )

        response = await service.generate_response(
            "SSL VPN ayarları hangi menü altında?"
        )

        self.assertEqual(provider.call_count, 1)
        self.assertTrue(service.last_diagnostics["ollama_called"])
        self.assertEqual(
            service.last_diagnostics["answer_mode"],
            "deterministic_post_validation_fallback",
        )
        self.assertEqual(response.response, "VPN Yönetimi > SSL VPN Ayarları")
        self.assertEqual(response.sources[0].relative_path, chunk.relative_path)

    async def test_mixed_guide_structured_question_does_not_fast_path(self) -> None:
        provider = RecordingProvider()
        first = create_retrieved_chunk(
            document_name="first.md", relative_path="guides/first.md",
            section_title="Alanlar", chunk_text="- `Birinci Alan`: Değer.",
        )
        second = create_retrieved_chunk(
            similarity_score=0.89, document_name="second.md",
            relative_path="guides/second.md", section_title="Alanlar",
            chunk_text="- `İkinci Alan`: Değer.",
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([first, second])
            ),
        )

        await service.generate_response("Hangi alanlar bulunur?")

        self.assertEqual(provider.call_count, 1)
        self.assertNotEqual(service.last_diagnostics["answer_mode"], "no_answer")

    async def test_returns_safe_answer_for_empty_retrieval(self) -> None:
        provider = RecordingProvider()
        retrieval_service = RetrievalServiceDouble(
            result=create_retrieval_result([])
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=retrieval_service,
        )

        response = await service.generate_response("Unknown topic")

        self.assertEqual(response.response, NO_RELEVANT_CONTEXT_RESPONSE)
        self.assertEqual(response.sources, [])
        self.assertIsNone(provider.received_prompt)

    async def test_trusts_final_context_selected_by_retrieval_service(self) -> None:
        provider = RecordingProvider()
        prompt_builder = RecordingPromptBuilder()
        low_similarity_chunk = create_retrieved_chunk(similarity_score=0.5)
        service = ChatService(
            provider=provider,
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([low_similarity_chunk])
            ),
            retrieval_min_similarity=0.65,
        )

        response = await service.generate_response("Unrelated question")

        self.assertEqual(response.response, "Generated response")
        self.assertEqual(response.sources[0].relative_path, "python/oop.md")
        self.assertEqual(prompt_builder.received_context, [low_similarity_chunk])

    async def test_uses_only_chunks_meeting_similarity_threshold(self) -> None:
        provider = RecordingProvider()
        prompt_builder = RecordingPromptBuilder()
        low_similarity_chunk = create_retrieved_chunk(
            similarity_score=0.5,
            document_name="low.md",
            relative_path="python/low.md",
            section_title="Low",
        )
        relevant_chunk = create_retrieved_chunk(similarity_score=0.9)
        service = ChatService(
            provider=provider,
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result(
                    [relevant_chunk, low_similarity_chunk]
                )
            ),
            retrieval_min_similarity=0.65,
        )

        response = await service.generate_response("Explain classes.")

        self.assertEqual(response.response, "Generated response")
        self.assertEqual(prompt_builder.received_context, [relevant_chunk])
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(response.sources[0].relative_path, "python/oop.md")
        self.assertEqual(response.sources[0].similarity_score, 0.9)
        self.assertEqual(provider.received_prompt, "Final RAG prompt")

    async def test_focuses_exact_unavailable_procedure_on_dominant_page(self) -> None:
        provider = RecordingProvider()
        prompt_builder = RecordingPromptBuilder()
        direct = create_retrieved_chunk(
            document_name="dinamik-nat.md",
            relative_path="guides/antikor_v2/nat/dinamik-nat.md",
            section_title="Dinamik NAT",
            chunk_text="Dinamik NAT yapılandırma alanları gösterilir.",
        )
        adjacent = create_retrieved_chunk(
            similarity_score=0.88,
            document_name="sdwan.md",
            relative_path="sdwan.md",
            section_title="NAT Arkasından Çalışma",
            chunk_text="SDWAN tünelleri NAT arkasında çalışabilir.",
        )
        service = ChatService(
            provider=provider,
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([direct, adjacent])
            ),
        )

        response = await service.generate_response("Dinamik NAT nasıl oluşturulur?")

        self.assertEqual(prompt_builder.received_context, [direct])
        self.assertEqual(
            [source.relative_path for source in response.sources],
            ["guides/antikor_v2/nat/dinamik-nat.md"],
        )

    async def test_button_question_does_not_mix_cross_page_controls(self) -> None:
        prompt_builder = RecordingPromptBuilder()
        rules = create_retrieved_chunk(
            document_name="guvenlik-kurallari.md",
            relative_path="guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md",
            section_title="Güvenlik Kuralları",
            chunk_text="Güvenlik Kuralları ekranında Kaydet kontrolü görünür.",
        )
        vpn = create_retrieved_chunk(
            similarity_score=0.85,
            document_name="vpn.md",
            relative_path="guides/vpn.md",
            section_title="VPN",
            chunk_text="VPN ekranında Kaydet butonu bağlantıyı kaydeder.",
        )
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([rules, vpn])
            ),
        )

        response = await service.generate_response(
            "Güvenlik kurallarında Kaydet butonu ne zaman kullanılır?"
        )

        self.assertEqual(prompt_builder.received_context, [rules])
        self.assertEqual(len(response.sources), 1)

    async def test_sufficient_procedure_keeps_detailed_same_page_chunks(self) -> None:
        prompt_builder = RecordingPromptBuilder()
        first = create_retrieved_chunk(
            document_name="ppp.md",
            relative_path="guides/ppp.md",
            section_title="Kullanım adımları",
            chunk_text="Sanal Ethernet PPP için Ekle düğmesine tıklayın.",
        )
        second = create_retrieved_chunk(
            similarity_score=0.88,
            document_name="ppp.md",
            relative_path="guides/ppp.md",
            section_title="Alanlar",
            chunk_index=1,
            chunk_text="PPP Modem Arayüzü ve Plan alanlarını doldurun.",
        )
        unrelated = create_retrieved_chunk(
            similarity_score=0.8,
            document_name="ethernet.md",
            relative_path="guides/ethernet.md",
            section_title="Ethernet",
            chunk_text="Ethernet durumunu gösterir.",
        )
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([first, second, unrelated])
            ),
        )

        response = await service.generate_response("Sanal Ethernet PPP ayarı nasıl yapılır?")

        self.assertEqual(prompt_builder.received_context, [first, second])
        self.assertEqual(len(response.sources), 2)

    async def test_prefers_exact_document_over_adjacent_longer_title(self) -> None:
        prompt_builder = RecordingPromptBuilder()
        exact = create_retrieved_chunk(
            similarity_score=0.90,
            document_name="ssl-vpn-ayarlari.md",
            relative_path="guides/ssl-vpn-ayarlari.md",
            section_title="Kapsam",
            chunk_text="SSL VPN için WAN IP ve VPN ağı ayarları bulunur.",
        )
        adjacent = create_retrieved_chunk(
            similarity_score=0.94,
            document_name="istemcisiz-ssl-web-vpn-ayarlari.md",
            relative_path="guides/istemcisiz-ssl-web-vpn-ayarlari.md",
            section_title="Kapsam",
            chunk_text="İstemcisiz SSL Web VPN portal ayarları bulunur.",
        )
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([adjacent, exact])
            ),
        )

        response = await service.generate_response("SSL VPN ayarları nasıl yapılandırılır?")

        self.assertEqual(prompt_builder.received_context, [exact])
        self.assertEqual(response.sources[0].relative_path, exact.relative_path)

    async def test_focused_chunks_follow_source_order(self) -> None:
        prompt_builder = RecordingPromptBuilder()
        continuation = create_retrieved_chunk(
            similarity_score=0.95,
            document_name="ppp.md",
            relative_path="guides/ppp.md",
            section_title="Menü yolu",
            chunk_index=2,
            chunk_text="Devam eden işlem dizisi.",
        )
        beginning = create_retrieved_chunk(
            similarity_score=0.90,
            document_name="ppp.md",
            relative_path="guides/ppp.md",
            section_title="Menü yolu",
            chunk_index=1,
            chunk_text="Sanal Ethernet PPP başlangıç işlemi.",
        )
        unrelated = create_retrieved_chunk(
            similarity_score=0.85,
            document_name="nat.md",
            relative_path="guides/nat.md",
            section_title="NAT",
            chunk_text="NAT bilgisi.",
        )
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([continuation, beginning, unrelated])
            ),
        )

        response = await service.generate_response("Sanal Ethernet PPP nasıl yapılır?")

        self.assertEqual(prompt_builder.received_context, [beginning, continuation])
        self.assertEqual([item.chunk_index for item in response.sources], [1, 2])

    async def test_returns_safe_answer_for_empty_collection(self) -> None:
        provider = RecordingProvider()
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                error=EmptyCollectionError()
            ),
        )

        response = await service.generate_response("Unknown topic")

        self.assertEqual(response.response, NO_RELEVANT_CONTEXT_RESPONSE)
        self.assertEqual(response.sources, [])
        self.assertIsNone(provider.received_prompt)

    async def test_removes_duplicate_citations_in_retrieval_order(self) -> None:
        provider = RecordingProvider()
        first_chunk = create_retrieved_chunk(similarity_score=0.95)
        duplicate_chunk = create_retrieved_chunk(similarity_score=0.9)
        second_source = create_retrieved_chunk(
            similarity_score=0.8,
            document_name="routing.md",
            relative_path="fastapi/routing.md",
            section_title="Route order",
            chunk_index=2,
        )
        service = ChatService(
            provider=provider,
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result(
                    [first_chunk, duplicate_chunk, second_source]
                )
            ),
        )

        response = await service.generate_response("Question")

        self.assertEqual(
            [source.relative_path for source in response.sources],
            ["python/oop.md", "fastapi/routing.md"],
        )
        self.assertEqual(response.sources[0].similarity_score, 0.95)

    async def test_wraps_retrieval_failure(self) -> None:
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=RecordingPromptBuilder(),  # type: ignore[arg-type]
            retrieval_service=RetrievalServiceDouble(
                error=RetrievalSearchError()
            ),
        )

        with self.assertRaises(ChatRetrievalError):
            await service.generate_response("Question")

    async def test_wraps_prompt_building_failure(self) -> None:
        service = ChatService(
            provider=RecordingProvider(),
            prompt_builder=RecordingPromptBuilder(  # type: ignore[arg-type]
                should_fail=True
            ),
            retrieval_service=RetrievalServiceDouble(
                result=create_retrieval_result([create_retrieved_chunk()])
            ),
        )

        with self.assertRaises(ChatPromptError):
            await service.generate_response("Question")


if __name__ == "__main__":
    unittest.main()
