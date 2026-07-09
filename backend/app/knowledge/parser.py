"""Structure-preserving Markdown and Word knowledge parsers."""

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from zipfile import BadZipFile

from docx import Document as load_word_document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.knowledge.models import KnowledgeDocument, KnowledgeSection

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")
WORD_HEADING_PATTERN = re.compile(
    r"^(?:Heading|Başlık)\s*([1-6])$",
    re.IGNORECASE,
)


class DocumentParser(Protocol):
    """Parser capability required by the knowledge indexer."""

    def parse(self, path: Path) -> KnowledgeDocument:
        """Parse one supported knowledge document."""


class MarkdownParser:
    """Read Markdown files and preserve their semantic sections."""

    def __init__(
        self,
        knowledge_base_path: Path,
        language: str = "en",
    ) -> None:
        self._knowledge_base_path = knowledge_base_path.resolve()
        self._language = language

    def parse(self, path: Path) -> KnowledgeDocument:
        """Parse one knowledge Markdown file into a structured document."""
        resolved_path = path.resolve()
        self._validate_path(resolved_path)

        content = resolved_path.read_text(encoding="utf-8")
        file_stats = resolved_path.stat()
        created_timestamp = getattr(
            file_stats,
            "st_birthtime",
            file_stats.st_ctime,
        )

        return KnowledgeDocument(
            document_name=resolved_path.name,
            relative_path=resolved_path.relative_to(
                self._knowledge_base_path
            ).as_posix(),
            content=content,
            sections=self._extract_sections(
                content,
                fallback_title=self._title_from_path(resolved_path),
            ),
            language=self._language,
            created_at=datetime.fromtimestamp(created_timestamp, tz=UTC),
            updated_at=datetime.fromtimestamp(file_stats.st_mtime, tz=UTC),
        )

    def _validate_path(self, path: Path) -> None:
        """Validate that a parser input is a contained Markdown file."""
        if not path.is_file():
            raise FileNotFoundError(f"Knowledge document not found: {path}")
        if path.suffix.lower() != ".md":
            raise ValueError(f"Knowledge document must be Markdown: {path}")
        if not path.is_relative_to(self._knowledge_base_path):
            raise ValueError(
                "Knowledge document must be inside the knowledge base"
            )

    @staticmethod
    def _extract_sections(
        content: str,
        fallback_title: str,
    ) -> list[KnowledgeSection]:
        """Split Markdown at headings while preserving fenced code blocks."""
        sections: list[KnowledgeSection] = []
        current_title = fallback_title
        current_level: int | None = None
        current_lines: list[str] = []
        active_fence: str | None = None

        for line in content.splitlines(keepends=True):
            fence_match = FENCE_PATTERN.match(line)
            if fence_match:
                marker = fence_match.group(1)
                if active_fence is None:
                    active_fence = marker
                elif (
                    marker[0] == active_fence[0]
                    and len(marker) >= len(active_fence)
                    and not line[fence_match.end() :].strip()
                ):
                    active_fence = None
                current_lines.append(line)
                continue

            heading_match = (
                HEADING_PATTERN.match(line.rstrip("\r\n"))
                if active_fence is None
                else None
            )
            if heading_match:
                MarkdownParser._append_section(
                    sections,
                    current_title,
                    current_level,
                    current_lines,
                )
                current_title = heading_match.group(2).strip().rstrip("#").strip()
                current_level = len(heading_match.group(1))
                current_lines = [line]
                continue

            current_lines.append(line)

        MarkdownParser._append_section(
            sections,
            current_title,
            current_level,
            current_lines,
        )
        return sections

    @staticmethod
    def _append_section(
        sections: list[KnowledgeSection],
        title: str,
        level: int | None,
        lines: list[str],
    ) -> None:
        """Append one non-empty parsed section."""
        section_content = "".join(lines).strip()
        if section_content:
            sections.append(
                KnowledgeSection(
                    title=title,
                    level=level,
                    content=section_content,
                )
            )

    @staticmethod
    def _title_from_path(path: Path) -> str:
        """Create a readable fallback title from a file name."""
        return path.stem.replace("_", " ").replace("-", " ").title()


