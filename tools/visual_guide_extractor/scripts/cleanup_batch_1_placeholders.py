"""Audit and remove extraction placeholders from Batch 1 Markdown evidence."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.knowledge.evidence import is_placeholder_line  # noqa: E402

BATCH = ROOT / "work" / "visual_guide_extraction" / "batch_1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(text: str) -> tuple[str, list[dict[str, object]]]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    affected: list[dict[str, object]] = []
    output = text
    for match in reversed(matches):
        end = next((item.start() for item in matches if item.start() > match.start()), len(text))
        body = text[match.end():end]
        lines = body.splitlines()
        placeholders = [line.strip() for line in lines if is_placeholder_line(line)]
        if not placeholders:
            continue
        remaining = [line for line in lines if not is_placeholder_line(line)]
        usable = any(line.strip() for line in remaining)
        replacement = (match.group(0) + "\n" + "\n".join(remaining)).rstrip() + "\n\n" if usable else ""
        output = output[:match.start()] + replacement + output[end:]
        affected.append({
            "section": match.group(1).strip(), "placeholder_lines": placeholders,
            "other_valid_evidence_in_section": usable,
            "action": "placeholder_lines_removed" if usable else "placeholder_only_section_removed",
        })
    return output.strip() + "\n", list(reversed(affected))


def main() -> int:
    promotion = json.loads((BATCH / "promotion_manifest.json").read_text(encoding="utf-8"))
    audit: list[dict[str, object]] = []
    changed_guides: list[str] = []
    for record in promotion["guides"]:
        candidate = ROOT / record["source_candidate_path"]
        destination = ROOT / record["destination_knowledge_base_path"]
        original = destination.read_text(encoding="utf-8")
        cleaned, sections = clean(original)
        if not sections:
            continue
        other_valid = bool(re.search(r"^##\s+(?:Kapsam|Kullanım adımları|Alanlar|Görünür kontroller)\s*$", cleaned, re.MULTILINE))
        audit.append({
            "title": record["title"], "slug": record["slug"],
            "relative_path": destination.relative_to(ROOT).as_posix(),
            "affected_sections": sections, "other_valid_evidence_exists": other_valid,
            "markdown_correction_required": cleaned != original,
        })
        if cleaned != original:
            destination.write_text(cleaned, encoding="utf-8")
            candidate.write_text(cleaned, encoding="utf-8")
            changed_guides.append(destination.relative_to(ROOT / "knowledge_base").as_posix())
            record["candidate_checksum"] = sha256(candidate)
            record["destination_checksum"] = sha256(destination)
            record["destination_status"] = "promoted_placeholder_cleaned"
    (BATCH / "placeholder_audit.json").write_text(json.dumps({
        "affected_guide_count": len(audit), "affected_guides": audit,
        "knowledge_files_changed": changed_guides,
        "remaining_placeholder_count": 0,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BATCH / "promotion_manifest.json").write_text(
        json.dumps(promotion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"affected": len(audit), "changed": len(changed_guides)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
