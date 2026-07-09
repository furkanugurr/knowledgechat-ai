"""Heading-aware text chunking without embedding generation."""

from dataclasses import dataclass

from app.knowledge.models import KnowledgeDocument


@dataclass(frozen=True, slots=True)
class ChunkDraft:
    """Intermediate chunk content before metadata is attached."""

    content: str
    section_title: str


class TextChunker:
    """Split parsed sections into overlapping character-based chunks."""

    def __init__(self, chunk_size: int, overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(self, document: KnowledgeDocument) -> list[ChunkDraft]:
        """Chunk each heading section independently and in source order."""
        chunks: list[ChunkDraft] = []
        for section in document.sections:
            chunks.extend(
                ChunkDraft(
                    content=content,
                    section_title=section.title,
                )
                for content in self._split_text(section.content)
            )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        """Split text near semantic boundaries with configured overlap."""
        stripped_text = text.strip()
        if not stripped_text:
            return []
        if len(stripped_text) <= self._chunk_size:
            return [stripped_text]

        chunks: list[str] = []
        start = 0
        while start < len(stripped_text):
            maximum_end = min(start + self._chunk_size, len(stripped_text))
            end = self._find_boundary(stripped_text, start, maximum_end)
            chunk = stripped_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(stripped_text):
                break

            next_start = max(end - self._overlap, start + 1)
            start = next_start

        return chunks

    def _find_boundary(self, text: str, start: int, maximum_end: int) -> int:
        """Prefer paragraph, line, then word boundaries near chunk end."""
        if maximum_end >= len(text):
            return len(text)

        minimum_boundary = start + self._chunk_size // 2
        for separator in ("\n\n", "\n", " "):
            boundary = text.rfind(
                separator,
                minimum_boundary,
                maximum_end + 1,
            )
            if boundary >= minimum_boundary:
                return boundary + len(separator)
        return maximum_end
