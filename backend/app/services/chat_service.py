"""Provider-independent chat application service."""

import logging
from time import perf_counter
from typing import Protocol

from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider
from app.retrieval.models import RetrievalResult
from app.retrieval.retriever import (
    EmptyCollectionError,
    RetrievalError,
)

logger = logging.getLogger(__name__)

NO_RELEVANT_CONTEXT_RESPONSE = (
    "I could not find relevant information in the knowledge base "
    "for this question."
)


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
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._retrieval_service = retrieval_service

    async def generate_response(self, user_message: str) -> str:
        """Retrieve context, build a RAG prompt, and return the response."""
        provider_name = type(self._provider).__name__
        started_at = perf_counter()
        logger.info("Starting RAG chat flow provider=%s", provider_name)

        try:
            retrieval_result = await self._retrieval_service.retrieve(
                user_message
            )
        except EmptyCollectionError:
            logger.info("RAG retrieval returned an empty collection")
            return NO_RELEVANT_CONTEXT_RESPONSE
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
        if not retrieval_result.chunks:
            return NO_RELEVANT_CONTEXT_RESPONSE

        try:
            prompt = self._prompt_builder.build(
                user_message,
                retrieval_result.chunks,
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

        logger.info(
            "LLM response completed provider=%s duration_seconds=%.3f",
            provider_name,
            perf_counter() - started_at,
        )
        return response
