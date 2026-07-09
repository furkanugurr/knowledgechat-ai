"""Provider-independent language model contract and errors."""

from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Base exception for language model provider failures."""


class LLMProviderUnavailableError(LLMProviderError):
    """Raised when a language model provider cannot fulfill a request."""


class LLMProviderTimeoutError(LLMProviderError):
    """Raised when a language model provider request times out."""


class LLMProvider(ABC):
    """Interface implemented by every language model provider."""

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response for one final prompt."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the provider is reachable."""
