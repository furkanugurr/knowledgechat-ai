"""Provider-independent knowledge chunk embedding service."""

import logging
from collections.abc import Sequence
from time import perf_counter

from app.embedding.models import (
    EmbeddedChunk,
    EmbeddingResult,
    EmbeddingVector,
)
from app.embedding.provider import (
    EmbeddingProvider,
    EmbeddingProviderInvalidResponseError,
)
from app.knowledge.models import KnowledgeChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings while preserving original knowledge chunks."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    async def embed_text(self, text: str) -> EmbeddingVector:
        """Generate one embedding without knowledge chunk construction."""
        if not text.strip():
            raise ValueError("text cannot be empty")

        vectors = await self._provider.generate_embeddings([text])
        if len(vectors) != 1:
            raise EmbeddingProviderInvalidResponseError(
                "Embedding provider must return exactly one vector"
            )
        return vectors[0]

    async def embed_chunks(
        self,
        chunks: Sequence[KnowledgeChunk],
    ) -> EmbeddingResult:
        """Generate and pair one embedding for each knowledge chunk."""
        started_at = perf_counter()
        logger.info("Embedding started chunks=%d", len(chunks))

        if not chunks:
            duration = perf_counter() - started_at
            logger.info(
                "Embedding completed chunks=0 duration_seconds=%.3f",
                duration,
            )
            return EmbeddingResult(
                embedded_chunks=[],
                total_chunks=0,
                dimensions=0,
                duration_seconds=duration,
            )

        try:
            vectors = await self._provider.generate_embeddings(
                [chunk.content for chunk in chunks]
            )
        except Exception:
            logger.error(
                "Embedding failed chunks=%d duration_seconds=%.3f",
                len(chunks),
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        if len(vectors) != len(chunks):
            raise EmbeddingProviderInvalidResponseError(
                "Embedding provider result count does not match chunk count"
            )

        embedded_chunks = [
            EmbeddedChunk(chunk=chunk, embedding=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        duration = perf_counter() - started_at
        logger.info("Embedding chunks processed chunks=%d", len(chunks))
        logger.info(
            "Embedding completed chunks=%d duration_seconds=%.3f",
            len(chunks),
            duration,
        )
        return EmbeddingResult(
            embedded_chunks=embedded_chunks,
            total_chunks=len(embedded_chunks),
            dimensions=len(vectors[0].values),
            duration_seconds=duration,
        )
