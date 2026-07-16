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
        document_records: dict[str, list[VectorSearchRecord]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.records = records or []
        self.document_records = document_records or {}
        self.error = error
        self.top_k: int | None = None
        self.document_top_k: int | None = None

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

    def search_document(
        self,
        query_embedding: EmbeddingVector,
        relative_path: str,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        self.document_top_k = top_k
        return self.document_records.get(relative_path, [])[:top_k]

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
            candidate_k=30,
            context_max_chunks=5,
        )

        result = await service.retrieve("How does routing work?")

        self.assertEqual(result.total_results, 1)
        self.assertEqual(result.top_k, 5)
        self.assertEqual(
            result.chunks[0].relative_path,
            "fastapi/routing.md",
        )
        self.assertIsInstance(result.model_dump_json(), str)

    async def test_candidate_pool_is_larger_than_final_context(self) -> None:
        records = [create_record(f"guide/{index}.md", 0.9 - index / 100, index) for index in range(10)]
        provider = SearchVectorStoreProvider(records=records)
        service = RetrievalService(
            embedding_service=RecordingQuestionEmbeddingService(),  # type: ignore[arg-type]
            vector_store_provider=provider,
            candidate_k=30,
            context_max_chunks=5,
        )

        result = await service.retrieve("unmatched question")

        self.assertEqual(30, provider.top_k)
        self.assertLessEqual(result.total_results, 5)

    async def test_expands_dominant_document_and_preserves_chunk_order(self) -> None:
        path = "guides/antikor_v2/nat/dinamik-nat.md"
        title = VectorSearchRecord(
            document="# Dinamik NAT", similarity_score=0.9,
            metadata={"document_name":"dinamik-nat.md","relative_path":path,"section_title":"Dinamik NAT","chunk_index":0,"language":"tr"},
        )
        steps = VectorSearchRecord(
            document="## Kullanım adımları\n+ Ekle ardından Kaydet", similarity_score=0.6,
            metadata={"document_name":"dinamik-nat.md","relative_path":path,"section_title":"Kullanım adımları","chunk_index":2,"language":"tr"},
        )
        controls = VectorSearchRecord(
            document="## Görünür kontroller\n+ Ekle\nKaydet", similarity_score=0.5,
            metadata={"document_name":"dinamik-nat.md","relative_path":path,"section_title":"Görünür kontroller","chunk_index":4,"language":"tr"},
        )
        provider = SearchVectorStoreProvider(
            records=[title], document_records={path: [controls, steps, title]}
        )
        service = RetrievalService(
            embedding_service=RecordingQuestionEmbeddingService(),  # type: ignore[arg-type]
            vector_store_provider=provider,
            candidate_k=30,
            context_max_chunks=5,
        )

        result = await service.retrieve("Dinamik NAT nasıl oluşturulur?")

        self.assertEqual([0, 2, 4], [item.chunk_index for item in result.chunks])
        context = "\n".join(item.chunk_text for item in result.chunks)
        self.assertIn("Kullanım adımları", context)
        self.assertIn("+ Ekle", context)
        self.assertIn("Kaydet", context)

    async def test_rejects_unrelated_mixed_context(self) -> None:
        provider = SearchVectorStoreProvider(
            records=[
                create_record("logs/top-target-ip.md", 0.9, 0),
                create_record("vpn/settings.md", 0.88, 0),
            ]
        )
        service = RetrievalService(
            embedding_service=RecordingQuestionEmbeddingService(),  # type: ignore[arg-type]
            vector_store_provider=provider,
            candidate_k=30,
            context_max_chunks=5,
        )

        result = await service.retrieve("Yeni güvenlik kuralında Hedef Adres alanı")

        self.assertEqual([], result.chunks)


if __name__ == "__main__":
    unittest.main()
