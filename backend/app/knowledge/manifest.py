"""Validated knowledge indexing manifest loading."""

import hashlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ManifestError(Exception):
    """Raised when the knowledge manifest cannot be loaded or validated."""


class KnowledgeManifest(BaseModel):
    """Dynamic configuration for the knowledge indexing pipeline."""

    version: int = Field(ge=1)
    default_language: str = Field(min_length=2)
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)
    supported_extensions: list[str] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("supported_extensions")
    @classmethod
    def normalize_extensions(cls, values: list[str]) -> list[str]:
        """Normalize, validate, and deterministically order extensions."""
        normalized = sorted(
            {
                value.strip().lower().lstrip(".")
                for value in values
                if value.strip()
            }
        )
        if not normalized:
            raise ValueError("supported_extensions cannot be empty")

        unsupported = set(normalized) - {"docx", "md"}
        if unsupported:
            raise ValueError(
                "Unsupported knowledge extensions: "
                f"{', '.join(sorted(unsupported))}"
            )
        return normalized

    @model_validator(mode="after")
    def validate_chunk_configuration(self) -> "KnowledgeManifest":
        """Ensure overlap cannot consume an entire chunk."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self

    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 hash of indexing configuration."""
        serialized = self.model_dump_json()
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ManifestLoader:
    """Load a knowledge manifest from YAML."""

    def __init__(self, manifest_path: Path) -> None:
        self._manifest_path = manifest_path.resolve()

    def load(self) -> KnowledgeManifest:
        """Read and validate the configured YAML manifest."""
        try:
            raw_manifest: Any = yaml.safe_load(
                self._manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise ManifestError(
                f"Unable to read knowledge manifest: {self._manifest_path}"
            ) from exc

        if not isinstance(raw_manifest, dict):
            raise ManifestError("Knowledge manifest must contain a mapping")

        try:
            return KnowledgeManifest.model_validate(raw_manifest)
        except ValueError as exc:
            raise ManifestError(
                f"Invalid knowledge manifest {self._manifest_path}: {exc}"
            ) from exc
