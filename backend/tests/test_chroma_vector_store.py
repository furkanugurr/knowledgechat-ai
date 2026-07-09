"""Tests for persistent ChromaDB vector storage."""

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb

from app.embedding.models import EmbeddedChunk, EmbeddingVector
from app.knowledge.models import KnowledgeChunk, KnowledgeMetadata
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider
from app.vectorstore.provider import (
    CollectionCreationError,
    VectorDeleteError,
    VectorStoreProvider,
    VectorStoreUnavailableError,
    VectorUpsertError,
)


def create_embedded_chunk(
    relative_path: str,
    content: str,
    chunk_index: int = 0,
    total_chunks: int = 1,
    values: list[float] | None = None,
) -> EmbeddedChunk:
    """Create an embedded knowledge chunk fixture."""
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return EmbeddedChunk(
        chunk=KnowledgeChunk(
            content=content,
            metadata=KnowledgeMetadata(
                document_name=Path(relative_path).name,
                relative_path=relative_path,
                section_title="Test Section",
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                language="en",
                created_at=timestamp,
                updated_at=timestamp,
            ),
        ),
        embedding=EmbeddingVector(values=values or [0.1, 0.2, 0.3]),
    )


class ChromaVectorStoreTests(unittest.TestCase):
    """Verify real local Chroma collection operations and persistence."""

    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.persistence_path = Path(self._temporary_directory.name) / "chroma"
        self.collection_name = "knowledgechat-tests"

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def create_provider(self) -> ChromaVectorStoreProvider:
        """Create a provider using an isolated persistent directory."""
        return ChromaVectorStoreProvider(
            persistence_path=self.persistence_path,
            collection_name=self.collection_name,
        )

    def test_initializes_provider_and_creates_collection(self) -> None:
        provider = self.create_provider()

        info = provider.create_collection()

        self.assertIsInstance(provider, VectorStoreProvider)
        self.assertEqual(info.collection_name, self.collection_name)
        self.assertEqual(info.record_count, 0)
        self.assertTrue(provider.health_check())
        self.assertTrue(self.persistence_path.exists())

    def test_upserts_document_embedding_and_metadata(self) -> None:
        provider = self.create_provider()
        embedded_chunk = create_embedded_chunk(
            "python/oop.md",
            "Object-oriented programming.",
        )

        upserted = provider.upsert_embeddings([embedded_chunk])
        collection = chromadb.PersistentClient(
            path=str(self.persistence_path)
        ).get_collection(
            name=self.collection_name,
            embedding_function=None,
        )
        stored = collection.get(
            include=["documents", "metadatas", "embeddings"]
        )

        self.assertEqual(upserted, 1)
        self.assertEqual(collection.count(), 1)
        self.assertEqual(
            stored["documents"],
            ["Object-oriented programming."],
        )
        self.assertEqual(
            stored["metadatas"][0],
            {
                "document_name": "oop.md",
                "relative_path": "python/oop.md",
                "section_title": "Test Section",
                "chunk_index": 0,
                "language": "en",
            },
        )
        self.assertEqual(len(stored["embeddings"][0]), 3)

    def test_duplicate_upsert_updates_without_duplication(self) -> None:
        provider = self.create_provider()
        provider.upsert_embeddings(
            [create_embedded_chunk("python/oop.md", "Original")]
        )

        provider.upsert_embeddings(
            [
                create_embedded_chunk(
                    "python/oop.md",
                    "Updated",
                    values=[0.4, 0.5, 0.6],
                )
            ]
        )

        self.assertEqual(provider.collection_info().record_count, 1)
        collection = chromadb.PersistentClient(
            path=str(self.persistence_path)
        ).get_collection(
            name=self.collection_name,
            embedding_function=None,
        )
        self.assertEqual(
            collection.get(include=["documents"])["documents"],
            ["Updated"],
        )

    def test_upsert_removes_stale_chunks_for_changed_document(self) -> None:
        provider = self.create_provider()
        provider.upsert_embeddings(
            [
                create_embedded_chunk(
                    "python/oop.md",
                    "First",
                    chunk_index=0,
                    total_chunks=2,
                ),
                create_embedded_chunk(
                    "python/oop.md",
                    "Second",
                    chunk_index=1,
                    total_chunks=2,
                ),
            ]
        )

        provider.upsert_embeddings(
            [
                create_embedded_chunk(
                    "python/oop.md",
                    "Combined",
                    chunk_index=0,
                    total_chunks=1,
                )
            ]
        )

        self.assertEqual(provider.collection_info().record_count, 1)

    def test_deletes_all_vectors_for_removed_document(self) -> None:
        provider = self.create_provider()
        provider.upsert_embeddings(
            [
                create_embedded_chunk("python/oop.md", "OOP"),
                create_embedded_chunk("git/commits.md", "Commits"),
            ]
        )

        deleted = provider.delete_embeddings(["python/oop.md"])

        self.assertEqual(deleted, 1)
        self.assertEqual(provider.collection_info().record_count, 1)

    def test_vectors_persist_across_provider_restart(self) -> None:
        first_provider = self.create_provider()
        first_provider.upsert_embeddings(
            [create_embedded_chunk("python/oop.md", "Persistent")]
        )

        restarted_provider = self.create_provider()
        info = restarted_provider.create_collection()
        collection = chromadb.PersistentClient(
            path=str(self.persistence_path)
        ).get_collection(
            name=self.collection_name,
            embedding_function=None,
        )
        stored = collection.get(include=["embeddings"])

        self.assertEqual(info.record_count, 1)
        self.assertEqual(len(stored["embeddings"][0]), 3)


