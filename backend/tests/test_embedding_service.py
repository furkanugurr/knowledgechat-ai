"""Tests for provider-independent knowledge chunk embedding."""

import unittest
from collections.abc import Sequence
from datetime import UTC, datetime

from app.embedding.models import EmbeddingVector
from app.embedding.provider import EmbeddingProvider
from app.knowledge.models import KnowledgeChunk, KnowledgeMetadata
from app.services.embedding_service import EmbeddingService


class RecordingEmbeddingProvider(EmbeddingProvider):
    """Embedding provider test double recording batch input."""

    def __init__(self) -> None:
        self.received_texts: list[str] = []
        self.call_count = 0

    async def generate_embeddings(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        self.call_count += 1
        self.received_texts = list(texts)
        return [
            EmbeddingVector(values=[float(index), 1.0, 2.0])
            for index, _ in enumerate(texts)
        ]

    async def health_check(self) -> bool:
        return True


def create_chunk(content: str, chunk_index: int, total: int) -> KnowledgeChunk:
    """Create a knowledge chunk fixture."""
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return KnowledgeChunk(
        content=content,
        metadata=KnowledgeMetadata(
            document_name="example.md",
            relative_path="python/example.md",
            section_title="Example",
            chunk_index=chunk_index,
            total_chunks=total,
            language="en",
            created_at=timestamp,
            updated_at=timestamp,
        ),
    )


class EmbeddingServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify chunk ordering and provider-independent embedding results."""

    async def test_embeds_chunks_and_preserves_original_models(self) -> None:
        provider = RecordingEmbeddingProvider()
        service = EmbeddingService(provider)
        chunks = [
            create_chunk("First chunk", 0, 2),
            create_chunk("Second chunk", 1, 2),
        ]

        result = await service.embed_chunks(chunks)

        self.assertEqual(provider.received_texts, ["First chunk", "Second chunk"])
        self.assertEqual(result.total_chunks, 2)
        self.assertEqual(result.dimensions, 3)
        self.assertEqual(result.embedded_chunks[0].chunk, chunks[0])
        self.assertEqual(
            result.embedded_chunks[1].embedding.values,
            [1.0, 1.0, 2.0],
        )
        self.assertIsInstance(result.model_dump_json(), str)

    async def test_empty_batch_does_not_call_provider(self) -> None:
        provider = RecordingEmbeddingProvider()

        result = await EmbeddingService(provider).embed_chunks([])

        self.assertEqual(provider.call_count, 0)
        self.assertEqual(result.embedded_chunks, [])
        self.assertEqual(result.total_chunks, 0)
        self.assertEqual(result.dimensions, 0)

    async def test_embeds_single_text_for_retrieval(self) -> None:
        provider = RecordingEmbeddingProvider()

        vector = await EmbeddingService(provider).embed_text(
            "What is Python?"
        )

        self.assertEqual(provider.received_texts, ["What is Python?"])
        self.assertEqual(vector.values, [0.0, 1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
