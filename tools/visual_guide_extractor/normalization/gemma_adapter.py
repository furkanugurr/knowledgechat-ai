"""Gemma adapter constrained to editing HTML and Qwen evidence."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from tools.visual_guide_extractor.schemas.extraction import (
    GuidePage,
    NormalizedGuide,
    VisionExtraction,
)


class GemmaNormalizer:
    """Normalize language without introducing new guide information."""

    def __init__(self, host: str, model: str, prompt_path: Path, timeout: float) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._prompt = prompt_path.read_text(encoding="utf-8").strip()
        self._client = httpx.Client(timeout=timeout)

    def normalize(
        self,
        page: GuidePage,
        vision_results: list[VisionExtraction],
    ) -> NormalizedGuide:
        """Return schema-validated editorial normalization."""
        evidence = {
            "page": page.model_dump(mode="json"),
            "vision_results": [result.model_dump(mode="json") for result in vision_results],
        }
        response = self._client.post(
            f"{self._host}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "format": NormalizedGuide.model_json_schema(),
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"{self._prompt}\n\nSOURCE EVIDENCE:\n"
                            f"{json.dumps(evidence, ensure_ascii=False)}"
                        ),
                    }
                ],
                "options": {"temperature": 0},
                "keep_alive": "5m",
            },
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("Gemma normalization response has no message content")
        result = NormalizedGuide.model_validate_json(content)
        return result.model_copy(
            update={"page_title": page.page_title, "source_url": page.source_url}
        )

    def unload(self) -> None:
        """Release Gemma after the normalization phase."""
        response = self._client.post(
            f"{self._host}/api/generate",
            json={"model": self._model, "keep_alive": 0},
        )
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()
