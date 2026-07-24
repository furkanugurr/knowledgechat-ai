"""OpenAI-compatible vLLM implementation of the language model contract."""

import logging
from time import perf_counter
from typing import Any

import httpx

from app.providers.base import (
    LLMProvider,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class VLLMProvider(LLMProvider):
    """Generate responses through vLLM's OpenAI-compatible HTTP API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout: float,
        max_tokens: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key.strip()
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Create the managed asynchronous HTTP client."""
        if self._client is None:
            headers = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=self._timeout,
                transport=self._transport,
            )

    async def close(self) -> None:
        """Close the managed asynchronous HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate_response(self, prompt: str) -> str:
        """Send a final prompt and return validated assistant content."""
        client = self._require_client()
        started_at = perf_counter()
        logger.info("Provider request started provider=vllm model=%s", self._model)

        try:
            response = await client.post(
                "/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "temperature": 0,
                    "max_tokens": self._max_tokens,
                },
            )
            response.raise_for_status()
            generated_text = self._extract_generated_text(response.json())
        except httpx.TimeoutException as exc:
            self._log_failure(started_at, "timeout")
            raise LLMProviderTimeoutError from exc
        except (
            httpx.HTTPError,
            ValueError,
            LLMProviderUnavailableError,
        ) as exc:
            self._log_failure(started_at, "unavailable")
            raise LLMProviderUnavailableError from exc

        logger.info(
            "Provider request succeeded provider=vllm model=%s "
            "duration_seconds=%.3f",
            self._model,
            perf_counter() - started_at,
        )
        return generated_text

    async def health_check(self) -> bool:
        """Return whether the vLLM OpenAI-compatible API is reachable."""
        client = self._require_client()
        try:
            response = await client.get("/v1/models")
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("VLLMProvider must be started before use.")
        return self._client

    @staticmethod
    def _extract_generated_text(payload: Any) -> str:
        if not isinstance(payload, dict):
            raise LLMProviderUnavailableError
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderUnavailableError
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMProviderUnavailableError
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMProviderUnavailableError
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderUnavailableError
        return content

    def _log_failure(self, started_at: float, reason: str) -> None:
        logger.error(
            "Provider request failed provider=vllm model=%s reason=%s "
            "duration_seconds=%.3f",
            self._model,
            reason,
            perf_counter() - started_at,
        )
