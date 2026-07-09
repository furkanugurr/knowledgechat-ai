"""Application service for persisting generated embeddings."""

import logging
from time import perf_counter

from app.embedding.models import EmbeddingResult
from app.knowledge.models import IndexResult
from app.vectorstore.models import VectorStoreResult
from app.vectorstore.provider import VectorStoreProvider

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Persist embedding changes without generating or retrieving vectors."""

    def __init__(self, provider: VectorStoreProvider) -> None:
        self._provider = provider

    def store(
        self,
        embedding_result: EmbeddingResult,
        index_result: IndexResult,
    ) -> VectorStoreResult:
        """Apply removals and upserts, then return collection statistics."""
        started_at = perf_counter()
        logger.info(
            "Vector storage started upserts=%d removed_documents=%d",
            embedding_result.total_chunks,
            len(index_result.removed_files),
        )

        try:
            self._provider.create_collection()
            deleted_count = self._provider.delete_embeddings(
                index_result.removed_files
            )
            upserted_count = self._provider.upsert_embeddings(
                embedding_result.embedded_chunks
            )
            collection_info = self._provider.collection_info()
        except Exception:
            logger.error(
                "Vector storage failed duration_seconds=%.3f",
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        duration = perf_counter() - started_at

        logger.info(
            "Vector storage completed upserted=%d deleted=%d total=%d "
            "duration_seconds=%.3f",
            upserted_count,
            deleted_count,
            collection_info.record_count,
            duration,
        )
        return VectorStoreResult(
            collection_name=collection_info.collection_name,
            vectors_upserted=upserted_count,
            vectors_deleted=deleted_count,
            total_vectors=collection_info.record_count,
            duration_seconds=duration,
        )
