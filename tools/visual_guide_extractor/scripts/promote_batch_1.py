"""Validate and promote approved Batch 1 guide candidates."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.knowledge.evidence import has_usable_evidence, is_placeholder_line  # noqa: E402
BATCH = ROOT / "work" / "visual_guide_extraction" / "batch_1"
KNOWLEDGE = ROOT / "knowledge_base" / "guides" / "antikor_v2"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_errors(path: Path, source_url: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if len(re.findall(r"^#\s+\S", text, re.MULTILINE)) != 1:
        errors.append("invalid_title")
    if source_url not in text:
        errors.append("missing_source_url")
    if len(text.strip()) < 200:
        errors.append("empty_or_short")
    sections = re.split(r"^##\s+.+?\s*$", text, flags=re.MULTILINE)[1:]
    if not any(has_usable_evidence(section) for section in sections):
        errors.append("missing_evidence_section")
    if any(is_placeholder_line(line) for line in text.splitlines()):
        errors.append("placeholder_evidence_present")
    if "\ufffd" in text or "\u00c3" in text or "\u00c2" in text:
        errors.append("corrupted_turkish_text")
    if "## Kaynak bilgisi" not in text:
        errors.append("malformed_markdown")
    return errors


def main() -> int:
    batch_manifest = json.loads((BATCH / "batch_manifest.json").read_text(encoding="utf-8"))
    guides = batch_manifest["guides"]
    if len(guides) != 46 or any(item["final_status"] != "approved_candidate" for item in guides):
        raise RuntimeError("Batch manifest must contain exactly 46 approved candidates")

    existing = sorted(KNOWLEDGE.rglob("*.md"))
    if len(existing) != 42:
        raise RuntimeError(f"Expected 42 existing guides, found {len(existing)}")
    before = {path.relative_to(KNOWLEDGE).as_posix(): checksum(path) for path in existing}
    existing_slugs = {path.stem.casefold() for path in existing}
    selected_slugs = [str(item["slug"]).casefold() for item in guides]
    if len(selected_slugs) != len(set(selected_slugs)):
        raise RuntimeError("Duplicate candidate slug")
    conflicts = sorted(existing_slugs & set(selected_slugs))
    if conflicts:
        raise RuntimeError(f"Candidate slug conflicts: {conflicts}")

    records: list[dict[str, object]] = []
    for item in guides:
        source = ROOT / item["candidate_path"]
        destination = KNOWLEDGE / item["category_key"] / f"{item['slug']}.md"
        errors = markdown_errors(source, item["source_url"])
        if errors:
            raise RuntimeError(f"Invalid candidate {item['slug']}: {errors}")
        status = "new"
        if destination.exists():
            if checksum(destination) != checksum(source):
                raise RuntimeError(f"Unexpected destination conflict: {destination}")
            status = "already_identical"
        records.append({
            "source_candidate_path": source.relative_to(ROOT).as_posix(),
            "destination_knowledge_base_path": destination.relative_to(ROOT).as_posix(),
            "title": item["title"], "category": item["category"], "slug": item["slug"],
            "source_url": item["source_url"], "candidate_checksum": checksum(source),
            "destination_status": status,
        })

    (BATCH / "promotion_manifest.json").write_text(
        json.dumps({"guide_count": len(records), "existing_checksums_before": before,
                    "guides": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for record in records:
        if record["destination_status"] == "new":
            source = ROOT / str(record["source_candidate_path"])
            destination = ROOT / str(record["destination_knowledge_base_path"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            record["destination_status"] = "promoted"

    after_existing = {relative: checksum(KNOWLEDGE / relative) for relative in before}
    if after_existing != before:
        raise RuntimeError("An existing promoted guide changed during promotion")
    promoted = sorted(KNOWLEDGE.rglob("*.md"))
    if len(promoted) != 88:
        raise RuntimeError(f"Expected 88 promoted guides, found {len(promoted)}")
    for record in records:
        destination = ROOT / str(record["destination_knowledge_base_path"])
        if checksum(destination) != record["candidate_checksum"]:
            raise RuntimeError(f"Checksum mismatch after promotion: {destination}")
    (BATCH / "promotion_manifest.json").write_text(
        json.dumps({"guide_count": len(records), "existing_checksums_before": before,
                    "existing_checksums_after": after_existing, "existing_guides_unchanged": True,
                    "final_antikor_guide_count": len(promoted), "guides": records},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"promoted": sum(x["destination_status"] == "promoted" for x in records),
                      "total": len(promoted), "existing_unchanged": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
