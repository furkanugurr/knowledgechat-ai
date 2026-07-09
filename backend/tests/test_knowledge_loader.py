"""Tests for knowledge base document discovery."""

import tempfile
import unittest
from pathlib import Path

from app.knowledge.loader import KnowledgeLoader


class KnowledgeLoaderTests(unittest.TestCase):
    """Verify recursive, contained supported-file discovery."""

    def test_discovers_sorted_supported_files_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            nested = root / "python" / "advanced"
            nested.mkdir(parents=True)
            (root / "README.md").write_text("Guide", encoding="utf-8")
            first = root / "python" / "basics.md"
            second = nested / "decorators.MD"
            third = nested / "handbook.docx"
            ignored = nested / "notes.txt"
            first.write_text("# Basics", encoding="utf-8")
            second.write_text("# Decorators", encoding="utf-8")
            third.write_text("Word placeholder", encoding="utf-8")
            ignored.write_text("Not Markdown", encoding="utf-8")

            discovered = KnowledgeLoader(root).discover()

        self.assertEqual(
            discovered,
            sorted([first.resolve(), second.resolve(), third.resolve()]),
        )

    def test_rejects_a_missing_knowledge_base(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing"

            with self.assertRaises(FileNotFoundError):
                KnowledgeLoader(missing_path).discover()


if __name__ == "__main__":
    unittest.main()
