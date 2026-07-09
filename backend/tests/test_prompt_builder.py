"""Tests for managed prompt construction."""

import tempfile
import unittest
from pathlib import Path

from app.prompt.prompt_builder import PromptBuilder


class PromptBuilderTests(unittest.TestCase):
    """Verify prompt loading and final prompt formatting."""

    def test_builds_all_prompt_sections_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            system_prompt = directory / "system.txt"
            developer_prompt = directory / "developer.txt"
            system_prompt.write_text("System guidance", encoding="utf-8")
            developer_prompt.write_text(
                "Developer guidance",
                encoding="utf-8",
            )
            builder = PromptBuilder(system_prompt, developer_prompt)

            prompt = builder.build("User message")

        self.assertEqual(
            prompt,
            "SYSTEM PROMPT\nSystem guidance\n\n"
            "DEVELOPER PROMPT\nDeveloper guidance\n\n"
            "USER MESSAGE\nUser message",
        )

    def test_rejects_an_empty_prompt_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            system_prompt = directory / "system.txt"
            developer_prompt = directory / "developer.txt"
            system_prompt.write_text(" ", encoding="utf-8")
            developer_prompt.write_text(
                "Developer guidance",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                PromptBuilder(system_prompt, developer_prompt)


if __name__ == "__main__":
    unittest.main()
