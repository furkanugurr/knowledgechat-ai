"""Knowledge chunk metadata construction."""

from collections.abc import Sequence
from pathlib import Path

from app.knowledge.chunker import ChunkDraft
from app.knowledge.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeMetadata,
)


class MetadataExtractor:
    """Attach document and section metadata to every chunk draft."""

    def create_chunks(
        self,
        document: KnowledgeDocument,
        chunks: Sequence[ChunkDraft],
    ) -> list[KnowledgeChunk]:
        """Return finalized chunks with zero-based ordering metadata."""
        total_chunks = len(chunks)
        return [
            KnowledgeChunk(
                content=chunk.content,
                metadata=KnowledgeMetadata(
                    document_name=document.document_name,
                    relative_path=document.relative_path,
                    section_title=chunk.section_title,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    language=document.language,
                    source_type=self._source_type(document.relative_path),
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                ),
            )
            for chunk_index, chunk in enumerate(chunks)
        ]

    @staticmethod
    def _source_type(relative_path: str) -> str:
        """Classify repository sources without a hand-maintained registry."""
        suffix = Path(relative_path).suffix.casefold()
        if suffix == ".docx":
            return "product_document"
        if relative_path.replace("\\", "/").startswith("guides/"):
            return "guide"
        return "knowledge_document"
