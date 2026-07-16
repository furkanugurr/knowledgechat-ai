"""Validate promoted guides with the unchanged backend ingestion components."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.knowledge.chunker import TextChunker
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.manifest import ManifestLoader
from app.knowledge.metadata import MetadataExtractor
from app.knowledge.parser import KnowledgeParser


def run() -> dict[str, object]:
    base = ROOT / "knowledge_base"
    manifest = ManifestLoader(base / "manifest.yaml").load()
    paths = KnowledgeLoader(base).discover(manifest.supported_extensions)
    parser = KnowledgeParser(base, manifest.default_language)
    chunker = TextChunker(manifest.chunk_size, manifest.chunk_overlap)
    metadata = MetadataExtractor()
    promoted = [path for path in paths if path.relative_to(base).as_posix().startswith("guides/antikor_v2/")]
    errors: list[str] = []
    empty_chunks = 0
    oversized_chunks = 0
    promoted_chunks = 0
    languages: set[str] = set()
    relative_paths: list[str] = []
    docx_parsed = markdown_parsed = 0
    for path in paths:
        try:
            document = parser.parse(path)
            drafts = chunker.split(document)
            chunks = metadata.create_chunks(document, drafts)
            empty_chunks += sum(not chunk.content.strip() for chunk in chunks)
            oversized_chunks += sum(len(chunk.content) > manifest.chunk_size for chunk in chunks)
            languages.add(document.language)
            if path.suffix.lower() == ".docx":
                docx_parsed += 1
            elif path.suffix.lower() == ".md":
                markdown_parsed += 1
            if path in promoted:
                promoted_chunks += len(chunks)
                relative_paths.append(document.relative_path)
        except Exception as exc:
            errors.append(f"{path.relative_to(base).as_posix()}: {type(exc).__name__}: {exc}")
    report = {
        "all_files_discovered": len(paths),
        "promoted_files_discovered": len(promoted),
        "docx_files_parsed": docx_parsed,
        "markdown_files_parsed": markdown_parsed,
        "promoted_chunks_created": promoted_chunks,
        "empty_chunk_count": empty_chunks,
        "oversized_chunk_count": oversized_chunks,
        "manifest_chunk_size": manifest.chunk_size,
        "manifest_chunk_overlap": manifest.chunk_overlap,
        "languages": sorted(languages),
        "all_promoted_paths_valid": all(path.startswith("guides/antikor_v2/") for path in relative_paths),
        "errors": errors,
        "compatible": len(promoted) == 42 and not errors and not empty_chunks and not oversized_chunks,
    }
    destination = ROOT / "work" / "visual_guide_extraction" / "sprint20" / "compatibility_report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
