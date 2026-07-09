"""Tests for the language model provider abstraction."""

import unittest

from app.providers.base import LLMProvider
from app.providers.ollama_provider import OllamaProvider


class GenerateOnlyProvider(LLMProvider):
    """Incomplete provider used to verify the abstract contract."""

    async def generate_response(self, prompt: str) -> str:
        return prompt


class ProviderAbstractionTests(unittest.TestCase):
    """Verify provider implementations must satisfy the shared contract."""

    def test_ollama_provider_implements_llm_provider(self) -> None:
        self.assertTrue(issubclass(OllamaProvider, LLMProvider))

    def test_provider_requires_health_check(self) -> None:
        with self.assertRaises(TypeError):
            GenerateOnlyProvider()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
