"""Provider-independent chat application service."""

import logging
import re
from time import perf_counter
from typing import Protocol

from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider
from app.retrieval.models import RetrievalResult, RetrievedChunk
from app.retrieval.intent import QuestionIntent
from app.retrieval.answer_grounding import GroundedAnswerGuard
from app.retrieval.domain_relevance import DomainRelevanceGate
from app.retrieval.retriever import (
    EmptyCollectionError,
    RetrievalError,
)
from app.schemas.chat import ChatResponse, CitationSource
from app.retrieval.question_plan import (
    AnswerCompletenessValidator,
    QuestionPlanner,
)

logger = logging.getLogger(__name__)

NO_RELEVANT_CONTEXT_RESPONSE = (
    "Bu soruyla ilgili bilgi mevcut bilgi tabanında bulunamadı. "
    "Lütfen Antikor ürünleri, ayarları veya kılavuzlarıyla ilgili bir soru sorun."
)
INSUFFICIENT_CONCEPT_DEFINITION_RESPONSE = (
    "Bu kavram Antikor kılavuzlarında geçiyor ancak mevcut kaynaklarda "
    "açık bir tanımı bulunmuyor."
)
GREETING_RESPONSE = (
    "Merhaba! Knowledge base içindeki belgeler hakkında soru sorabilirsin."
)
GREETING_MESSAGES = frozenset({"merhaba", "selam", "hello", "hi", "iyi günler"})


class KnowledgeRetrievalService(Protocol):
    """Minimal retrieval capability required by RAG chat."""

    async def retrieve(self, question: str) -> RetrievalResult:
        """Return relevant knowledge chunks for a question."""


class ChatServiceError(Exception):
    """Base exception for chat orchestration failures."""


class ChatRetrievalError(ChatServiceError):
    """Raised when knowledge retrieval fails."""


class ChatPromptError(ChatServiceError):
    """Raised when the final RAG prompt cannot be built."""


