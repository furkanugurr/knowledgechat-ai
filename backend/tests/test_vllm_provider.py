"""Tests for the optional OpenAI-compatible vLLM chat provider."""

import json
import os
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ.setdefault("APP_NAME", "KnowledgeChat AI Backend")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("OLLAMA_HOST", "http://ollama.test")
os.environ.setdefault("CHAT_MODEL", "gemma3:12b")
os.environ.setdefault("EMBEDDING_MODEL", "nomic-embed-text")
os.environ.setdefault("VECTOR_DB_PATH", "/tmp/vllm-provider-tests")
os.environ.setdefault("VECTOR_COLLECTION_NAME", "test")
os.environ.setdefault("REQUEST_TIMEOUT", "1")

from app.api.dependencies import get_chat_service
from app.core.config import Settings
from app.main import create_application
from app.providers.base import (
    LLMProvider,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.providers.factory import create_llm_provider
from app.providers.ollama_provider import OllamaProvider
from app.providers.vllm_provider import VLLMProvider
from app.schemas.chat import ChatResponse, CitationSource


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "APP_NAME": "KnowledgeChat AI Backend",
        "APP_VERSION": "0.1.0",
        "ENVIRONMENT": "test",
        "HOST": "127.0.0.1",
        "PORT": 8000,
        "LOG_LEVEL": "WARNING",
        "OLLAMA_HOST": "http://ollama.test",
        "CHAT_MODEL": "gemma3:12b",
        "EMBEDDING_MODEL": "nomic-embed-text",
        "VECTOR_DB_PATH": "/tmp/vllm-provider-tests",
        "VECTOR_COLLECTION_NAME": "test",
        "REQUEST_TIMEOUT": 1,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


class ProviderBackedChatService:
    """Small endpoint fixture exercising provider output and public schema."""

    def __init__(self, provider: VLLMProvider) -> None:
        self.provider = provider

    async def generate_response(self, message: str) -> ChatResponse:
        answer = await self.provider.generate_response(message)
        return ChatResponse(
            response=answer,
            sources=[
                CitationSource(
                    document_name="guide.md",
                    relative_path="guides/guide.md",
                    section_title="Kapsam",
                    chunk_index=0,
                    similarity_score=0.91,
                    language="tr",
                )
            ],
        )


class VLLMProviderTests(unittest.IsolatedAsyncioTestCase):
    """Validate requests, responses, lifecycle, and safe failures."""

    def create_provider(
        self,
        handler: httpx.MockTransport,
        *,
        api_key: str = "",
    ) -> VLLMProvider:
        return VLLMProvider(
            base_url="http://vllm.test/",
            model="Qwen/Qwen2.5-0.5B-Instruct",
            api_key=api_key,
            timeout=1,
            max_tokens=321,
            transport=handler,
        )

    async def test_implements_provider_contract(self) -> None:
        self.assertTrue(issubclass(VLLMProvider, LLMProvider))

    async def test_requires_start_before_generation(self) -> None:
        provider = self.create_provider(httpx.MockTransport(lambda _: None))
        with self.assertRaisesRegex(RuntimeError, "must be started"):
            await provider.generate_response("prompt")

    async def test_sends_openai_compatible_request(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(request.url.path, "/v1/chat/completions")
            self.assertEqual(
                payload["model"], "Qwen/Qwen2.5-0.5B-Instruct"
            )
            self.assertEqual(
                payload["messages"], [{"role": "user", "content": "prompt"}]
            )
            self.assertEqual(payload["max_tokens"], 321)
            self.assertEqual(payload["temperature"], 0)
            self.assertFalse(payload["stream"])
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": " yanıt "}}]},
            )

        provider = self.create_provider(httpx.MockTransport(handler))
        await provider.start()
        try:
            self.assertEqual(await provider.generate_response("prompt"), " yanıt ")
        finally:
            await provider.close()

    async def test_adds_bearer_header_when_key_is_configured(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["authorization"], "Bearer secret")
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "ok"}}]}
            )

        provider = self.create_provider(
            httpx.MockTransport(handler), api_key=" secret "
        )
        await provider.start()
        try:
            await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_omits_authorization_when_key_is_empty(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "ok"}}]}
            )

        provider = self.create_provider(httpx.MockTransport(handler))
        await provider.start()
        try:
            await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_health_check_uses_models_endpoint(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(
                lambda request: httpx.Response(
                    200 if request.url.path == "/v1/models" else 404
                )
            )
        )
        await provider.start()
        try:
            self.assertTrue(await provider.health_check())
        finally:
            await provider.close()

    async def test_health_check_returns_false_for_http_error(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(lambda _: httpx.Response(503))
        )
        await provider.start()
        try:
            self.assertFalse(await provider.health_check())
        finally:
            await provider.close()

    async def test_timeout_uses_shared_timeout_error(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow")

        provider = self.create_provider(httpx.MockTransport(handler))
        await provider.start()
        try:
            with self.assertRaises(LLMProviderTimeoutError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_http_error_uses_shared_unavailable_error(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(lambda _: httpx.Response(500))
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_invalid_json_uses_shared_unavailable_error(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(
                lambda _: httpx.Response(200, content=b"not-json")
            )
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_missing_choices_is_rejected(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(lambda _: httpx.Response(200, json={}))
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_empty_choices_is_rejected(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(
                lambda _: httpx.Response(200, json={"choices": []})
            )
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_missing_message_is_rejected(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(
                lambda _: httpx.Response(200, json={"choices": [{}]})
            )
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_empty_content_is_rejected(self) -> None:
        payload = {"choices": [{"message": {"content": "  "}}]}
        provider = self.create_provider(
            httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
        )
        await provider.start()
        try:
            with self.assertRaises(LLMProviderUnavailableError):
                await provider.generate_response("prompt")
        finally:
            await provider.close()

    async def test_start_is_idempotent_and_close_clears_client(self) -> None:
        provider = self.create_provider(
            httpx.MockTransport(lambda _: httpx.Response(200))
        )
        await provider.start()
        client = provider._client
        await provider.start()
        self.assertIs(provider._client, client)
        await provider.close()
        self.assertIsNone(provider._client)


class ProviderSelectionTests(unittest.TestCase):
    """Verify default compatibility and explicit provider selection."""

    def test_default_provider_is_ollama(self) -> None:
        provider = create_llm_provider(make_settings())
        self.assertIsInstance(provider, OllamaProvider)

    def test_explicit_ollama_provider_is_selected(self) -> None:
        provider = create_llm_provider(make_settings(LLM_PROVIDER="OLLAMA"))
        self.assertIsInstance(provider, OllamaProvider)

    def test_vllm_provider_is_selected_with_configured_values(self) -> None:
        settings = make_settings(
            LLM_PROVIDER="vllm",
            VLLM_BASE_URL="http://custom:9000",
            VLLM_MODEL="custom-model",
            VLLM_API_KEY="token",
            VLLM_REQUEST_TIMEOUT_SECONDS=42,
        )
        provider = create_llm_provider(settings)
        self.assertIsInstance(provider, VLLMProvider)
        self.assertEqual(provider._base_url, "http://custom:9000")
        self.assertEqual(provider._model, "custom-model")
        self.assertEqual(provider._timeout, 42)

    def test_provider_value_is_normalized(self) -> None:
        self.assertEqual(
            make_settings(LLM_PROVIDER=" VLLM ").llm_provider, "vllm"
        )

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            make_settings(LLM_PROVIDER="unknown")


class VLLMEndpointIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Verify mocked vLLM generation preserves the public HTTP contract."""

    async def test_endpoint_returns_vllm_answer_and_citations(self) -> None:
        provider = VLLMProvider(
            base_url="http://vllm.test",
            model="test-model",
            api_key="",
            timeout=1,
            max_tokens=128,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "choices": [
                            {"message": {"content": "Kaynaklı vLLM yanıtı"}}
                        ]
                    },
                )
            ),
        )
        await provider.start()
        application = create_application(make_settings())
        application.dependency_overrides[get_chat_service] = (
            lambda: ProviderBackedChatService(provider)
        )
        try:
            with TestClient(application) as client:
                response = client.post(
                    "/api/v1/chat", json={"message": "VLAN nedir?"}
                )
        finally:
            await provider.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "Kaynaklı vLLM yanıtı")
        self.assertEqual(len(response.json()["sources"]), 1)
        self.assertEqual(
            response.json()["sources"][0]["relative_path"], "guides/guide.md"
        )
        self.assertNotIn("chunk_text", response.json()["sources"][0])


if __name__ == "__main__":
    unittest.main()
