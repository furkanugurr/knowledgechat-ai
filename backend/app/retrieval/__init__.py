"""Provider-independent semantic retrieval layer."""

from app.retrieval.models import RetrievalResult, RetrievedChunk
from app.retrieval.retriever import (
    EmptyCollectionError,
    InvalidRetrievalResultError,
    RetrievalEmbeddingError,
    RetrievalError,
    RetrievalSearchError,
    Retriever,
)

__all__ = [
    "EmptyCollectionError",
    "InvalidRetrievalResultError",
    "RetrievalEmbeddingError",
    "RetrievalError",
    "RetrievalResult",
    "RetrievalSearchError",
    "RetrievedChunk",
    "Retriever",
]
