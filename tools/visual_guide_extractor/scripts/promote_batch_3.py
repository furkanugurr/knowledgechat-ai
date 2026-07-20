"""Validate and promote the 38 approved final Batch 3 candidates."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from tools.visual_guide_extractor.scripts.promote_batch_2 import checksum, markdown_errors

BATCH = ROOT / "work" / "visual_guide_extraction" / "batch_3"
KNOWLEDGE = ROOT / "knowledge_base" / "guides" / "antikor_v2"


def main() -> int:
    manifest = json.loads((BATCH / "batch_manifest.json").read_text(encoding="utf-8"))
    guides = manifest["guides"]
    if len(guides) != 38 or any(item["final_status"] != "approved_candidate" for item in guides):
        raise RuntimeError("Batch 3 must contain exactly 38 approved candidates")
    existing = sorted(KNOWLEDGE.rglob("*.md"))
    if len(existing) != 127:
        raise RuntimeError(f"Expected 127 existing guides, found {len(existing)}")
    before = {path.relative_to(KNOWLEDGE).as_posix(): checksum(path) for path in existing}
    existing_slugs = {path.stem.casefold() for path in existing}
    selected_slugs = [str(item["slug"]).casefold() for item in guides]
    if len(selected_slugs) != len(set(selected_slugs)):
        raise RuntimeError("Duplicate candidate slug")
    conflicts = sorted(existing_slugs & set(selected_slugs))
    if conflicts:
        raise RuntimeError(f"Candidate slug conflicts: {conflicts}")
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
            raise RuntimeError(f"Destination conflict; refusing overwrite: {destination}")
        records.append({
            "source_candidate_path": source.relative_to(ROOT).as_posix(),
            "destination_knowledge_base_path": destination.relative_to(ROOT).as_posix(),
            "title": item["title"], "category": item["category"],
            "category_key": item["category_key"], "slug": item["slug"],
            "source_url": item["source_url"], "candidate_checksum": checksum(source),
            "destination_status": "new",
        })
    payload: dict[str, object] = {
        "guide_count": 38, "existing_guide_count": 127,
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
        raise RuntimeError("A previous promoted guide changed")
    promoted = sorted(KNOWLEDGE.rglob("*.md"))
    if len(promoted) != 165:
        raise RuntimeError(f"Expected 165 promoted guides, found {len(promoted)}")
    slugs = [path.stem.casefold() for path in promoted]
    if len(slugs) != len(set(slugs)):
        raise RuntimeError("Duplicate promoted guide slug")
    invalid: dict[str, list[str]] = {}
    for path in promoted:
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^-\s+Sayfa:\s+(\S+)", text, re.MULTILINE)
        errors = markdown_errors(path, match.group(1) if match else "__missing__")
        if errors:
            invalid[path.relative_to(KNOWLEDGE).as_posix()] = errors
    if invalid:
        raise RuntimeError(f"Promoted Markdown validation failed: {invalid}")
    for record in records:
        destination = ROOT / str(record["destination_knowledge_base_path"])
        if checksum(destination) != record["candidate_checksum"]:
            raise RuntimeError(f"Checksum mismatch: {destination}")
    payload.update({
        "existing_checksums_after": after, "existing_guides_unchanged": True,
        "final_antikor_guide_count": 165, "all_promoted_markdown_valid": True,
        "guides": records,
    })
    (BATCH / "promotion_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"promoted": 38, "total": 165, "existing_unchanged": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
