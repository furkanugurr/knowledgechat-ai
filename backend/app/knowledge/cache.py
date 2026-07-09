"""Versioned and atomically persisted knowledge index cache."""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.knowledge.models import IndexedFile


class CacheError(Exception):
    """Base exception for knowledge index cache failures."""


class CorruptedCacheError(CacheError):
    """Raised when persisted cache data is invalid."""


class CachePersistenceError(CacheError):
    """Raised when cache data cannot be written."""


class IndexCacheState(BaseModel):
    """Extensible persisted state for incremental indexing."""

    version: int = Field(default=1, ge=1)
    manifest_hash: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    files: dict[str, IndexedFile] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class FileHasher:
    """Generate streaming SHA-256 hashes for knowledge files."""

    def __init__(self, block_size: int = 1024 * 1024) -> None:
        if block_size <= 0:
            raise ValueError("block_size must be greater than zero")
        self._block_size = block_size

    def sha256(self, path: Path) -> str:
        """Return the lowercase SHA-256 digest for one file."""
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            while block := file_handle.read(self._block_size):
                digest.update(block)
        return digest.hexdigest()


class IndexCache:
    """Load and atomically persist versioned incremental-index state."""

    def __init__(self, cache_path: Path) -> None:
        self._cache_path = cache_path.resolve()

    def load(self) -> IndexCacheState:
        """Return persisted state or a new state when no cache exists."""
        if not self._cache_path.exists():
            return IndexCacheState()

        try:
            payload = json.loads(
                self._cache_path.read_text(encoding="utf-8")
            )
            return IndexCacheState.model_validate(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
            raise CorruptedCacheError(
                f"Knowledge index cache is corrupted: {self._cache_path}"
            ) from exc

    def save(self, state: IndexCacheState) -> None:
        """Atomically persist cache state as readable JSON."""
        temporary_path = self._cache_path.with_suffix(
            f"{self._cache_path.suffix}.tmp"
        )
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                state.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self._cache_path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise CachePersistenceError(
                f"Unable to write knowledge index cache: {self._cache_path}"
            ) from exc
