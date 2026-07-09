"""Run the knowledge indexing, embedding, and vector storage pipeline."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.knowledge.cache import IndexCache
from app.knowledge.indexer import KnowledgeIndexer
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.manifest import ManifestLoader
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IndexingSummary:
    """Short operational summary for one end-to-end indexing run."""

    files_scanned: int
    files_indexed: int
    chunks_embedded: int
    vectors_stored: int

    def format(self) -> str:
        """Return a concise human-readable summary."""
        return "\n".join(
            (
                "Knowledge indexing completed",
                f"Files scanned: {self.files_scanned}",
                f"Files indexed: {self.files_indexed}",
                f"Chunks embedded: {self.chunks_embedded}",
                f"Vectors stored: {self.vectors_stored}",
            )
        )


async def run_indexing_pipeline(
    indexer: KnowledgeIndexer,
    embedding_service: EmbeddingService,
    vector_store_service: VectorStoreService,
) -> IndexingSummary:
    """Run existing pipeline components without constructing providers."""
    index_result = await asyncio.to_thread(indexer.index)
    embedding_result = await embedding_service.embed_chunks(
        index_result.chunks
    )
    vector_result = await asyncio.to_thread(
        vector_store_service.store,
        embedding_result,
        index_result,
    )
    return IndexingSummary(
        files_scanned=index_result.statistics.files_scanned,
        files_indexed=index_result.statistics.files_indexed,
        chunks_embedded=embedding_result.total_chunks,
        vectors_stored=vector_result.vectors_upserted,
    )


def create_indexer(repository_root: Path) -> KnowledgeIndexer:
    """Create the repository-backed knowledge indexer."""
    knowledge_base_path = repository_root / "knowledge_base"
    return KnowledgeIndexer(
        loader=KnowledgeLoader(knowledge_base_path),
        manifest_loader=ManifestLoader(
            knowledge_base_path / "manifest.yaml"
        ),
        cache=IndexCache(
            repository_root / "backend" / "data" / "index_cache.json"
        ),
    )


async def run(settings: Settings) -> IndexingSummary:
    """Construct configured providers and execute local indexing."""
    repository_root = Path(__file__).resolve().parents[2]
    embedding_provider = OllamaEmbeddingProvider(
        host=settings.ollama_host,
        model=settings.embedding_model,
        timeout=settings.request_timeout,
    )
    embedding_service = EmbeddingService(embedding_provider)
    vector_store_service = VectorStoreService(
        ChromaVectorStoreProvider(
            persistence_path=settings.vector_db_path,
            collection_name=settings.vector_collection_name,
        )
    )

    await embedding_provider.start()
    try:
        return await run_indexing_pipeline(
            indexer=create_indexer(repository_root),
            embedding_service=embedding_service,
            vector_store_service=vector_store_service,
        )
    finally:
        await embedding_provider.close()


def main() -> int:
    """Run the local indexing utility and print its summary."""
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        summary = asyncio.run(run(settings))
    except Exception:
        logger.exception("Knowledge indexing failed")
        return 1

    print(summary.format())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
