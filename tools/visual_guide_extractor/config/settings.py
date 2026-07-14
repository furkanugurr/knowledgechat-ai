"""Environment-backed settings for the visual guide extraction PoC."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExtractionSettings:
    """Runtime settings kept separate from the KnowledgeChat application."""

    repository_root: Path
    work_root: Path
    ollama_host: str
    vision_model: str
    normalization_model: str
    request_timeout: float
    vision_context_window: int
    run_vision: bool
    force_vision: bool
    force_normalization: bool

    @classmethod
    def from_environment(cls) -> "ExtractionSettings":
        """Build settings from environment variables and safe PoC defaults."""
        repository_root = Path(__file__).resolve().parents[3]
        return cls(
            repository_root=repository_root,
            work_root=repository_root / "work" / "visual_guide_extraction",
            ollama_host=os.getenv("VISUAL_GUIDE_OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
            vision_model=os.getenv("VISUAL_GUIDE_VISION_MODEL", "qwen2.5vl:7b"),
            normalization_model=os.getenv(
                "VISUAL_GUIDE_NORMALIZATION_MODEL", "gemma3:12b"
            ),
            request_timeout=float(os.getenv("VISUAL_GUIDE_REQUEST_TIMEOUT", "120")),
            vision_context_window=int(
                os.getenv("VISUAL_GUIDE_VISION_CONTEXT_WINDOW", "8192")
            ),
            run_vision=os.getenv("VISUAL_GUIDE_RUN_VISION", "false").lower()
            in {"1", "true", "yes"},
            force_vision=os.getenv("VISUAL_GUIDE_FORCE_VISION", "false").lower()
            in {"1", "true", "yes"},
            force_normalization=os.getenv(
                "VISUAL_GUIDE_FORCE_NORMALIZATION", "false"
            ).lower()
            in {"1", "true", "yes"},
        )

    def ensure_work_directories(self) -> None:
        """Create only the approved temporary output directories."""
        for name in (
            "pages",
            "images",
            "vision_results",
            "normalized_results",
            "approved_drafts",
            "reports",
        ):
            (self.work_root / name).mkdir(parents=True, exist_ok=True)
