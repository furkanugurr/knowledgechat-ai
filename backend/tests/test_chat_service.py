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
    GREETING_RESPONSE,
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


def create_retrieved_chunk(
    *,
    similarity_score: float = 0.9,
    document_name: str = "oop.md",
    relative_path: str = "python/oop.md",
    section_title: str = "Classes",
    chunk_index: int = 0,
    language: str = "en",
) -> RetrievedChunk:
    """Create one retrieved knowledge chunk."""
    return RetrievedChunk(
        chunk_text="Classes define object behavior.",
        similarity_score=similarity_score,
        document_name=document_name,
        relative_path=relative_path,
        section_title=section_title,
        chunk_index=chunk_index,
        language=language,
    )


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify RAG orchestration without external providers."""

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

    async def test_filters_out_low_similarity_retrieval_results(self) -> None:
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

        self.assertEqual(response.response, NO_RELEVANT_CONTEXT_RESPONSE)
        self.assertEqual(response.sources, [])
        self.assertIsNone(provider.received_prompt)
        self.assertIsNone(prompt_builder.received_context)

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
