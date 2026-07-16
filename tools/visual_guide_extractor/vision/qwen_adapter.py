"""Ollama adapter for strict Qwen2.5-VL JSON extraction."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from tools.visual_guide_extractor.schemas.extraction import VisionExtraction


class QwenVisionAdapter:
    """Analyze one screenshot without allowing free-form Markdown output."""

    def __init__(
        self,
        host: str,
        model: str,
        prompt_path: Path,
        timeout: float,
        context_window: int = 8192,
        client: httpx.Client | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._prompt = prompt_path.read_text(encoding="utf-8").strip()
        self._timeout = timeout
        self._context_window = context_window
        self._client = client or httpx.Client(timeout=timeout)

    def analyze(
        self,
        image_path: Path,
        page_title: str,
        image_index: int,
        html_context: str,
        extraction_metadata: dict[str, object] | None = None,
    ) -> VisionExtraction:
        """Return schema-validated observations for one guide screenshot."""
        request_prompt = (
            f"{self._prompt}\n\n"
            f"PAGE TITLE: {page_title}\n"
            f"IMAGE INDEX: {image_index}\n"
            "EXISTING EXTRACTION METADATA:\n"
            f"{json.dumps(extraction_metadata or {}, ensure_ascii=False)}\n"
            "AUTHORITATIVE HTML CONTEXT:\n"
            f"{html_context[:12000]}"
        )
        image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        messages: list[dict[str, object]] = [
            {
                "role": "user",
                "content": request_prompt,
                "images": [image_data],
            }
        ]
        last_error: ValueError | None = None
        for attempt in range(2):
            response = self._client.post(
                f"{self._host}/api/chat",
                json={
                "model": self._model,
                "stream": False,
                "format": VisionExtraction.model_json_schema(),
                "messages": messages,
                "options": {
                    "temperature": 0,
                    "num_ctx": self._context_window,
                },
                "keep_alive": "5m",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = response.text[:1000]
                raise ValueError(
                    f"Ollama vision request failed ({response.status_code}): {detail}"
                ) from exc
            payload = response.json()
            content = payload.get("message", {}).get("content")
            if not isinstance(content, str):
                raise ValueError("Ollama vision response has no message content")
            try:
                return self.parse_content(content, page_title, image_index)
            except ValueError as exc:
                last_error = exc
                if attempt == 0:
                    messages.extend(
                        [
                            {"role": "assistant", "content": content},
                            {
                                "role": "user",
                                "content": (
                                    "Önceki JSON şema doğrulamasından geçmedi. "
                                    f"Hata: {exc}. Yalnızca düzeltilmiş JSON döndür. "
                                    "Aynı etiketi controls ve fields içinde tekrarlama; "
                                    "kind değerlerini izin verilen seçeneklerden seç."
                                ),
                            },
                        ]
                    )
        if last_error is None:
            raise ValueError("Qwen result could not be validated")
        raise last_error

    @staticmethod
    def parse_content(
        content: str,
        page_title: str,
        image_index: int,
    ) -> VisionExtraction:
        """Parse and validate Qwen JSON without accepting free text."""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Qwen returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Qwen JSON response must be an object")
        parsed["page_title"] = page_title
        parsed["image_index"] = image_index
        QwenVisionAdapter._remove_empty_and_duplicate_items(parsed)
        QwenVisionAdapter._prefer_fields_for_duplicate_labels(parsed)
        QwenVisionAdapter._remove_empty_and_duplicate_items(parsed)
        try:
            return VisionExtraction.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError(
                f"Qwen JSON response does not match the schema: {exc}"
            ) from exc

    @staticmethod
    def _remove_empty_and_duplicate_items(payload: dict[str, object]) -> None:
        """Clean harmless model formatting noise without adding observations."""
        for key in ("ordered_steps", "warnings", "uncertainties"):
            values = payload.get(key)
            if not isinstance(values, list):
                continue
            seen: set[str] = set()
            cleaned: list[str] = []
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    continue
                marker = value.strip().casefold()
                if marker not in seen:
                    seen.add(marker)
                    cleaned.append(value.strip())
            payload[key] = cleaned
        for key in ("controls", "fields"):
            values = payload.get(key)
            if not isinstance(values, list):
                continue
            seen: set[str] = set()
            cleaned: list[object] = []
            for value in values:
                if not isinstance(value, dict):
                    cleaned.append(value)
                    continue
                marker = str(value.get("name", "")).strip().casefold()
                if marker and marker in seen:
                    continue
                if marker:
                    seen.add(marker)
                cleaned.append(value)
            payload[key] = cleaned

    @staticmethod
    def _prefer_fields_for_duplicate_labels(payload: dict[str, object]) -> None:
        """Remove duplicate controls when the same label is a config field."""
        raw_controls = payload.get("controls")
        raw_fields = payload.get("fields")
        if not isinstance(raw_controls, list) or not isinstance(raw_fields, list):
            return
        field_names = {
            str(item.get("name", "")).strip().casefold()
            for item in raw_fields
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        }
        removed_names: list[str] = []
        filtered_controls: list[object] = []
        for item in raw_controls:
            if not isinstance(item, dict):
                filtered_controls.append(item)
                continue
            name = str(item.get("name", "")).strip()
            if name and name.casefold() in field_names:
                removed_names.append(name)
                continue
            filtered_controls.append(item)
        if not removed_names:
            return
        payload["controls"] = filtered_controls
        uncertainties = payload.setdefault("uncertainties", [])
        if isinstance(uncertainties, list):
            uncertainties.append(
                "Model aynı etiketi control ve field olarak sınıflandırdı; "
                "yapılandırma değeri olan field korundu: "
                + ", ".join(sorted(set(removed_names)))
            )

    def unload(self) -> None:
        """Release the model before Gemma is loaded on limited VRAM."""
        response = self._client.post(
            f"{self._host}/api/generate",
            json={"model": self._model, "keep_alive": 0},
        )
        response.raise_for_status()

    def close(self) -> None:
        """Close the managed HTTP client."""
        self._client.close()
