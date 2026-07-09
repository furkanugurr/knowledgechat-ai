"""Provider-independent vector storage layer."""

from app.vectorstore.chroma_provider import ChromaVectorStoreProvider
from app.vectorstore.models import (
    VectorCollectionInfo,
    VectorSearchRecord,
    VectorStoreResult,
)
from app.vectorstore.provider import (
    CollectionCreationError,
    EmptyVectorStoreError,
    InvalidVectorSearchResultError,
    VectorDeleteError,
    VectorSearchError,
    VectorStoreProvider,
    VectorStoreProviderError,
    VectorStoreUnavailableError,
    VectorUpsertError,
)

__all__ = [
    "ChromaVectorStoreProvider",
    "CollectionCreationError",
    "EmptyVectorStoreError",
    "InvalidVectorSearchResultError",
    "VectorCollectionInfo",
    "VectorDeleteError",
    "VectorSearchError",
    "VectorSearchRecord",
    "VectorStoreProvider",
    "VectorStoreProviderError",
    "VectorStoreResult",
    "VectorStoreUnavailableError",
    "VectorUpsertError",
]
