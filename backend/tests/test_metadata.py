"""Tests for knowledge chunk metadata construction."""

import unittest
from datetime import UTC, datetime

from app.knowledge.chunker import ChunkDraft
from app.knowledge.metadata import MetadataExtractor
from app.knowledge.models import KnowledgeDocument, KnowledgeSection


class MetadataExtractorTests(unittest.TestCase):
    """Verify required document metadata is attached to every chunk."""

    def test_creates_complete_metadata_for_each_chunk(self) -> None:
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        updated_at = datetime(2026, 2, 1, tzinfo=UTC)
        document = KnowledgeDocument(
            document_name="routing.md",
            relative_path="fastapi/routing.md",
            content="# Routing",
            sections=[
                KnowledgeSection(
                    title="Routing",
                    level=1,
                    content="# Routing",
                )
            ],
            language="en",
            created_at=created_at,
            updated_at=updated_at,
        )
        drafts = [
            ChunkDraft(content="First chunk", section_title="Routing"),
            ChunkDraft(content="Second chunk", section_title="Path parameters"),
        ]

        chunks = MetadataExtractor().create_chunks(document, drafts)

        self.assertEqual(len(chunks), 2)
        for index, chunk in enumerate(chunks):
            metadata = chunk.metadata
            self.assertEqual(metadata.document_name, "routing.md")
            self.assertEqual(metadata.relative_path, "fastapi/routing.md")
            self.assertEqual(metadata.chunk_index, index)
            self.assertEqual(metadata.total_chunks, 2)
            self.assertEqual(metadata.language, "en")
            self.assertEqual(metadata.created_at, created_at)
            self.assertEqual(metadata.updated_at, updated_at)
        self.assertEqual(chunks[1].metadata.section_title, "Path parameters")
        self.assertEqual(chunks[1].metadata.source_type, "knowledge_document")

    def test_marks_docx_sources_as_product_documents(self) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        document = KnowledgeDocument(
            document_name="Antikor.docx", relative_path="Antikor.docx",
            content="Antikor", sections=[], language="tr",
            created_at=timestamp, updated_at=timestamp,
        )
        chunks = MetadataExtractor().create_chunks(
            document, [ChunkDraft(content="Antikor", section_title="Giriş")]
        )
        self.assertEqual(chunks[0].metadata.source_type, "product_document")


if __name__ == "__main__":
    unittest.main()
