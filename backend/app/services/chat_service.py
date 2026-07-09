"""Provider-independent chat application service."""

import logging
from time import perf_counter

from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class ChatService:
    """Coordinate prompt construction and language model generation."""

    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder

    async def generate_response(self, user_message: str) -> str:
        """Build a final prompt and return the provider response."""
        provider_name = type(self._provider).__name__
        started_at = perf_counter()
        logger.info("Chat generation started provider=%s", provider_name)

        try:
            prompt = self._prompt_builder.build(user_message)
            response = await self._provider.generate_response(prompt)
        except Exception:
            logger.error(
                "Chat generation failed provider=%s duration_seconds=%.3f",
                provider_name,
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        logger.info(
            "Chat generation succeeded provider=%s duration_seconds=%.3f",
            provider_name,
            perf_counter() - started_at,
        )
        return response
