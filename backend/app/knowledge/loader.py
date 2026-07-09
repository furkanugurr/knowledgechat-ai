"""Supported file discovery for the repository knowledge base."""

from collections.abc import Collection
from pathlib import Path


class KnowledgeLoader:
    """Recursively discover supported knowledge files."""

    def __init__(self, knowledge_base_path: Path) -> None:
        self._knowledge_base_path = knowledge_base_path.resolve()

    @property
    def knowledge_base_path(self) -> Path:
        """Return the resolved knowledge base root."""
        return self._knowledge_base_path

    def discover(
        self,
        supported_extensions: Collection[str] = ("md", "docx"),
    ) -> list[Path]:
        """Return sorted supported files contained by the knowledge base."""
        if not self._knowledge_base_path.is_dir():
            raise FileNotFoundError(
                f"Knowledge base directory not found: "
                f"{self._knowledge_base_path}"
            )

        normalized_extensions = {
            extension.lower().lstrip(".")
            for extension in supported_extensions
        }
        readme_path = self._knowledge_base_path / "README.md"
        discovered_paths = (
            path.resolve()
            for path in self._knowledge_base_path.rglob("*")
            if path.is_file()
            and path.suffix.lower().lstrip(".") in normalized_extensions
        )
        return sorted(
            path
            for path in discovered_paths
            if path != readme_path
            and path.is_relative_to(self._knowledge_base_path)
        )