class FailingCollection:
    """Collection test double with configurable operation failures."""

    def __init__(self, fail_operation: str) -> None:
        self._fail_operation = fail_operation

    def count(self) -> int:
        return 1

    def get(self, **kwargs: Any) -> dict[str, list[str]]:
        return {"ids": []}

    def upsert(self, **kwargs: Any) -> None:
        if self._fail_operation == "upsert":
            raise RuntimeError("upsert failed")

    def delete(self, **kwargs: Any) -> None:
        if self._fail_operation == "delete":
            raise RuntimeError("delete failed")


class FakeClient:
    """Chroma client test double."""

    def __init__(
        self,
        collection: FailingCollection | None = None,
        fail_creation: bool = False,
    ) -> None:
        self._collection = collection
        self._fail_creation = fail_creation

    def get_or_create_collection(self, **kwargs: Any) -> FailingCollection:
        if self._fail_creation:
            raise RuntimeError("creation failed")
        assert self._collection is not None
        return self._collection

    def heartbeat(self) -> int:
        return 1


class ChromaVectorStoreErrorTests(unittest.TestCase):
    """Verify Chroma failures map to meaningful provider exceptions."""

    def test_handles_connection_failure(self) -> None:
        def failing_factory(**kwargs: Any) -> Any:
            raise RuntimeError("connection failed")

        provider = ChromaVectorStoreProvider(
            Path("/tmp/chroma-failure-test"),
            "failure-tests",
            client_factory=failing_factory,
        )

        with self.assertRaises(VectorStoreUnavailableError):
            provider.create_collection()

    def test_handles_collection_creation_failure(self) -> None:
        provider = ChromaVectorStoreProvider(
            Path("/tmp/chroma-creation-test"),
            "failure-tests",
            client_factory=lambda **kwargs: FakeClient(fail_creation=True),
        )

        with self.assertRaises(CollectionCreationError):
            provider.create_collection()

    def test_handles_upsert_failure(self) -> None:
        collection = FailingCollection("upsert")
        provider = ChromaVectorStoreProvider(
            Path("/tmp/chroma-upsert-test"),
            "failure-tests",
            client_factory=lambda **kwargs: FakeClient(collection),
        )

        with self.assertRaises(VectorUpsertError):
            provider.upsert_embeddings(
                [create_embedded_chunk("python/oop.md", "OOP")]
            )

    def test_handles_delete_failure(self) -> None:
        collection = FailingCollection("delete")
        provider = ChromaVectorStoreProvider(
            Path("/tmp/chroma-delete-test"),
            "failure-tests",
            client_factory=lambda **kwargs: FakeClient(collection),
        )

        with self.assertRaises(VectorDeleteError):
            provider.delete_embeddings(["python/oop.md"])


if __name__ == "__main__":
    unittest.main()
