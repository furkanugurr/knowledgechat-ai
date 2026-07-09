"""Embedding provider contract and provider-independent errors."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.embedding.models import EmbeddingVector


class EmbeddingProviderError(Exception):
    """Base exception for embedding provider failures."""


class EmbeddingProviderUnavailableError(EmbeddingProviderError):
    """Raised when an embedding provider cannot be reached."""


class EmbeddingProviderTimeoutError(EmbeddingProviderError):
    """Raised when an embedding request exceeds its timeout."""


class EmbeddingProviderInvalidResponseError(EmbeddingProviderError):
    """Raised when an embedding provider returns malformed data."""


class EmbeddingProvider(ABC):
    """Interface implemented by every embedding provider."""

    @abstractmethod
    async def generate_embeddings(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Generate one embedding vector for every input text."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the embedding provider is reachable."""
