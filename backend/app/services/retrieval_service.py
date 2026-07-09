"""Application service for provider-independent semantic retrieval."""

import logging
from time import perf_counter

from app.retrieval.models import RetrievalResult
from app.retrieval.retriever import Retriever
from app.services.embedding_service import EmbeddingService
from app.vectorstore.provider import VectorStoreProvider

logger = logging.getLogger(__name__)


class RetrievalService:
    """Orchestrate retrieval with configured result limits."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store_provider: VectorStoreProvider,
        top_k: int,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        self._retriever = Retriever(
            embedding_service=embedding_service,
            vector_store_provider=vector_store_provider,
        )
        self._top_k = top_k

    async def retrieve(self, question: str) -> RetrievalResult:
        """Retrieve relevant chunks and return a serializable result."""
        started_at = perf_counter()
        logger.info("Retrieval started top_k=%d", self._top_k)
        try:
            chunks = await self._retriever.retrieve(
                question,
                self._top_k,
            )
        except Exception:
            logger.error(
                "Retrieval failed duration_seconds=%.3f",
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        duration = perf_counter() - started_at
        logger.info(
            "Completed retrieval results=%d duration_seconds=%.3f",
            len(chunks),
            duration,
        )
        return RetrievalResult(
            chunks=chunks,
            total_results=len(chunks),
            top_k=self._top_k,
            duration_seconds=duration,
        )
