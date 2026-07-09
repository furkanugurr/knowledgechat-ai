"""Tests for the local end-to-end indexing utility core."""

import unittest
from types import SimpleNamespace

from scripts.index_knowledge import run_indexing_pipeline


class IndexerDouble:
    """Knowledge indexer test double."""

    def index(self):
        return SimpleNamespace(
            chunks=["chunk-1", "chunk-2"],
            statistics=SimpleNamespace(
                files_scanned=4,
                files_indexed=2,
            ),
            removed_files=[],
        )


class EmbeddingServiceDouble:
    """Embedding service test double."""

    def __init__(self) -> None:
        self.received_chunks = None

    async def embed_chunks(self, chunks):
        self.received_chunks = chunks
        return SimpleNamespace(
            embedded_chunks=["embedded-1", "embedded-2"],
            total_chunks=2,
        )


class VectorStoreServiceDouble:
    """Vector store service test double."""

    def __init__(self) -> None:
        self.embedding_result = None
        self.index_result = None

    def store(self, embedding_result, index_result):
        self.embedding_result = embedding_result
        self.index_result = index_result
        return SimpleNamespace(vectors_upserted=2)


class IndexKnowledgeScriptTests(unittest.IsolatedAsyncioTestCase):
    """Verify script orchestration without Ollama or ChromaDB."""

    async def test_runs_existing_pipeline_and_returns_summary(self) -> None:
        indexer = IndexerDouble()
        embedding_service = EmbeddingServiceDouble()
        vector_store_service = VectorStoreServiceDouble()

        summary = await run_indexing_pipeline(
            indexer=indexer,  # type: ignore[arg-type]
            embedding_service=embedding_service,  # type: ignore[arg-type]
            vector_store_service=vector_store_service,  # type: ignore[arg-type]
        )

        self.assertEqual(embedding_service.received_chunks, indexer.index().chunks)
        self.assertIsNotNone(vector_store_service.embedding_result)
        self.assertIsNotNone(vector_store_service.index_result)
        self.assertEqual(summary.files_scanned, 4)
        self.assertEqual(summary.files_indexed, 2)
        self.assertEqual(summary.chunks_embedded, 2)
        self.assertEqual(summary.vectors_stored, 2)
        self.assertIn("Files scanned: 4", summary.format())


if __name__ == "__main__":
    unittest.main()
