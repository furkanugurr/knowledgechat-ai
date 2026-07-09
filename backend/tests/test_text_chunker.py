"""Tests for heading-aware text chunking."""

import unittest
from datetime import UTC, datetime

from app.knowledge.chunker import TextChunker
from app.knowledge.models import KnowledgeDocument, KnowledgeSection


def create_document(sections: list[KnowledgeSection]) -> KnowledgeDocument:
    """Create a parsed document fixture."""
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return KnowledgeDocument(
        document_name="example.md",
        relative_path="python/example.md",
        content="\n\n".join(section.content for section in sections),
        sections=sections,
        language="en",
        created_at=timestamp,
        updated_at=timestamp,
    )


class TextChunkerTests(unittest.TestCase):
    """Verify chunk boundaries, overlap, and section ownership."""

    def test_preserves_heading_boundaries(self) -> None:
        document = create_document(
            [
                KnowledgeSection(
                    title="First",
                    level=1,
                    content="A" * 30,
                ),
                KnowledgeSection(
                    title="Second",
                    level=2,
                    content="B" * 30,
                ),
            ]
        )

        chunks = TextChunker(chunk_size=12, overlap=2).split(document)

        self.assertEqual(
            [chunk.section_title for chunk in chunks],
            ["First", "First", "First", "Second", "Second", "Second"],
        )
        self.assertTrue(
            all(
                set(chunk.content) <= {"A"}
                for chunk in chunks
                if chunk.section_title == "First"
            )
        )
        self.assertTrue(
            all(
                set(chunk.content) <= {"B"}
                for chunk in chunks
                if chunk.section_title == "Second"
            )
        )

    def test_applies_character_overlap(self) -> None:
        document = create_document(
            [
                KnowledgeSection(
                    title="Alphabet",
                    level=1,
                    content="abcdefghijklmnopqrstuvwxyz",
                )
            ]
        )

        chunks = TextChunker(chunk_size=10, overlap=3).split(document)

        self.assertEqual(chunks[0].content[-3:], chunks[1].content[:3])

    def test_rejects_overlap_equal_to_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            TextChunker(chunk_size=100, overlap=100)


if __name__ == "__main__":
    unittest.main()