class ChatService:
    """Coordinate retrieval, prompt construction, and LLM generation."""

    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
        retrieval_service: KnowledgeRetrievalService,
        retrieval_min_similarity: float = 0.65,
        out_of_domain_min_similarity: float = 0.70,
        out_of_domain_min_lexical_overlap: float = 0.12,
        out_of_domain_min_guide_confidence: float = 0.50,
        domain_gate_enabled: bool = False,
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._retrieval_service = retrieval_service
        self._retrieval_min_similarity = retrieval_min_similarity
        self._answer_guard = GroundedAnswerGuard()
        self._domain_gate = DomainRelevanceGate(
            out_of_domain_min_similarity,
            out_of_domain_min_lexical_overlap,
            out_of_domain_min_guide_confidence,
        )
        self._domain_gate_enabled = domain_gate_enabled
        self._last_diagnostics: dict[str, object] = {}

    @property
    def last_diagnostics(self) -> dict[str, object]:
        """Return internal diagnostics for tests and validation tooling."""
        return dict(self._last_diagnostics)

    async def generate_response(self, user_message: str) -> ChatResponse:
        """Retrieve context, build a RAG prompt, and return the response."""
        provider_name = type(self._provider).__name__
        started_at = perf_counter()
        self._last_diagnostics = {
            "answer_mode": "llm",
            "detected_intent": None,
            "evidence_sufficient": False,
            "selected_guide": None,
            "selected_sections": [],
            "ollama_called": False,
            "domain_relevant": None,
            "no_answer_reason": None,
            "top_similarity": 0.0,
            "lexical_overlap": 0.0,
            "guide_confidence": 0.0,
            "confidence_tier": None,
            "entity_signal": False,
            "ui_label_signal": False,
            "category_signal": False,
            "lexical_signal": False,
            "semantic_signal": False,
            "guide_agreement_signal": False,
            "final_decision_reason": None,
            "resolved_guide": None,
            "dominant_path": None,
            "concept_signal": False,
            "acronym_signal": False,
            "concept_term": None,
            "concept_definition_available": False,
            "concept_evidence_level": "insufficient",
            "concept_evidence_types": [],
            "primary_entity": None,
            "requested_components": [],
            "answered_components": [],
            "missing_components": [],
            "completeness_retry_count": 0,
        }
        logger.info("Starting RAG chat flow provider=%s", provider_name)

        if self._is_greeting(user_message):
            logger.info("Greeting message handled without retrieval")
            return ChatResponse(response=GREETING_RESPONSE, sources=[])

        plan = QuestionPlanner.plan(user_message)
        try:
            retrieval_result = await self._retrieval_service.retrieve(
                user_message
            )
        except EmptyCollectionError:
            logger.info("RAG retrieval returned an empty collection")
            return self._empty_context_response()
        except RetrievalError as exc:
            logger.error(
                "RAG retrieval failed duration_seconds=%.3f",
                perf_counter() - started_at,
            )
            raise ChatRetrievalError(
                "Knowledge retrieval failed."
            ) from exc

        logger.info(
            "Retrieval completed retrieved_chunks=%d",
            retrieval_result.total_results,
        )
        relevant_chunks = (
            retrieval_result.chunks
            if plan.is_multi_part or plan.primary_intent in {
                QuestionIntent.COMPARISON,
                QuestionIntent.CONCEPT_DEFINITION,
                QuestionIntent.PRODUCT_OVERVIEW,
            }
            else self._focus_context(user_message, retrieval_result.chunks)
        )
        logger.info(
            "Final retrieval context accepted relevant_chunks=%d",
            len(relevant_chunks),
        )

        if not relevant_chunks:
            self._last_diagnostics.update({
                "answer_mode": "no_answer",
                "ollama_called": False,
                "no_answer_reason": "empty_retrieval",
            })
            return self._empty_context_response()

        retrieval_diagnostics = getattr(
            self._retrieval_service, "last_diagnostics", {}
        )
        if callable(retrieval_diagnostics):
            retrieval_diagnostics = retrieval_diagnostics()
        if isinstance(retrieval_diagnostics, dict):
            self._last_diagnostics.update({
                "retrieval_candidates": retrieval_diagnostics.get(
                    "retrieval_candidates", []
                ),
                "rejected_candidates": retrieval_diagnostics.get(
                    "rejected_candidates", []
                ),
                "final_evidence_sections": retrieval_diagnostics.get(
                    "final_evidence_sections", []
                ),
                "selected_product_categories": retrieval_diagnostics.get(
                    "selected_product_categories", []
                ),
                "requested_product_scope": retrieval_diagnostics.get(
                    "requested_product_scope"
                ),
                "selected_capability_categories": retrieval_diagnostics.get(
                    "selected_capability_categories", []
                ),
                "missing_capability_categories": retrieval_diagnostics.get(
                    "missing_capability_categories", []
                ),
                "marketing_chunk_ratio": retrieval_diagnostics.get(
                    "marketing_chunk_ratio", 0.0
                ),
                "dominant_category": retrieval_diagnostics.get("dominant_category"),
                "sub_product_ratio": retrieval_diagnostics.get("sub_product_ratio", 0.0),
                "core_overview_present": retrieval_diagnostics.get(
                    "core_overview_present", False
                ),
                "field_coverage_plan": retrieval_diagnostics.get(
                    "field_coverage_plan", {}
                ),
            })
        if self._domain_gate_enabled:
            decision = self._domain_gate.evaluate(
                user_message,
                relevant_chunks,
                retrieval_diagnostics
                if isinstance(retrieval_diagnostics, dict) else {},
            )
            self._last_diagnostics.update({
                "domain_relevant": decision.domain_relevant,
                "no_answer_reason": decision.reason,
                "top_similarity": decision.top_similarity,
                "lexical_overlap": decision.lexical_overlap,
                "guide_confidence": decision.guide_confidence,
                "confidence_tier": decision.confidence_tier,
                "entity_signal": decision.entity_signal,
                "ui_label_signal": decision.ui_label_signal,
                "category_signal": decision.category_signal,
                "lexical_signal": decision.lexical_signal,
                "semantic_signal": decision.semantic_signal,
                "guide_agreement_signal": decision.guide_agreement_signal,
                "final_decision_reason": decision.final_decision_reason,
                "resolved_guide": retrieval_diagnostics.get("resolved_guide"),
                "dominant_path": retrieval_diagnostics.get("dominant_path"),
                "concept_signal": decision.concept_signal,
                "acronym_signal": decision.acronym_signal,
                "concept_term": retrieval_diagnostics.get("concept_term"),
                "concept_definition_available": retrieval_diagnostics.get(
                    "concept_definition_available", False
                ),
                "concept_evidence_level": retrieval_diagnostics.get(
                    "concept_evidence_level", "insufficient"
                ),
                "concept_evidence_types": retrieval_diagnostics.get(
                    "concept_evidence_types", []
                ),
            })
            if not decision.domain_relevant:
                self._last_diagnostics["answer_mode"] = "no_answer"
                logger.info(
                    "Question rejected by domain gate reason=%s", decision.reason
                )
                return self._empty_context_response()

        intent = plan.primary_intent
        if (
            intent == QuestionIntent.CONCEPT_DEFINITION
            and retrieval_diagnostics.get("concept_match")
            and retrieval_diagnostics.get(
                "concept_evidence_level",
                "explicit_definition"
                if retrieval_diagnostics.get("concept_definition_available")
                else "insufficient",
            ) == "insufficient"
        ):
            self._last_diagnostics.update({
                "answer_mode": "no_answer",
                "detected_intent": intent.value,
                "selected_guide": relevant_chunks[0].relative_path,
                "selected_sections": [
                    item.section_title for item in relevant_chunks
                ],
                "evidence_sufficient": False,
            })
            return ChatResponse(
                response=INSUFFICIENT_CONCEPT_DEFINITION_RESPONSE,
                sources=self._build_sources(relevant_chunks),
            )
        navigation_hint = PromptBuilder._navigation_path_hint(relevant_chunks)
        if (
            plan.primary_entity in {"Rapor Ayarları", "SSL VPN"}
            and any(
                chunk.relative_path.replace("\\", "/").endswith(
                    "/raporlar/rapor-ayarlari.md"
                    if plan.primary_entity == "Rapor Ayarları"
                    else "/vpn/ssl-vpn-ayarlari.md"
                )
                for chunk in relevant_chunks
            )
        ):
            navigation_hint = (
                "Raporlar > Rapor Ayarları"
                if plan.primary_entity == "Rapor Ayarları"
                else "VPN > SSL VPN Ayarları"
            )
        creation_hint = PromptBuilder._creation_control_hint(relevant_chunks)
        guide_confident = self._guide_selection_is_confident(
            user_message, retrieval_result.chunks, relevant_chunks
        )
        deterministic_fallback = (
            self._answer_guard.structured_fast_path(
                user_message,
                intent,
                relevant_chunks,
                navigation_hint=navigation_hint,
                creation_hint=creation_hint,
            )
            if (
                guide_confident
                or (
                    intent == QuestionIntent.CONCEPT_DEFINITION
                    and retrieval_diagnostics.get("concept_match")
                    and retrieval_diagnostics.get(
                        "concept_evidence_level",
                        "explicit_definition"
                        if retrieval_diagnostics.get("concept_definition_available")
                        else "insufficient",
                    ) == "explicit_definition"
                )
            ) else None
        )
        self._last_diagnostics.update({
            "detected_intent": intent.value,
            "primary_entity": plan.primary_entity,
            "requested_components": [
                item.value for item in plan.requested_components
            ],
            "selected_guide": relevant_chunks[0].relative_path,
            "selected_sections": [
                item.section_title for item in relevant_chunks
            ],
            "evidence_sufficient": deterministic_fallback is not None,
        })

        try:
            prompt = self._prompt_builder.build(
                user_message,
                relevant_chunks,
            )
        except Exception as exc:
            logger.error(
                "RAG prompt building failed duration_seconds=%.3f",
                perf_counter() - started_at,
            )
            raise ChatPromptError(
                "Unable to build the RAG prompt."
            ) from exc

        logger.info("RAG prompt built")
        citation_chunks = relevant_chunks
        try:
            self._last_diagnostics["ollama_called"] = True
            raw_response = await self._provider.generate_response(prompt)
            if "procedure" in {
                item.value for item in plan.requested_components
            }:
                raw_response = self._answer_guard.normalize_ordered_procedure(
                    raw_response
                )
            answered = AnswerCompletenessValidator.answered_components(
                plan, raw_response
            )
            missing = [
                item for item in plan.requested_components if item not in answered
            ]
            if missing and plan.is_multi_part:
                correction_prompt = self._prompt_builder.build_correction(
                    user_message,
                    relevant_chunks,
                    raw_response,
                    [item.value for item in missing],
                )
                raw_response = await self._provider.generate_response(
                    correction_prompt
                )
                if "procedure" in {
                    item.value for item in plan.requested_components
                }:
                    raw_response = self._answer_guard.normalize_ordered_procedure(
                        raw_response
                    )
                self._last_diagnostics["completeness_retry_count"] = 1
            response = (
                raw_response
                if plan.is_multi_part
                else self._answer_guard.ensure_grounded(
                    user_message,
                    intent,
                    relevant_chunks,
                    raw_response,
                    navigation_hint=navigation_hint,
                    creation_hint=creation_hint,
                )
            )
            answered = AnswerCompletenessValidator.answered_components(
                plan, response
            )
            missing = [
                item for item in plan.requested_components if item not in answered
            ]
            if missing and plan.is_multi_part:
                fallback = self._answer_guard.component_aware_fallback(
                    plan, relevant_chunks
                )
                if fallback is not None:
                    response, citation_chunks = fallback
                    answered = AnswerCompletenessValidator.answered_components(
                        plan, response
                    )
                    missing = [
                        item for item in plan.requested_components
                        if item not in answered
                    ]
                    self._last_diagnostics["answer_mode"] = (
                        "component_aware_post_validation_fallback"
                    )
            if (
                "comparison" in {item.value for item in plan.requested_components}
                and self._has_unsupported_comparison_claim(response)
            ):
                fallback = self._answer_guard.component_aware_fallback(
                    plan, relevant_chunks
                )
                if fallback is not None:
                    response, citation_chunks = fallback
                    self._last_diagnostics["answer_mode"] = (
                        "component_aware_post_validation_fallback"
                    )
            self._last_diagnostics.update({
                "answered_components": [item.value for item in answered],
                "missing_components": [item.value for item in missing],
            })
            if (
                response == raw_response
                and deterministic_fallback is not None
                and intent == QuestionIntent.FIRST_ACTION
                and deterministic_fallback[0].casefold() not in response.casefold()
            ):
                response = deterministic_fallback[0]
            if (
                response != raw_response
                and self._last_diagnostics["answer_mode"]
                != "component_aware_post_validation_fallback"
            ):
                self._last_diagnostics["answer_mode"] = (
                    "deterministic_post_validation_fallback"
                )
                if deterministic_fallback is not None:
                    citation_chunks = deterministic_fallback[1]
                    self._last_diagnostics["selected_sections"] = [
                        item.section_title for item in citation_chunks
                    ]
        except Exception:
            logger.error(
                "LLM response failed provider=%s duration_seconds=%.3f",
                provider_name,
                perf_counter() - started_at,
                exc_info=True,
            )
            if deterministic_fallback is not None:
                answer, supporting_chunks = deterministic_fallback
                self._last_diagnostics.update({
                    "answer_mode": "deterministic_post_validation_fallback",
                    "selected_sections": [
                        item.section_title for item in supporting_chunks
                    ],
                })
                return ChatResponse(
                    response=answer,
                    sources=self._build_sources(supporting_chunks),
                )
            self._last_diagnostics.update({
                "answer_mode": "no_answer",
                "no_answer_reason": "llm_failure_without_safe_fallback",
            })
            return self._empty_context_response()

        logger.info("Building citations")
        sources = self._build_sources(citation_chunks)
        logger.info("Citations built citation_count=%d", len(sources))
        logger.info(
            "Chat response completed provider=%s duration_seconds=%.3f",
            provider_name,
            perf_counter() - started_at,
        )
        return ChatResponse(response=response, sources=sources)

    @staticmethod
    def _empty_context_response() -> ChatResponse:
        """Return the safe response used when no context is available."""
        return ChatResponse(
            response=NO_RELEVANT_CONTEXT_RESPONSE,
            sources=[],
        )

    @staticmethod
    def _is_greeting(user_message: str) -> bool:
        """Return whether the message is a simple greeting."""
        normalized_message = " ".join(
            user_message.casefold().strip(" \t\r\n.!?,;:").split()
        )
        return normalized_message in GREETING_MESSAGES

    def _filter_relevant_chunks(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Return chunks meeting the configured similarity threshold."""
        return [
            chunk
            for chunk in chunks
            if chunk.similarity_score >= self._retrieval_min_similarity
        ]

    @classmethod
    def _guide_selection_is_confident(
        cls,
        question: str,
        original_chunks: list[RetrievedChunk],
        selected_chunks: list[RetrievedChunk],
    ) -> bool:
        """Reject structured fast paths chosen from an ambiguous guide mix."""
        selected_paths = {item.relative_path for item in selected_chunks}
        if len(selected_paths) != 1:
            return False
        original_paths = {item.relative_path for item in original_chunks}
        if len(original_paths) == 1:
            return True
        question_tokens = cls._focus_tokens(question)
        document_tokens = cls._focus_tokens(selected_chunks[0].document_name)
        return bool(question_tokens & document_tokens)

    @classmethod
    def _focus_context(
        cls,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Prefer the single document most directly matching the question."""
        if len(chunks) < 2:
            return chunks
        question_tokens = cls._focus_tokens(question)
        if not question_tokens:
            return chunks
        scores: dict[str, float] = {}
        procedural_question = any(
            marker in question.casefold()
            for marker in (
                "nasıl", "oluştur", "ekle", "yapılandır", "tanımla",
                "ne zaman", "nereden", "ayar",
            )
        )
        for chunk in chunks:
            searchable = " ".join(
                (
                    chunk.document_name,
                    chunk.relative_path,
                    chunk.section_title or "",
                    chunk.chunk_text,
                )
            )
            context_tokens = cls._focus_tokens(searchable)
            overlap = sum(
                any(cls._tokens_match(token, candidate) for candidate in context_tokens)
                for token in question_tokens
            ) / len(question_tokens)
            document_tokens = cls._focus_tokens(
                chunk.document_name
            )
            document_overlap = sum(
                any(cls._tokens_match(token, candidate) for candidate in document_tokens)
                for token in question_tokens
            ) / len(question_tokens)
            unmatched_document_tokens = sum(
                not any(cls._tokens_match(token, candidate) for candidate in question_tokens)
                for token in document_tokens
            )
            section = (chunk.section_title or "").casefold()
            section_bonus = (
                0.2
                if procedural_question
                and any(
                    value in section
                    for value in ("kullanım adımları", "menü yolu", "alanlar")
                )
                else 0.0
            )
            score = (
                overlap
                + (0.3 * document_overlap)
                + section_bonus
                + (0.1 * chunk.similarity_score)
                - (0.12 * unmatched_document_tokens)
            )
            scores[chunk.relative_path] = max(
                scores.get(chunk.relative_path, 0.0),
                score,
            )
        best_path, best_score = max(scores.items(), key=lambda item: item[1])
        relevance_score = best_score - (
            0.1
            * max(
                chunk.similarity_score
                for chunk in chunks
                if chunk.relative_path == best_path
            )
        )
        if relevance_score < 0.2:
            return chunks
        return sorted(
            (chunk for chunk in chunks if chunk.relative_path == best_path),
            key=lambda chunk: chunk.chunk_index,
        )

    @staticmethod
    def _focus_tokens(value: str) -> set[str]:
        stopwords = {
            "aciklar", "alan", "bilgi", "butonu", "icin", "kullanilir",
            "nasil", "nerede", "nedir", "zaman", "veya", "hangi",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9çğıöşü]+", value.casefold())
            if len(token) >= 3 and token not in stopwords
        }

    @staticmethod
    def _has_unsupported_comparison_claim(answer: str) -> bool:
        folded = answer.casefold()
        return any(term in folded for term in (
            "daha güvenli", "daha güvenilir", "daha iyi", "ideal", "üstün",
        ))

    @staticmethod
    def _tokens_match(first: str, second: str) -> bool:
        if first == second:
            return True
        return len(first) >= 5 and len(second) >= 5 and first[:5] == second[:5]

    @staticmethod
    def _build_sources(
        chunks: list[RetrievedChunk],
    ) -> list[CitationSource]:
        """Build ordered citations, removing duplicate chunk references."""
        sources: list[CitationSource] = []
        seen: set[tuple[str, str | None, int]] = set()

        for chunk in chunks:
            citation_key = (
                chunk.relative_path,
                chunk.section_title,
                chunk.chunk_index,
            )
            if citation_key in seen:
                continue

            seen.add(citation_key)
            sources.append(
                CitationSource(
                    document_name=chunk.document_name,
                    relative_path=chunk.relative_path,
                    section_title=chunk.section_title,
                    chunk_index=chunk.chunk_index,
                    similarity_score=chunk.similarity_score,
                    language=chunk.language,
                )
            )

        return sources
