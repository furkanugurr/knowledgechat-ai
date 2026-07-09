"""Tests for provider-independent semantic retrieval."""

import unittest
from collections.abc import Sequence

from app.embedding.models import EmbeddedChunk, EmbeddingVector
from app.embedding.provider import EmbeddingProviderUnavailableError
from app.retrieval.retriever import (
    EmptyCollectionError,
    InvalidRetrievalResultError,
    RetrievalEmbeddingError,
    RetrievalSearchError,
    Retriever,
)
from app.services.retrieval_service import RetrievalService
from app.vectorstore.models import (
    VectorCollectionInfo,
    VectorSearchRecord,
)
from app.vectorstore.provider import (
    EmptyVectorStoreError,
    VectorSearchError,
    VectorStoreProvider,
)


class RecordingQuestionEmbeddingService:
    """Question embedding test double."""

    def __init__(self, should_fail: bool = False) -> None:
        self.question: str | None = None
        self._should_fail = should_fail

    async def embed_text(self, text: str) -> EmbeddingVector:
        self.question = text
        if self._should_fail:
            raise EmbeddingProviderUnavailableError
        return EmbeddingVector(values=[1.0, 0.0, 0.0])


class SearchVectorStoreProvider(VectorStoreProvider):
    """Vector store test double with configurable search behavior."""

    def __init__(
        self,
        records: list[VectorSearchRecord] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.records = records or []
        self.error = error
        self.top_k: int | None = None

    def create_collection(self) -> VectorCollectionInfo:
        return VectorCollectionInfo(
            collection_name="test",
            record_count=len(self.records),
        )

    def upsert_embeddings(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        return len(embedded_chunks)

    def delete_embeddings(self, relative_paths: Sequence[str]) -> int:
        return 0

    def collection_info(self) -> VectorCollectionInfo:
        return self.create_collection()

    def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        self.top_k = top_k
        if self.error is not None:
            raise self.error
        return self.records[:top_k]

    def health_check(self) -> bool:
        return True


def create_record(
    relative_path: str,
    score: float,
    chunk_index: int,
) -> VectorSearchRecord:
    """Create one complete vector search record."""
    return VectorSearchRecord(
        document=f"Content for {relative_path}",
        similarity_score=score,
        metadata={
            "document_name": relative_path.rsplit("/", 1)[-1],
            "relative_path": relative_path,
            "section_title": "Test Section",
            "chunk_index": chunk_index,
            "language": "en",
        },
    )


class RetrieverTests(unittest.IsolatedAsyncioTestCase):
    """Verify question embedding, search, ordering, and errors."""

    async def test_retrieves_top_k_chunks_in_similarity_order(self) -> None:
        embedding_service = RecordingQuestionEmbeddingService()
        provider = SearchVectorStoreProvider(
            records=[
                create_record("python/near.md", 0.75, 1),
                create_record("python/exact.md", 1.0, 0),
                create_record("python/far.md", 0.2, 2),
            ]
        )
        retriever = Retriever(embedding_service, provider)

        chunks = await retriever.retrieve(
            "What is Python?",
            top_k=2,
        )

        self.assertEqual(embedding_service.question, "What is Python?")
        self.assertEqual(provider.top_k, 2)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(
            [chunk.relative_path for chunk in chunks],
            ["python/exact.md", "python/near.md"],
        )

    async def test_handles_empty_collection(self) -> None:
        retriever = Retriever(
            RecordingQuestionEmbeddingService(),
            SearchVectorStoreProvider(error=EmptyVectorStoreError()),
        )

        with self.assertRaises(EmptyCollectionError):
            await retriever.retrieve("Question", top_k=5)

    async def test_handles_embedding_failure(self) -> None:
        retriever = Retriever(
            RecordingQuestionEmbeddingService(should_fail=True),
            SearchVectorStoreProvider(),
        )

        with self.assertRaises(RetrievalEmbeddingError):
            await retriever.retrieve("Question", top_k=5)

    async def test_handles_vector_search_failure(self) -> None:
        retriever = Retriever(
            RecordingQuestionEmbeddingService(),
            SearchVectorStoreProvider(error=VectorSearchError()),
        )

        with self.assertRaises(RetrievalSearchError):
            await retriever.retrieve("Question", top_k=5)

    async def test_handles_invalid_chunk_metadata(self) -> None:
        invalid_record = VectorSearchRecord(
            document="Content",
            similarity_score=0.5,
            metadata={"relative_path": "python/oop.md"},
        )
        retriever = Retriever(
            RecordingQuestionEmbeddingService(),
            SearchVectorStoreProvider(records=[invalid_record]),
        )

        with self.assertRaises(InvalidRetrievalResultError):
            await retriever.retrieve("Question", top_k=5)


class RetrievalServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify retrieval service orchestration and serialization."""

    async def test_returns_serializable_retrieval_result(self) -> None:
        embedding_service = RecordingQuestionEmbeddingService()
        provider = SearchVectorStoreProvider(
            records=[create_record("fastapi/routing.md", 0.9, 0)]
        )
        service = RetrievalService(
            embedding_service=embedding_service,  # type: ignore[arg-type]
            vector_store_provider=provider,
            top_k=5,
        )

        result = await service.retrieve("How does routing work?")

        self.assertEqual(result.total_results, 1)
        self.assertEqual(result.top_k, 5)
        self.assertEqual(
            result.chunks[0].relative_path,
            "fastapi/routing.md",
        )
        self.assertIsInstance(result.model_dump_json(), str)


if __name__ == "__main__":
    unittest.main()
