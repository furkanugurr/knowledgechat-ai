"""Build final prompts from managed prompt files and user messages."""

from collections.abc import Sequence
from pathlib import Path

from app.retrieval.models import RetrievedChunk


class PromptBuilder:
    """Combine system, developer, and user prompt sections."""

    def __init__(
        self,
        system_prompt_path: Path,
        developer_prompt_path: Path,
    ) -> None:
        self._system_prompt = self._read_prompt(system_prompt_path)
        self._developer_prompt = self._read_prompt(developer_prompt_path)

    @classmethod
    def from_defaults(cls) -> "PromptBuilder":
        """Create a builder using the application's default prompt files."""
        app_directory = Path(__file__).resolve().parent.parent
        return cls(
            system_prompt_path=(
                app_directory / "system_prompts" / "default.txt"
            ),
            developer_prompt_path=(
                app_directory / "developer_prompts" / "default.txt"
            ),
        )

    def build(
        self,
        user_message: str,
        retrieved_context: Sequence[RetrievedChunk] | None = None,
    ) -> str:
        """Return one final prompt with optional knowledge context."""
        sections = [
            f"SYSTEM PROMPT\n{self._system_prompt}",
            f"DEVELOPER PROMPT\n{self._developer_prompt}",
        ]
        if retrieved_context:
            sections.append(
                "KNOWLEDGE CONTEXT\n"
                f"{self._format_context(retrieved_context)}"
            )
        sections.append(f"USER MESSAGE\n{user_message}")
        return "\n\n".join(sections)

    @staticmethod
    def _format_context(
        retrieved_context: Sequence[RetrievedChunk],
    ) -> str:
        """Format retrieved chunks as clearly separated prompt sources."""
        sources = []
        for source_index, chunk in enumerate(
            retrieved_context,
            start=1,
        ):
            sources.append(
                "\n".join(
                    (
                        f"### Source {source_index}",
                        f"Document: {chunk.relative_path}",
                        f"Section: {chunk.section_title}",
                        "Content:",
                        chunk.chunk_text,
                    )
                )
            )
        return "\n\n".join(
            (
                "## Knowledge Context",
                *sources,
            )
        )

    @staticmethod
    def _read_prompt(path: Path) -> str:
        """Read and validate one managed prompt file."""
        prompt = path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise ValueError(f"Prompt file cannot be empty: {path}")
        return prompt
