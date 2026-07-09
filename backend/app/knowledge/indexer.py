"""Incremental orchestration for the complete knowledge pipeline."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.knowledge.cache import FileHasher, IndexCache, IndexCacheState
from app.knowledge.chunker import TextChunker
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.manifest import ManifestLoader
from app.knowledge.metadata import MetadataExtractor
from app.knowledge.models import (
    IndexedFile,
    IndexResult,
    IndexStatistics,
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.knowledge.parser import MarkdownParser

logger = logging.getLogger(__name__)

ParserFactory = Callable[[Path, str], MarkdownParser]
ChunkerFactory = Callable[[int, int], TextChunker]


class KnowledgeIndexingError(Exception):
    """Raised when a knowledge document cannot be indexed."""


class KnowledgeIndexer:
    """Orchestrate incremental knowledge loading and preparation."""

    def __init__(
        self,
        loader: KnowledgeLoader,
        manifest_loader: ManifestLoader,
        cache: IndexCache,
        metadata_extractor: MetadataExtractor | None = None,
        file_hasher: FileHasher | None = None,
        parser_factory: ParserFactory = MarkdownParser,
        chunker_factory: ChunkerFactory = TextChunker,
    ) -> None:
        self._loader = loader
        self._manifest_loader = manifest_loader
        self._cache = cache
        self._metadata_extractor = metadata_extractor or MetadataExtractor()
        self._file_hasher = file_hasher or FileHasher()
        self._parser_factory = parser_factory
        self._chunker_factory = chunker_factory

    def index(self) -> IndexResult:
        """Index new and changed documents and report incremental changes."""
        started_at = perf_counter()
        manifest = self._manifest_loader.load()
        cached_state = self._cache.load()
        manifest_hash = manifest.fingerprint()
        configuration_changed = cached_state.manifest_hash != manifest_hash

        logger.info("Scanning knowledge base")
        paths = self._loader.discover(manifest.supported_extensions)
        relative_paths = {
            self._relative_path(path)
            for path in paths
        }
        removed_files = sorted(set(cached_state.files) - relative_paths)
        next_files = {
            relative_path: indexed_file
            for relative_path, indexed_file in cached_state.files.items()
            if relative_path in relative_paths
        }

        parser = self._parser_factory(
            self._loader.knowledge_base_path,
            manifest.default_language,
        )
        chunker = self._chunker_factory(
            manifest.chunk_size,
            manifest.chunk_overlap,
        )
        indexed_files: list[IndexedFile] = []
        created_chunks: list[KnowledgeChunk] = []
        files_skipped = 0

        for path in paths:
            relative_path = self._relative_path(path)
            try:
                file_hash = self._file_hasher.sha256(path)
                cached_file = cached_state.files.get(relative_path)
                if (
                    not configuration_changed
                    and cached_file is not None
                    and cached_file.sha256 == file_hash
                ):
                    files_skipped += 1
                    continue

                logger.info("Reading knowledge file path=%s", relative_path)
                document = parser.parse(path)
                logger.info("Chunking knowledge file path=%s", relative_path)
                chunks = self._create_chunks(document, chunker)
            except (OSError, UnicodeError, ValueError) as exc:
                raise KnowledgeIndexingError(
                    f"Unable to index knowledge document: {relative_path}"
                ) from exc

            indexed_file = IndexedFile(
                relative_path=relative_path,
                sha256=file_hash,
                indexed_at=datetime.now(tz=UTC),
                chunk_count=len(chunks),
            )
            next_files[relative_path] = indexed_file
            indexed_files.append(indexed_file)
            created_chunks.extend(chunks)

        cache_changed = (
            configuration_changed
            or bool(indexed_files)
            or bool(removed_files)
        )
        if cache_changed:
            logger.info("Writing knowledge index cache")
            self._cache.save(
                IndexCacheState(
                    version=cached_state.version,
                    manifest_hash=manifest_hash,
                    files=next_files,
                )
            )

        statistics = IndexStatistics(
            files_scanned=len(paths),
            files_indexed=len(indexed_files),
            files_skipped=files_skipped,
            files_removed=len(removed_files),
            chunks_created=len(created_chunks),
            duration_seconds=perf_counter() - started_at,
        )
        logger.info(
            "Knowledge indexing completed scanned=%d indexed=%d skipped=%d "
            "removed=%d chunks=%d duration_seconds=%.3f",
            statistics.files_scanned,
            statistics.files_indexed,
            statistics.files_skipped,
            statistics.files_removed,
            statistics.chunks_created,
            statistics.duration_seconds,
        )
        return IndexResult(
            manifest_version=manifest.version,
            indexed_files=indexed_files,
            removed_files=removed_files,
            chunks=created_chunks,
            statistics=statistics,
        )

    def _relative_path(self, path: Path) -> str:
        """Return one normalized repository knowledge path."""
        return path.relative_to(
            self._loader.knowledge_base_path
        ).as_posix()

    def _create_chunks(
        self,
        document: KnowledgeDocument,
        chunker: TextChunker,
    ) -> list[KnowledgeChunk]:
        """Create metadata-enriched chunks for one parsed document."""
        drafts = chunker.split(document)
        return self._metadata_extractor.create_chunks(document, drafts)
