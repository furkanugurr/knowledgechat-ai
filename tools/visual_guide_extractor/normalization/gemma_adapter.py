"""Gemma adapter constrained to editing HTML and Qwen evidence."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from pydantic import ValidationError

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

    def normalize_compact(
        self,
        page: GuidePage,
        vision_results: list[VisionExtraction],
    ) -> NormalizedGuide:
        """Retry normalization with compact evidence to reduce truncation risk."""
        evidence = {
            "page_title": page.page_title,
            "source_url": page.source_url,
            "html_text": page.html_context()[:8000],
            "vision_results": [
                {
                    "screen_name": result.screen_name,
                    "purpose": result.purpose,
                    "visible_navigation_path": result.visible_navigation_path,
                    "controls": [item.model_dump(mode="json") for item in result.controls],
                    "fields": [item.model_dump(mode="json") for item in result.fields],
                    "ordered_steps": result.ordered_steps,
                    "warnings": result.warnings,
                    "uncertainties": result.uncertainties,
                }
                for result in vision_results
            ],
        }
        response = self._client.post(
            f"{self._host}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "format": NormalizedGuide.model_json_schema(),
                "messages": [{
                    "role": "user",
                    "content": (
                        f"{self._prompt}\n\nCOMPACT RETRY RULES:\n"
                        "Keep the output concise. Omit duplicate descriptions. "
                        "If English explanatory prose appears in evidence, rewrite only that prose in Turkish; "
                        "copy UI labels character-for-character. Do not add facts.\n\nSOURCE EVIDENCE:\n"
                        f"{json.dumps(evidence, ensure_ascii=False)}"
                    ),
                }],
                "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 8192},
                "keep_alive": "5m",
            },
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("Gemma compact response has no message content")
        try:
            result = NormalizedGuide.model_validate_json(content)
        except ValidationError as exc:
            message = str(exc)
            if "EOF" in message or "json_invalid" in message:
                raise ValueError("Gemma compact JSON was truncated") from exc
            raise
        return result.model_copy(update={"page_title": page.page_title, "source_url": page.source_url})

    def unload(self) -> None:
        """Release Gemma after the normalization phase."""
        response = self._client.post(
            f"{self._host}/api/generate",
            json={"model": self._model, "keep_alive": 0},
        )
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()
