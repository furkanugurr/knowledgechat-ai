"""Tests for the Ollama embedding provider."""

import json
import unittest

import httpx

from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.embedding.provider import (
    EmbeddingProvider,
    EmbeddingProviderInvalidResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)


class OllamaEmbeddingProviderTests(unittest.IsolatedAsyncioTestCase):
    """Verify Ollama HTTP requests, validation, and error mapping."""

    async def test_generates_embeddings_successfully(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(request.url.path, "/api/embed")
            self.assertEqual(payload["model"], "configured-model")
            self.assertEqual(payload["input"], ["First", "Second"])
            return httpx.Response(
                200,
                json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]},
            )

        provider = OllamaEmbeddingProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            vectors = await provider.generate_embeddings(["First", "Second"])
        finally:
            await provider.close()

        self.assertIsInstance(provider, EmbeddingProvider)
        self.assertEqual(vectors[0].values, [0.1, 0.2])
        self.assertEqual(vectors[1].values, [0.3, 0.4])

    async def test_maps_timeout_to_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        provider = OllamaEmbeddingProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            with self.assertRaises(EmbeddingProviderTimeoutError):
                await provider.generate_embeddings(["Text"])
        finally:
            await provider.close()

    async def test_maps_connection_failure_to_unavailable_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("unavailable", request=request)

        provider = OllamaEmbeddingProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            with self.assertRaises(EmbeddingProviderUnavailableError):
                await provider.generate_embeddings(["Text"])
        finally:
            await provider.close()

    async def test_rejects_invalid_embedding_response(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"embeddings": [["not-a-number"]]},
            )

        provider = OllamaEmbeddingProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            with self.assertRaises(EmbeddingProviderInvalidResponseError):
                await provider.generate_embeddings(["Text"])
        finally:
            await provider.close()

    async def test_health_check_reports_reachability(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api/tags")
            return httpx.Response(200, json={"models": []})

        provider = OllamaEmbeddingProvider(
            host="http://ollama.test",
            model="configured-model",
            timeout=1,
            transport=httpx.MockTransport(handler),
        )
        await provider.start()
        try:
            is_healthy = await provider.health_check()
        finally:
            await provider.close()

        self.assertTrue(is_healthy)


if __name__ == "__main__":
    unittest.main()