class WordParser:
    """Read DOCX files while preserving headings and table text."""

    def __init__(
        self,
        knowledge_base_path: Path,
        language: str = "en",
    ) -> None:
        self._knowledge_base_path = knowledge_base_path.resolve()
        self._language = language

    def parse(self, path: Path) -> KnowledgeDocument:
        """Parse one Word document into structured knowledge sections."""
        resolved_path = path.resolve()
        self._validate_path(resolved_path)

        try:
            word_document = load_word_document(resolved_path)
            content, sections = self._extract_content(
                word_document.iter_inner_content(),
                fallback_title=MarkdownParser._title_from_path(resolved_path),
            )
        except (BadZipFile, PackageNotFoundError, KeyError, ValueError) as exc:
            raise ValueError(
                f"Unable to read Word document: {resolved_path}"
            ) from exc

        if not content:
            raise ValueError(f"Word document contains no text: {resolved_path}")

        file_stats = resolved_path.stat()
        created_timestamp = getattr(
            file_stats,
            "st_birthtime",
            file_stats.st_ctime,
        )
        return KnowledgeDocument(
            document_name=resolved_path.name,
            relative_path=resolved_path.relative_to(
                self._knowledge_base_path
            ).as_posix(),
            content=content,
            sections=sections,
            language=self._language,
            created_at=datetime.fromtimestamp(created_timestamp, tz=UTC),
            updated_at=datetime.fromtimestamp(file_stats.st_mtime, tz=UTC),
        )

    def _validate_path(self, path: Path) -> None:
        """Validate that a parser input is a contained DOCX file."""
        if not path.is_file():
            raise FileNotFoundError(f"Knowledge document not found: {path}")
        if path.suffix.lower() != ".docx":
            raise ValueError(f"Knowledge document must be DOCX: {path}")
        if not path.is_relative_to(self._knowledge_base_path):
            raise ValueError(
                "Knowledge document must be inside the knowledge base"
            )

    @staticmethod
    def _extract_content(
        blocks: Iterable[Paragraph | Table],
        fallback_title: str,
    ) -> tuple[str, list[KnowledgeSection]]:
        """Convert ordered Word paragraphs and tables into sections."""
        sections: list[KnowledgeSection] = []
        all_content: list[str] = []
        current_title = fallback_title
        current_level: int | None = None
        current_lines: list[str] = []

        for block in blocks:
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                heading_level = WordParser._heading_level(block)
                if heading_level is not None:
                    WordParser._append_section(
                        sections,
                        current_title,
                        current_level,
                        current_lines,
                    )
                    current_title = text
                    current_level = heading_level
                    current_lines = [
                        f"{'#' * heading_level} {text}"
                    ]
                else:
                    current_lines.append(text)
                all_content.append(text)
                continue

            if isinstance(block, Table):
                table_lines = WordParser._table_lines(block)
                current_lines.extend(table_lines)
                all_content.extend(table_lines)

        WordParser._append_section(
            sections,
            current_title,
            current_level,
            current_lines,
        )
        return "\n\n".join(all_content), sections

    @staticmethod
    def _heading_level(paragraph: Paragraph) -> int | None:
        """Return the heading level represented by a Word style."""
        candidates = (
            getattr(paragraph.style, "name", None),
            getattr(paragraph.style, "style_id", None),
        )
        for candidate in candidates:
            if not candidate:
                continue
            match = WORD_HEADING_PATTERN.match(candidate)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _table_lines(table: Table) -> list[str]:
        """Return readable lines for non-empty Word table rows."""
        lines: list[str] = []
        for row in table.rows:
            values = [
                cell.text.strip().replace("\n", " ")
                for cell in row.cells
            ]
            if any(values):
                lines.append(" | ".join(values))
        return lines

    @staticmethod
    def _append_section(
        sections: list[KnowledgeSection],
        title: str,
        level: int | None,
        lines: list[str],
    ) -> None:
        """Append one non-empty Word section."""
        section_content = "\n\n".join(lines).strip()
        if section_content:
            sections.append(
                KnowledgeSection(
                    title=title,
                    level=level,
                    content=section_content,
                )
            )


class KnowledgeParser:
    """Dispatch knowledge files to their format-specific parser."""

    def __init__(
        self,
        knowledge_base_path: Path,
        language: str = "en",
    ) -> None:
        self._parsers: dict[str, DocumentParser] = {
            ".md": MarkdownParser(knowledge_base_path, language),
            ".docx": WordParser(knowledge_base_path, language),
        }

    def parse(self, path: Path) -> KnowledgeDocument:
        """Parse a document using its registered file format."""
        parser = self._parsers.get(path.suffix.lower())
        if parser is None:
            raise ValueError(
                f"Unsupported knowledge document format: {path.suffix}"
            )
        return parser.parse(path)
