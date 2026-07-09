"""Provider-independent embedding generation layer."""

from app.embedding.models import (
    EmbeddedChunk,
    EmbeddingResult,
    EmbeddingVector,
)
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.embedding.provider import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderInvalidResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)

__all__ = [
    "EmbeddedChunk",
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "EmbeddingProviderInvalidResponseError",
    "EmbeddingProviderTimeoutError",
    "EmbeddingProviderUnavailableError",
    "EmbeddingResult",
    "EmbeddingVector",
    "OllamaEmbeddingProvider",
]
