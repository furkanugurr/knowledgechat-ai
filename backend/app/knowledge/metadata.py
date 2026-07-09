"""Knowledge chunk metadata construction."""

from collections.abc import Sequence

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
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                ),
            )
            for chunk_index, chunk in enumerate(chunks)
        ]
