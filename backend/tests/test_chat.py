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
os.environ.setdefault("EMBEDDING_MODEL", "test-embedding-model")
os.environ.setdefault("VECTOR_DB_PATH", "/tmp/knowledgechat-test-chroma")
os.environ.setdefault("VECTOR_COLLECTION_NAME", "knowledgechat-tests")
os.environ.setdefault("REQUEST_TIMEOUT", "1")

from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.core.config import Settings
from app.main import create_application
from app.providers.base import (
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.schemas.chat import ChatResponse, CitationSource
from app.services.chat_service import ChatPromptError, ChatRetrievalError


class SuccessfulChatService:
    """Chat service test double returning a successful response."""

    async def generate_response(self, message: str) -> ChatResponse:
        return ChatResponse(
            response=f"Response for: {message}",
            sources=[
                CitationSource(
                    document_name="oop.md",
                    relative_path="python/oop.md",
                    section_title="Classes",
                    chunk_index=2,
                    similarity_score=0.87,
                    language="en",
                )
            ],
        )


class UnavailableChatService:
    """Chat service test double simulating an unavailable provider."""

    async def generate_response(self, message: str) -> str:
        raise LLMProviderUnavailableError


class TimedOutChatService:
    """Chat service test double simulating a provider timeout."""

    async def generate_response(self, message: str) -> str:
        raise LLMProviderTimeoutError


class RetrievalFailedChatService:
    """Chat service test double simulating retrieval failure."""

    async def generate_response(self, message: str) -> str:
        raise ChatRetrievalError


class PromptFailedChatService:
    """Chat service test double simulating prompt failure."""

    async def generate_response(self, message: str) -> str:
        raise ChatPromptError


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
            {
                "response": "Response for: Explain Python.",
                "sources": [
                    {
                        "document_name": "oop.md",
                        "relative_path": "python/oop.md",
                        "section_title": "Classes",
                        "chunk_index": 2,
                        "similarity_score": 0.87,
                        "language": "en",
                    }
                ],
            },
        )
        self.assertNotIn("chunk_text", response.json()["sources"][0])

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

    def test_retrieval_failure_is_safe(self) -> None:
        with self.create_client(RetrievalFailedChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "Explain Python."},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Knowledge retrieval service unavailable."},
        )

    def test_prompt_failure_is_safe(self) -> None:
        with self.create_client(PromptFailedChatService()) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": "Explain Python."},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"detail": "Unable to build the response prompt."},
        )


if __name__ == "__main__":
    unittest.main()
