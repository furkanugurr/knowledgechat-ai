"""Persistence for validated visual extraction results."""

from pathlib import Path

from tools.visual_guide_extractor.schemas.extraction import VisionExtraction


class VisionResultStore:
    """Persist only schema-validated Qwen results in page subdirectories."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def save(self, page_key: str, result: VisionExtraction) -> Path:
        """Save one result atomically enough for the local PoC workflow."""
        directory = self._root / page_key
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"image-{result.image_index}.json"
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(
            result.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
        return destination
