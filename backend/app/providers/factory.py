"""Language-model provider construction at the application boundary."""

import logging

from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.vllm_provider import VLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create the configured provider without changing application services."""
    if settings.llm_provider == "vllm":
        logger.info(
            "LLM provider selected provider=vllm model=%s",
            settings.vllm_model,
        )
        return VLLMProvider(
            base_url=settings.vllm_base_url,
            model=settings.vllm_model,
            api_key=settings.vllm_api_key,
            timeout=settings.vllm_request_timeout_seconds,
            max_tokens=settings.chat_max_tokens,
        )

    logger.info(
        "LLM provider selected provider=ollama model=%s",
        settings.chat_model,
    )
    return OllamaProvider(
        host=settings.ollama_host,
        model=settings.chat_model,
        timeout=settings.request_timeout,
        max_tokens=settings.chat_max_tokens,
    )
