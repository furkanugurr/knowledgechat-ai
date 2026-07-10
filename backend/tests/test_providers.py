"""Tests for the language model provider abstraction."""

import json
import unittest

import httpx

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


class OllamaProviderRequestTests(unittest.IsolatedAsyncioTestCase):
    """Verify Ollama generation request options and response handling."""

    async def test_sends_configured_output_token_limit(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(request.url.path, "/api/generate")
            self.assertEqual(payload["model"], "configured-model")
            self.assertEqual(payload["prompt"], "Grounded prompt")
            self.assertFalse(payload["stream"])
            self.assertEqual(payload["options"]["num_predict"], 768)
            return httpx.Response(200, json={"response": "Detailed answer"})

        provider = OllamaProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            max_tokens=768,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            response = await provider.generate_response("Grounded prompt")
        finally:
            await provider.close()

        self.assertEqual(response, "Detailed answer")


if __name__ == "__main__":
    unittest.main()
