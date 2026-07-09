"""Ollama implementation of the language model provider contract."""

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


class OllamaProvider(LLMProvider):
    """Generate responses through the asynchronous Ollama HTTP API."""

    def __init__(self, host: str, model: str, timeout: float) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Create the managed asynchronous HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._host,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        """Close the managed asynchronous HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate_response(self, prompt: str) -> str:
        """Send a final prompt to Ollama and return its validated response."""
        client = self._require_client()
        started_at = perf_counter()
        logger.info("Provider request started provider=ollama model=%s", self._model)

        try:
            response = await client.post(
                "/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
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
            "Provider request succeeded provider=ollama model=%s "
            "duration_seconds=%.3f",
            self._model,
            perf_counter() - started_at,
        )
        return generated_text

    async def health_check(self) -> bool:
        """Return whether the Ollama HTTP API is reachable."""
        client = self._require_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    def _require_client(self) -> httpx.AsyncClient:
        """Return the active client or fail on invalid lifecycle usage."""
        if self._client is None:
            raise RuntimeError("OllamaProvider must be started before use.")
        return self._client

    @staticmethod
    def _extract_generated_text(payload: Any) -> str:
        """Extract a non-empty generated response from an Ollama payload."""
        if not isinstance(payload, dict):
            raise LLMProviderUnavailableError

        generated_text = payload.get("response")
        if not isinstance(generated_text, str) or not generated_text.strip():
            raise LLMProviderUnavailableError

        return generated_text

    def _log_failure(self, started_at: float, reason: str) -> None:
        """Log provider failure metadata without prompt or response content."""
        logger.error(
            "Provider request failed provider=ollama model=%s reason=%s "
            "duration_seconds=%.3f",
            self._model,
            reason,
            perf_counter() - started_at,
        )
