"""Deterministically clean and revalidate Batch 2 candidate Markdown files."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.evidence import has_usable_evidence, is_placeholder_line
from tools.visual_guide_extractor.scripts.run_batch_1 import markdown_checks, normalize_url, save_json


BATCH_ROOT = ROOT / "work" / "visual_guide_extraction" / "batch_2"
MANIFEST_PATH = BATCH_ROOT / "batch_manifest.json"
FAILED_PATH = BATCH_ROOT / "failed_guides.json"
PROGRESS_PATH = BATCH_ROOT / "progress.json"
REPORT_PATH = BATCH_ROOT / "placeholder_cleanup_report.json"


def clean_markdown(text: str) -> tuple[str, list[dict[str, object]]]:
    """Remove only centrally detected placeholder lines and empty sections."""
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    changes: list[dict[str, object]] = []
    output = text
    for index in range(len(headings) - 1, -1, -1):
        heading = headings[index]
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end]
        lines = body.splitlines()
        removed = [line.strip() for line in lines if is_placeholder_line(line)]
        if not removed:
            continue
        remaining = [line for line in lines if not is_placeholder_line(line)]
        nonblank = [line for line in remaining if line.strip()]
        if nonblank:
            replacement = f"{heading.group(0)}\n" + "\n".join(remaining).strip() + "\n\n"
            action = "placeholder_lines_removed"
        else:
            replacement = ""
            action = "placeholder_only_section_removed"
        output = output[:heading.start()] + replacement + output[end:]
        changes.append({
            "section": heading.group(1).strip(),
            "action": action,
            "removed_lines": removed,
        })
    output = re.sub(r"\n{3,}", "\n\n", output).strip() + "\n"
    return output, list(reversed(changes))


def structural_checks(path: Path, expected_url: str) -> list[str]:
    failures = markdown_checks(path, expected_url)
    text = path.read_text(encoding="utf-8")
    if text.count("```") % 2:
        failures.append("unbalanced_code_fence")
    headings = re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
    if len(headings) != len(set(headings)):
        failures.append("duplicate_section_heading")
    sections = re.split(r"^##\s+.+?\s*$", text, flags=re.MULTILINE)[1:]
    if not any(has_usable_evidence(section) for section in sections):
        failures.append("no_usable_evidence_section")
    return sorted(set(failures))


def failure_record(item: dict[str, object]) -> dict[str, object]:
    return {
        key: item.get(key)
        for key in ("title", "slug", "category", "source_url", "final_status", "error")
    }


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    failed = json.loads(FAILED_PATH.read_text(encoding="utf-8"))
    affected_slugs = {
        str(item["slug"])
        for item in failed.get("guides", [])
        if item.get("error") == "placeholder_evidence_present"
    }
    if len(affected_slugs) != 23:
        raise RuntimeError(f"Expected 23 placeholder failures, found {len(affected_slugs)}")

    guide_by_slug = {str(item["slug"]): item for item in manifest["guides"]}
    if len(guide_by_slug) != len(manifest["guides"]):
        raise RuntimeError("Duplicate slug detected in Batch 2 manifest")
    urls = [normalize_url(str(item["source_url"])) for item in manifest["guides"]]
    if len(urls) != len(set(urls)):
        raise RuntimeError("Duplicate source URL detected in Batch 2 manifest")

    audit: list[dict[str, object]] = []
    removed_lines = 0
    removed_sections = 0
    for slug in sorted(affected_slugs):
        item = guide_by_slug[slug]
        candidate = ROOT / str(item["candidate_path"])
        original = candidate.read_text(encoding="utf-8")
        cleaned, changes = clean_markdown(original)
        removed_lines += sum(len(change["removed_lines"]) for change in changes)
        removed_sections += sum(change["action"] == "placeholder_only_section_removed" for change in changes)
        # Since the transformation removes full lines only, every retained UI
        # label/control/field line remains byte-for-byte unchanged.
        retained_original = [
            line for line in original.splitlines()
            if line.strip() and not line.lstrip().startswith("#") and not is_placeholder_line(line)
        ]
        retained_cleaned = cleaned.splitlines()
        ui_text_preserved = all(line in retained_cleaned for line in retained_original if line.strip())
        if not ui_text_preserved:
            raise RuntimeError(f"Valid evidence changed unexpectedly for {slug}")
        candidate.write_text(cleaned, encoding="utf-8")
        failures = structural_checks(candidate, str(item["source_url"]))
        item.update(
            final_status="approved_candidate" if not failures else "needs_targeted_retry",
            error="; ".join(failures) if failures else None,
            placeholder_cleanup_at=datetime.now(UTC).isoformat(),
        )
        audit.append({
            "title": item["title"],
            "slug": slug,
            "candidate_path": item["candidate_path"],
            "changed": cleaned != original,
            "removed_placeholder_line_count": sum(len(change["removed_lines"]) for change in changes),
            "removed_placeholder_only_section_count": sum(
                change["action"] == "placeholder_only_section_removed" for change in changes
            ),
            "changes": changes,
            "ui_text_preserved": ui_text_preserved,
            "validation_failures": failures,
            "passed": not failures,
        })

    affected_failures = {
        slug: structural_checks(ROOT / str(guide_by_slug[slug]["candidate_path"]), str(guide_by_slug[slug]["source_url"]))
        for slug in sorted(affected_slugs)
    }
    all_validation: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for item in manifest["guides"]:
        path_key = str(item["candidate_path"]).casefold()
        duplicate_path = path_key in seen_paths
        seen_paths.add(path_key)
        failures = structural_checks(ROOT / str(item["candidate_path"]), str(item["source_url"]))
        if duplicate_path:
            failures.append("duplicate_candidate_path")
        failures = sorted(set(failures))
        if failures:
            item.update(final_status="needs_targeted_retry", error="; ".join(failures))
        else:
            item.update(final_status="approved_candidate", error=None)
        all_validation.append({
            "title": item["title"], "slug": item["slug"],
            "candidate_path": item["candidate_path"], "passed": not failures,
            "failures": failures,
        })

    still_failing = [item for item in manifest["guides"] if item["final_status"] != "approved_candidate"]
    approved = sum(item["final_status"] == "approved_candidate" for item in manifest["guides"])
    ready = approved == len(manifest["guides"]) and not still_failing
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "affected_guide_count": len(affected_slugs),
        "cleaned_guide_count": sum(record["changed"] for record in audit),
        "removed_placeholder_line_count": removed_lines,
        "removed_placeholder_only_section_count": removed_sections,
        "affected_validation_passed": sum(not failures for failures in affected_failures.values()),
        "affected_validation_failed": sum(bool(failures) for failures in affected_failures.values()),
        "final_candidate_count": len(all_validation),
        "final_approved_count": approved,
        "guides_still_failing": [failure_record(item) for item in still_failing],
        "ready_for_promotion": ready,
        "audit": audit,
        "candidate_validation": all_validation,
    }
    save_json(REPORT_PATH, report)
    save_json(MANIFEST_PATH, manifest)
    save_json(FAILED_PATH, {
        "updated_at": datetime.now(UTC).isoformat(),
        "failed_count": len(still_failing),
        "guides": [failure_record(item) for item in still_failing],
    })
    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    progress.update(
        updated_at=datetime.now(UTC).isoformat(), completed=len(manifest["guides"]),
        successful=approved, failed=len(still_failing),
        currently_processing_guide=None, current_screenshot_number=None,
    )
    save_json(PROGRESS_PATH, progress)
    save_json(BATCH_ROOT / "candidate_validation_report.json", {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": dict(Counter("passed" if x["passed"] else "failed" for x in all_validation)),
        "guides": all_validation,
        "ready_for_promotion": ready,
    })
    print(json.dumps({
        "cleaned_guides": report["cleaned_guide_count"],
        "placeholder_lines_removed": removed_lines,
        "placeholder_only_sections_removed": removed_sections,
        "affected_passed": report["affected_validation_passed"],
        "final_approved": approved,
        "still_failing": len(still_failing),
        "ready_for_promotion": ready,
    }, ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
