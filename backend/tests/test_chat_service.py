"""Tests for provider-independent chat orchestration."""

import unittest

from app.providers.base import LLMProvider
from app.services.chat_service import ChatService


class RecordingProvider(LLMProvider):
    """Provider test double recording the received final prompt."""

    def __init__(self) -> None:
        self.received_prompt: str | None = None

    async def generate_response(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "Generated response"

    async def health_check(self) -> bool:
        return True


class RecordingPromptBuilder:
    """Prompt builder test double recording the user message."""

    def __init__(self) -> None:
        self.received_message: str | None = None

    def build(self, user_message: str) -> str:
        self.received_message = user_message
        return "Final managed prompt"


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify chat orchestration without HTTP or Ollama."""

    async def test_builds_prompt_and_calls_provider(self) -> None:
        provider = RecordingProvider()
        prompt_builder = RecordingPromptBuilder()
        service = ChatService(
            provider=provider,
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
        )

        response = await service.generate_response("User message")

        self.assertEqual(response, "Generated response")
        self.assertEqual(prompt_builder.received_message, "User message")
        self.assertEqual(provider.received_prompt, "Final managed prompt")


if __name__ == "__main__":
    unittest.main()
