"""Tests for knowledge file hashing and cache persistence."""

import hashlib
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from app.knowledge.cache import (
    CorruptedCacheError,
    FileHasher,
    IndexCache,
    IndexCacheState,
)
from app.knowledge.models import IndexedFile


class FileHasherTests(unittest.TestCase):
    """Verify deterministic streaming SHA-256 generation."""

    def test_generates_sha256_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "document.md"
            content = b"# Knowledge"
            path.write_bytes(content)

            file_hash = FileHasher(block_size=4).sha256(path)

        self.assertEqual(file_hash, hashlib.sha256(content).hexdigest())


class IndexCacheTests(unittest.TestCase):
    """Verify versioned cache persistence and corruption handling."""

    def test_persists_and_loads_cache_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache_path = Path(temporary_directory) / "index_cache.json"
            cache = IndexCache(cache_path)
            indexed_at = datetime(2026, 1, 1, tzinfo=UTC)
            indexed_file = IndexedFile(
                relative_path="python/oop.md",
                sha256="a" * 64,
                indexed_at=indexed_at,
                chunk_count=3,
            )
            state = IndexCacheState(
                manifest_hash="b" * 64,
                files={"python/oop.md": indexed_file},
            )

            cache.save(state)
            loaded_state = cache.load()

        self.assertEqual(loaded_state, state)

    def test_returns_empty_state_when_cache_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache = IndexCache(
                Path(temporary_directory) / "missing.json"
            )

            state = cache.load()

        self.assertEqual(state.files, {})
        self.assertIsNone(state.manifest_hash)

    def test_rejects_corrupted_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache_path = Path(temporary_directory) / "index_cache.json"
            cache_path.write_text("{invalid", encoding="utf-8")

            with self.assertRaises(CorruptedCacheError):
                IndexCache(cache_path).load()


if __name__ == "__main__":
    unittest.main()
