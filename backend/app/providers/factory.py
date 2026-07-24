"""Language-model provider construction at the application boundary."""

from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.vllm_provider import VLLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create the configured provider without changing application services."""
    if settings.llm_provider == "vllm":
        return VLLMProvider(
            base_url=settings.vllm_base_url,
            model=settings.vllm_model,
            api_key=settings.vllm_api_key,
            timeout=settings.vllm_request_timeout_seconds,
            max_tokens=settings.chat_max_tokens,
        )

    return OllamaProvider(
        host=settings.ollama_host,
        model=settings.chat_model,
        timeout=settings.request_timeout,
        max_tokens=settings.chat_max_tokens,
    )
