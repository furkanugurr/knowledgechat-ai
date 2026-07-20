"""Clean placeholder-only Batch 3 evidence and revalidate all candidates."""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.evidence import is_placeholder_line
from tools.visual_guide_extractor.scripts.cleanup_batch_2_placeholders import (
    clean_markdown,
    failure_record,
    structural_checks,
)
from tools.visual_guide_extractor.scripts.run_batch_1 import save_json

BATCH = ROOT / "work" / "visual_guide_extraction" / "batch_3"
MANIFEST = BATCH / "batch_manifest.json"
FAILED = BATCH / "failed_guides.json"
PROGRESS = BATCH / "progress.json"
REPORT = BATCH / "placeholder_cleanup_report.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failed = json.loads(FAILED.read_text(encoding="utf-8"))
    affected = {
        str(item["slug"])
        for item in failed.get("guides", [])
        if item.get("error") == "placeholder_evidence_present"
    }
    if len(affected) != 19:
        raise RuntimeError(f"Expected 19 placeholder failures, found {len(affected)}")
    guides = manifest["guides"]
    by_slug = {str(item["slug"]): item for item in guides}
    if len(by_slug) != len(guides):
        raise RuntimeError("Duplicate Batch 3 slug")
    paths = [str(item["candidate_path"]).casefold() for item in guides]
    if len(paths) != len(set(paths)):
        raise RuntimeError("Duplicate Batch 3 candidate path")

    audit: list[dict[str, object]] = []
    removed_lines = 0
    removed_sections = 0
    for slug in sorted(affected):
        item = by_slug[slug]
        candidate = ROOT / str(item["candidate_path"])
        original = candidate.read_text(encoding="utf-8")
        cleaned, changes = clean_markdown(original)
        line_count = sum(len(change["removed_lines"]) for change in changes)
        section_count = sum(
            change["action"] == "placeholder_only_section_removed" for change in changes
        )
        removed_lines += line_count
        removed_sections += section_count
        retained = [
            line for line in original.splitlines()
            if line.strip() and not line.lstrip().startswith("#") and not is_placeholder_line(line)
        ]
        cleaned_lines = cleaned.splitlines()
        ui_preserved = all(line in cleaned_lines for line in retained)
        if not ui_preserved:
            raise RuntimeError(f"Valid evidence changed unexpectedly: {slug}")
        candidate.write_text(cleaned, encoding="utf-8")
        errors = structural_checks(candidate, str(item["source_url"]))
        item.update(
            final_status="approved_candidate" if not errors else "needs_targeted_retry",
            error="; ".join(errors) if errors else None,
            placeholder_cleanup_at=datetime.now(UTC).isoformat(),
        )
        audit.append({
            "title": item["title"], "slug": slug,
            "candidate_path": item["candidate_path"], "changed": cleaned != original,
            "removed_placeholder_line_count": line_count,
            "removed_placeholder_only_section_count": section_count,
            "changes": changes, "ui_text_preserved": ui_preserved,
            "validation_failures": errors, "passed": not errors,
        })

    affected_passed = sum(record["passed"] for record in audit)
    if affected_passed != 19:
        save_json(REPORT, {"affected_guide_count": 19, "audit": audit})
        raise RuntimeError(f"Affected candidate validation passed {affected_passed}/19")

    validation: list[dict[str, object]] = []
    for item in guides:
        errors = structural_checks(ROOT / str(item["candidate_path"]), str(item["source_url"]))
        item.update(
            final_status="approved_candidate" if not errors else "needs_targeted_retry",
            error="; ".join(errors) if errors else None,
        )
        validation.append({
            "title": item["title"], "slug": item["slug"],
            "candidate_path": item["candidate_path"], "passed": not errors,
            "failures": errors,
        })
    still_failing = [item for item in guides if item["final_status"] != "approved_candidate"]
    approved = len(guides) - len(still_failing)
    ready = approved == 38 and not still_failing
    now = datetime.now(UTC).isoformat()
    report = {
        "generated_at": now, "affected_guide_count": len(affected),
        "cleaned_guide_count": sum(record["changed"] for record in audit),
        "removed_placeholder_line_count": removed_lines,
        "removed_placeholder_only_section_count": removed_sections,
        "affected_validation_passed": affected_passed,
        "affected_validation_failed": 19 - affected_passed,
        "final_candidate_count": len(validation), "final_approved_count": approved,
        "guides_still_failing": [failure_record(item) for item in still_failing],
        "ready_for_promotion": ready, "audit": audit,
        "candidate_validation": validation,
    }
    save_json(REPORT, report)
    save_json(MANIFEST, manifest)
    save_json(FAILED, {
        "updated_at": now, "failed_count": len(still_failing),
        "guides": [failure_record(item) for item in still_failing],
    })
    progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
    progress.update(
        updated_at=now, completed=38, successful=approved, failed=len(still_failing),
        currently_processing_guide=None, current_screenshot_number=None,
    )
    save_json(PROGRESS, progress)
    save_json(BATCH / "candidate_validation_report.json", {
        "generated_at": now,
        "summary": dict(Counter("passed" if item["passed"] else "failed" for item in validation)),
        "guides": validation, "ready_for_promotion": ready,
    })
    print(json.dumps({
        "cleaned_guides": report["cleaned_guide_count"],
        "placeholder_lines_removed": removed_lines,
        "placeholder_only_sections_removed": removed_sections,
        "affected_passed": affected_passed, "final_approved": approved,
        "still_failing": len(still_failing), "ready_for_promotion": ready,
    }, ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
