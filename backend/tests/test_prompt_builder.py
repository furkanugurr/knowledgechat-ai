"""Tests for managed prompt construction."""

import tempfile
import unittest
from pathlib import Path

from app.prompt.prompt_builder import PromptBuilder
from app.retrieval.models import RetrievedChunk


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

        self.assertTrue(prompt.startswith(
            "SYSTEM PROMPT\nSystem guidance\n\n"
            "DEVELOPER PROMPT\nDeveloper guidance\n\n"
            "ANSWER FOCUS CONTRACT\n"
        ))
        self.assertTrue(prompt.endswith("USER MESSAGE\nUser message"))

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

    def test_builds_prompt_with_retrieved_context(self) -> None:
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
            context = [
                RetrievedChunk(
                    chunk_text="Classes define object behavior.",
                    similarity_score=0.9,
                    document_name="oop.md",
                    relative_path="python/oop.md",
                    section_title="Classes",
                    chunk_index=0,
                    language="en",
                )
            ]

            prompt = builder.build("Explain classes.", context)

        self.assertIn("KNOWLEDGE CONTEXT", prompt)
        self.assertIn("## Knowledge Context", prompt)
        self.assertIn("### Source 1", prompt)
        self.assertIn("Document: python/oop.md", prompt)
        self.assertIn("Section: Classes", prompt)
        self.assertIn("Classes define object behavior.", prompt)
        self.assertLess(
            prompt.index("KNOWLEDGE CONTEXT"),
            prompt.index("USER MESSAGE"),
        )

    def test_marks_arrow_workflow_as_sufficient_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            system_prompt = directory / "system.txt"
            developer_prompt = directory / "developer.txt"
            system_prompt.write_text("System guidance", encoding="utf-8")
            developer_prompt.write_text("Developer guidance", encoding="utf-8")
            builder = PromptBuilder(system_prompt, developer_prompt)
            context = [
                RetrievedChunk(
                    chunk_text="Menü -> Arayüzü seç -> Kaydet",
                    similarity_score=0.9,
                    document_name="guide.md",
                    relative_path="guide.md",
                    section_title="Menü yolu",
                    chunk_index=1,
                    language="tr",
                )
            ]

            prompt = builder.build("Nasıl yapılır?", context)

        self.assertIn("EVIDENCE SUFFICIENCY NOTE", prompt)
        self.assertIn("sufficient procedural evidence", prompt)
        self.assertIn("ANSWER FOCUS CONTRACT", prompt)
        self.assertIn("For a Turkish question, never switch to English", prompt)

    def test_default_prompt_preserves_user_question_language(self) -> None:
        prompt = PromptBuilder.from_defaults().build("Python nedir?")

        self.assertIn(
            "Always answer in the same language as the user's question.",
            prompt,
        )
        self.assertIn("If the user asks in Turkish, answer in Turkish.", prompt)

    def test_default_prompt_requires_a_grounded_detailed_answer(self) -> None:
        prompt = PromptBuilder.from_defaults().build("Antikor nedir?")

        self.assertIn(
            "Answer the user's question yourself by synthesizing",
            prompt,
        )
        self.assertIn("Answer only the exact entity and action", prompt)
        self.assertIn("If the exact requested instruction is unavailable", prompt)
        self.assertIn("Do not add generic background", prompt)
        self.assertIn("Preserve detailed answers for sufficient evidence", prompt)
        self.assertIn("Do not invent missing details", prompt)
        self.assertIn(
            "Prefer a direct explanation followed by relevant details",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
