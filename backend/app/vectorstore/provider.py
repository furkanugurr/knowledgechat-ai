"""Vector store provider contract and provider-independent errors."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.embedding.models import EmbeddedChunk, EmbeddingVector
from app.vectorstore.models import VectorCollectionInfo, VectorSearchRecord


class VectorStoreProviderError(Exception):
    """Base exception for vector store provider failures."""


class VectorStoreUnavailableError(VectorStoreProviderError):
    """Raised when a vector store cannot be reached."""


class CollectionCreationError(VectorStoreProviderError):
    """Raised when a vector collection cannot be created."""


class VectorUpsertError(VectorStoreProviderError):
    """Raised when vectors cannot be inserted or updated."""


class VectorDeleteError(VectorStoreProviderError):
    """Raised when vectors cannot be deleted."""


class EmptyVectorStoreError(VectorStoreProviderError):
    """Raised when a similarity search has no indexed vectors."""


class VectorSearchError(VectorStoreProviderError):
    """Raised when vector similarity search fails."""


class InvalidVectorSearchResultError(VectorSearchError):
    """Raised when a provider returns malformed search results."""


class VectorStoreProvider(ABC):
    """Interface implemented by every vector storage provider."""

    @abstractmethod
    def create_collection(self) -> VectorCollectionInfo:
        """Create or load the configured collection."""

    @abstractmethod
    def upsert_embeddings(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        """Insert or update embedded chunks and return their count."""

    @abstractmethod
    def delete_embeddings(
        self,
        relative_paths: Sequence[str],
    ) -> int:
        """Delete vectors for source documents and return their count."""

    @abstractmethod
    def collection_info(self) -> VectorCollectionInfo:
        """Return current collection statistics."""

    @abstractmethod
    def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        """Return the highest-similarity records for one query vector."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return whether the vector store is available."""
