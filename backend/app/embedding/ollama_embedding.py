"""Ollama implementation of the embedding provider contract."""

import logging
import math
from collections.abc import Sequence
from typing import Any

import httpx

from app.embedding.models import EmbeddingVector
from app.embedding.provider import (
    EmbeddingProvider,
    EmbeddingProviderInvalidResponseError,
    EmbeddingProviderTimeoutError,
    EmbeddingProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Generate embeddings through Ollama's asynchronous HTTP API."""

    _BATCH_SIZE = 32

    def __init__(
        self,
        host: str,
        model: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Create the managed asynchronous HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._host,
                timeout=self._timeout,
                transport=self._transport,
            )

    async def close(self) -> None:
        """Close the managed asynchronous HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate_embeddings(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return one validated Ollama embedding for every input text."""
        if not texts:
            return []

        client = self._require_client()
        vectors: list[EmbeddingVector] = []
        try:
            for start in range(0, len(texts), self._BATCH_SIZE):
                batch = list(texts[start : start + self._BATCH_SIZE])
                response = await client.post(
                    "/api/embed",
                    json={
                        "model": self._model,
                        "input": batch,
                    },
                )
                response.raise_for_status()
                vectors.extend(self._extract_vectors(response.json(), len(batch)))
        except httpx.TimeoutException as exc:
            logger.error(
                "Embedding provider timed out provider=ollama model=%s",
                self._model,
            )
            raise EmbeddingProviderTimeoutError(
                "Ollama embedding request timed out."
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(
                "Embedding provider unavailable provider=ollama model=%s",
                self._model,
            )
            raise EmbeddingProviderUnavailableError(
                "Ollama embedding service unavailable."
            ) from exc

        except (ValueError, EmbeddingProviderInvalidResponseError) as exc:
            logger.error(
                "Embedding provider returned invalid data "
                "provider=ollama model=%s",
                self._model,
            )
            raise EmbeddingProviderInvalidResponseError(
                "Ollama returned an invalid embedding response."
            ) from exc

        return vectors

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
        """Return the active HTTP client."""
        if self._client is None:
            raise RuntimeError(
                "OllamaEmbeddingProvider must be started before use."
            )
        return self._client

    @staticmethod
    def _extract_vectors(
        payload: Any,
        expected_count: int,
    ) -> list[EmbeddingVector]:
        """Validate response count, numeric values, and vector dimensions."""
        if not isinstance(payload, dict):
            raise EmbeddingProviderInvalidResponseError

        raw_embeddings = payload.get("embeddings")
        if (
            not isinstance(raw_embeddings, list)
            or len(raw_embeddings) != expected_count
        ):
            raise EmbeddingProviderInvalidResponseError

        vectors: list[EmbeddingVector] = []
        dimensions: int | None = None
        for raw_vector in raw_embeddings:
            if not isinstance(raw_vector, list) or not raw_vector:
                raise EmbeddingProviderInvalidResponseError
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in raw_vector
            ):
                raise EmbeddingProviderInvalidResponseError

            vector = EmbeddingVector(
                values=[float(value) for value in raw_vector]
            )
            if dimensions is None:
                dimensions = len(vector.values)
            elif len(vector.values) != dimensions:
                raise EmbeddingProviderInvalidResponseError
            vectors.append(vector)

        return vectors
