"""Validate and promote the 39 approved Batch 2 guide candidates."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.evidence import has_usable_evidence, is_placeholder_line

BATCH = ROOT / "work" / "visual_guide_extraction" / "batch_2"
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
    if "�" in text or "Ã" in text or "Â" in text:
        errors.append("corrupted_turkish_text")
    if "## Kaynak bilgisi" not in text or text.count("```") % 2:
        errors.append("malformed_markdown")
    return errors


def main() -> int:
    batch_manifest = json.loads((BATCH / "batch_manifest.json").read_text(encoding="utf-8"))
    guides = batch_manifest["guides"]
    if len(guides) != 39 or any(item["final_status"] != "approved_candidate" for item in guides):
        raise RuntimeError("Batch manifest must contain exactly 39 approved candidates")

    existing = sorted(KNOWLEDGE.rglob("*.md"))
    if len(existing) != 88:
        raise RuntimeError(f"Expected 88 existing guides, found {len(existing)}")
    before = {path.relative_to(KNOWLEDGE).as_posix(): checksum(path) for path in existing}
    selected_slugs = [str(item["slug"]).casefold() for item in guides]
    if len(selected_slugs) != len(set(selected_slugs)):
        raise RuntimeError("Duplicate candidate slug")
    destinations = [f"{item['category_key']}/{item['slug']}.md".casefold() for item in guides]
    if len(destinations) != len(set(destinations)):
        raise RuntimeError("Duplicate candidate relative path")

    records: list[dict[str, object]] = []
    for item in guides:
        source = ROOT / str(item["candidate_path"])
        destination = KNOWLEDGE / str(item["category_key"]) / f"{item['slug']}.md"
        errors = markdown_errors(source, str(item["source_url"]))
        if errors:
            raise RuntimeError(f"Invalid candidate {item['slug']}: {errors}")
        if destination.exists():
            raise RuntimeError(f"Destination conflict; refusing to overwrite: {destination}")
        records.append({
            "source_candidate_path": source.relative_to(ROOT).as_posix(),
            "destination_knowledge_base_path": destination.relative_to(ROOT).as_posix(),
            "title": item["title"], "category": item["category"],
            "category_key": item["category_key"], "slug": item["slug"],
            "source_url": item["source_url"], "candidate_checksum": checksum(source),
            "destination_status": "new",
        })

    payload = {
        "guide_count": len(records), "existing_guide_count": len(existing),
        "existing_checksums_before": before, "guides": records,
    }
    (BATCH / "promotion_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for record in records:
        source = ROOT / str(record["source_candidate_path"])
        destination = ROOT / str(record["destination_knowledge_base_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        record["destination_status"] = "promoted"

    after = {relative: checksum(KNOWLEDGE / relative) for relative in before}
    if after != before:
        raise RuntimeError("An existing promoted guide changed during promotion")
    promoted = sorted(KNOWLEDGE.rglob("*.md"))
    if len(promoted) != 127:
        raise RuntimeError(f"Expected 127 promoted guides, found {len(promoted)}")
    all_slugs = [path.stem.casefold() for path in promoted]
    if len(all_slugs) != len(set(all_slugs)):
        raise RuntimeError("Duplicate promoted guide slug")
    all_errors: dict[str, list[str]] = {}
    for path in promoted:
        text = path.read_text(encoding="utf-8")
        source_match = re.search(r"^-\s+Sayfa:\s+(\S+)", text, re.MULTILINE)
        errors = markdown_errors(path, source_match.group(1) if source_match else "__missing__")
        if errors:
            all_errors[path.relative_to(KNOWLEDGE).as_posix()] = errors
    if all_errors:
        raise RuntimeError(f"Promoted Markdown validation failed: {all_errors}")
    for record in records:
        destination = ROOT / str(record["destination_knowledge_base_path"])
        if checksum(destination) != record["candidate_checksum"]:
            raise RuntimeError(f"Checksum mismatch: {destination}")

    payload.update({
        "existing_checksums_after": after, "existing_guides_unchanged": True,
        "final_antikor_guide_count": len(promoted), "all_promoted_markdown_valid": True,
        "guides": records,
    })
    (BATCH / "promotion_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"promoted": 39, "total": 127, "existing_unchanged": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
