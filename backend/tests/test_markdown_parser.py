"""Tests for structure-preserving Markdown parsing."""

import tempfile
import unittest
from pathlib import Path

from app.knowledge.parser import MarkdownParser


class MarkdownParserTests(unittest.TestCase):
    """Verify headings and fenced code blocks remain intact."""

    def test_extracts_sections_without_parsing_headings_in_code(self) -> None:
        content = (
            "# Python Variables\n\n"
            "Variables bind names to values.\n\n"
            "```python\n"
            "# This is a comment, not a heading\n"
            "name = \"KnowledgeChat\"\n"
            "```\n\n"
            "## Naming\n\n"
            "Use descriptive names.\n"
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            topic_directory = root / "python"
            topic_directory.mkdir()
            document_path = topic_directory / "variables.md"
            document_path.write_text(content, encoding="utf-8")

            document = MarkdownParser(root, language="en").parse(document_path)

        self.assertEqual(document.document_name, "variables.md")
        self.assertEqual(document.relative_path, "python/variables.md")
        self.assertEqual(document.content, content)
        self.assertEqual(
            [section.title for section in document.sections],
            ["Python Variables", "Naming"],
        )
        self.assertIn(
            "# This is a comment, not a heading",
            document.sections[0].content,
        )
        self.assertIn("```python", document.sections[0].content)

    def test_rejects_files_outside_the_knowledge_base(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            root = directory / "knowledge_base"
            root.mkdir()
            outside_path = directory / "outside.md"
            outside_path.write_text("# Outside", encoding="utf-8")

            with self.assertRaises(ValueError):
                MarkdownParser(root).parse(outside_path)


if __name__ == "__main__":
    unittest.main()
