"""Tests for the single-turn chat endpoint."""

import os
import unittest

os.environ.setdefault("APP_NAME", "KnowledgeChat AI Backend")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("CHAT_MODEL", "test-model")
os.environ.setdefault("REQUEST_TIMEOUT", "1")

from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.core.config import Settings
from app.main import create_application
from app.providers.base import (
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)


class SuccessfulChatService:
    """Chat service test double returning a successful response."""

    async def generate_response(self, message: str) -> str:
        return f"Response for: {message}"


class UnavailableChatService:
    """Chat service test double simulating an unavailable provider."""

    async def generate_response(self, message: str) -> str:
        raise LLMProviderUnavailableError


class TimedOutChatService:
    """Chat service test double simulating a provider timeout."""

    async def generate_response(self, message: str) -> str:
        raise LLMProviderTimeoutError


class ChatEndpointTests(unittest.TestCase):
    """Verify chat endpoint responses and validation."""

    def create_client(self, service: object) -> TestClient:
        """Create an application client with an overridden chat service."""
        application = create_application(Settings())
        application.dependency_overrides[get_chat_service] = lambda: service
        return TestClient(application)

    def test_successful_request(self) -> None:
        with self.create_client(SuccessfulChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "  Explain Python.  "},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"response": "Response for: Explain Python."},
        )

    def test_ollama_unavailable(self) -> None:
        with self.create_client(UnavailableChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "Explain Python."},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Ollama service unavailable."},
        )

    def test_ollama_timeout(self) -> None:
        with self.create_client(TimedOutChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "Explain Python."},
            )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.json(),
            {"detail": "Ollama request timed out."},
        )

    def test_validation_error_for_blank_message(self) -> None:
        with self.create_client(SuccessfulChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "   "},
            )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
