"""Tests for retrieval-augmented chat orchestration."""

import unittest
from collections.abc import Sequence

from app.providers.base import LLMProvider
from app.retrieval.models import RetrievalResult, RetrievedChunk
from app.retrieval.retriever import (
    EmptyCollectionError,
    RetrievalSearchError,
)
from app.services.chat_service import (
    NO_RELEVANT_CONTEXT_RESPONSE,
    ChatPromptError,
    ChatRetrievalError,
    ChatService,
)


class RecordingProvider(LLMProvider):
    """LLM provider test double recording the final prompt."""

    def __init__(self) -> None:
        self.received_prompt: str | None = None

    async def generate_response(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "Generated response"

    async def health_check(self) -> bool:
        return True


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
    ) -> None:
        self.result = result
        self.error = error
        self.received_question: str | None = None

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


def create_retrieved_chunk() -> RetrievedChunk:
    """Create one retrieved knowledge chunk."""
    return RetrievedChunk(
        chunk_text="Classes define object behavior.",
        similarity_score=0.9,
        document_name="oop.md",
        relative_path="python/oop.md",
        section_title="Classes",
        chunk_index=0,
        language="en",
    )


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify RAG orchestration without external providers."""

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

        self.assertEqual(response, "Generated response")
        self.assertEqual(
            retrieval_service.received_question,
            "Explain classes.",
        )
        self.assertEqual(prompt_builder.received_message, "Explain classes.")
        self.assertEqual(prompt_builder.received_context, [chunk])
        self.assertEqual(provider.received_prompt, "Final RAG prompt")

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

        self.assertEqual(response, NO_RELEVANT_CONTEXT_RESPONSE)
        self.assertIsNone(provider.received_prompt)

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

        self.assertEqual(response, NO_RELEVANT_CONTEXT_RESPONSE)
        self.assertIsNone(provider.received_prompt)

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
