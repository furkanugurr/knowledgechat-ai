"""Provider-independent chat application service."""

import logging
import re
from time import perf_counter
from typing import Protocol

from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider
from app.retrieval.models import RetrievalResult, RetrievedChunk
from app.retrieval.retriever import (
    EmptyCollectionError,
    RetrievalError,
)
from app.schemas.chat import ChatResponse, CitationSource

logger = logging.getLogger(__name__)

NO_RELEVANT_CONTEXT_RESPONSE = (
    "Bu soruyla ilgili bilgi tabanında yeterince ilgili bilgi bulamadım."
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
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._retrieval_service = retrieval_service
        self._retrieval_min_similarity = retrieval_min_similarity

    async def generate_response(self, user_message: str) -> ChatResponse:
        """Retrieve context, build a RAG prompt, and return the response."""
        provider_name = type(self._provider).__name__
        started_at = perf_counter()
        logger.info("Starting RAG chat flow provider=%s", provider_name)

        if self._is_greeting(user_message):
            logger.info("Greeting message handled without retrieval")
            return ChatResponse(response=GREETING_RESPONSE, sources=[])

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
        relevant_chunks = self._filter_relevant_chunks(
            retrieval_result.chunks
        )
        relevant_chunks = self._focus_context(user_message, relevant_chunks)
        logger.info(
            "Retrieval relevance filter applied min_similarity=%.3f "
            "relevant_chunks=%d",
            self._retrieval_min_similarity,
            len(relevant_chunks),
        )

        if not relevant_chunks:
            return self._empty_context_response()

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
        try:
            response = await self._provider.generate_response(prompt)
        except Exception:
            logger.error(
                "LLM response failed provider=%s duration_seconds=%.3f",
                provider_name,
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        logger.info("Building citations")
        sources = self._build_sources(relevant_chunks)
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
