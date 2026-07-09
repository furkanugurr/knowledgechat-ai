"""Tests for provider-independent vector persistence orchestration."""

import unittest
from collections.abc import Sequence

from app.embedding.models import (
    EmbeddedChunk,
    EmbeddingResult,
    EmbeddingVector,
)
from app.knowledge.models import IndexResult, IndexStatistics
from app.services.vector_store_service import VectorStoreService
from app.vectorstore.models import (
    VectorCollectionInfo,
    VectorSearchRecord,
)
from app.vectorstore.provider import VectorStoreProvider
from test_chroma_vector_store import create_embedded_chunk


class RecordingVectorStoreProvider(VectorStoreProvider):
    """Vector store test double recording service operation order."""

    def __init__(self) -> None:
        self.operations: list[str] = []
        self.record_count = 1

    def create_collection(self) -> VectorCollectionInfo:
        self.operations.append("create")
        return VectorCollectionInfo(
            collection_name="test-collection",
            record_count=self.record_count,
        )

    def upsert_embeddings(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        self.operations.append("upsert")
        self.record_count += len(embedded_chunks)
        return len(embedded_chunks)

    def delete_embeddings(self, relative_paths: Sequence[str]) -> int:
        self.operations.append("delete")
        deleted = len(relative_paths)
        self.record_count = max(self.record_count - deleted, 0)
        return deleted

    def collection_info(self) -> VectorCollectionInfo:
        self.operations.append("info")
        return VectorCollectionInfo(
            collection_name="test-collection",
            record_count=self.record_count,
        )

    def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        return []

    def health_check(self) -> bool:
        return True


class VectorStoreServiceTests(unittest.TestCase):
    """Verify embedding upserts and index removals are coordinated."""

    def test_stores_embeddings_and_applies_removed_documents(self) -> None:
        embedded_chunk = create_embedded_chunk(
            "python/oop.md",
            "Object-oriented programming.",
        )
        embedding_result = EmbeddingResult(
            embedded_chunks=[embedded_chunk],
            total_chunks=1,
            dimensions=3,
            duration_seconds=0.1,
        )
        index_result = IndexResult(
            manifest_version=1,
            indexed_files=[],
            removed_files=["git/removed.md"],
            chunks=[embedded_chunk.chunk],
            statistics=IndexStatistics(
                files_scanned=1,
                files_indexed=1,
                files_skipped=0,
                files_removed=1,
                chunks_created=1,
                duration_seconds=0.1,
            ),
        )
        provider = RecordingVectorStoreProvider()

        result = VectorStoreService(provider).store(
            embedding_result,
            index_result,
        )

        self.assertEqual(
            provider.operations,
            ["create", "delete", "upsert", "info"],
        )
        self.assertEqual(result.collection_name, "test-collection")
        self.assertEqual(result.vectors_deleted, 1)
        self.assertEqual(result.vectors_upserted, 1)
        self.assertEqual(result.total_vectors, 1)
        self.assertIsInstance(result.model_dump_json(), str)


if __name__ == "__main__":
    unittest.main()
