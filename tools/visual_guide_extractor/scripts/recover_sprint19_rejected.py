"""Recover only Sprint 19 rejected pages from cached Qwen evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.visual_guide_extractor.config.settings import ExtractionSettings
from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.normalization import GemmaNormalizer
from tools.visual_guide_extractor.quality import FinalQualityValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction

TARGETS = (
    "sanal-ethernet-ppp", "yonetim-paneli-kullanicilari", "ipsec-vpn-profilleri",
    "site-to-site-vpn-ayarlari", "ssl-vpn-ayarlari",
)


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def classify(values: list[str], prefix: str) -> list[str]:
    return [item for item in values if item.startswith(prefix)]


def run() -> dict[str, object]:
    started = perf_counter()
    settings = ExtractionSettings.from_environment()
    root = settings.work_root / "sprint19"
    report_root = root / "reports"
    manifest_path = settings.work_root / "sprint19_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_key = {item["page_key"]: item for item in manifest}
    formatter = MarkdownGenerator()
    validator = FinalQualityValidator()
    prompt = REPOSITORY_ROOT / "tools" / "visual_guide_extractor" / "prompts" / "normalization_prompt.txt"
    normalizer: GemmaNormalizer | None = None
    previous_report_path = report_root / "rejected_recovery_report.json"
    previous_report = json.loads(previous_report_path.read_text(encoding="utf-8")) if previous_report_path.exists() else {}
    diagnoses: list[dict[str, object]] = []
    additional_gemma_calls = 0
    recovered = 0

    try:
        for key in TARGETS:
            item = by_key[key]
            checkpoint = report_root / "recovery_checkpoints" / f"{key}.json"
            rejected_path = root / "rejected" / f"{key}.json"
            if item["approval_status"] == "approved" and not rejected_path.exists() and checkpoint.exists():
                cached = json.loads(checkpoint.read_text(encoding="utf-8"))
                if cached.get("final_approved") and cached.get("remaining_reasons"):
                    cached["removed_during_recovery"] = cached["remaining_reasons"]
                    cached["remaining_reasons"] = []
                    save_json(checkpoint, cached)
                diagnoses.append(cached)
                continue
            page_dir = root / "vision_results" / key
            page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8"))
            qwen = [VisionExtraction.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(page_dir.glob("image-*.json"))]
            previous = json.loads(rejected_path.read_text(encoding="utf-8"))
            gemma_path = page_dir / "gemma_normalized.json"
            historical_truncated = key == "ipsec-vpn-profilleri"
            deterministic = formatter.build_deterministic_guide(page, qwen)
            result = validator.validate(page, qwen, deterministic)
            retry_status = "not_needed_deterministic_passed"
            retry_error = None

            attempt_path = page_dir / "gemma_retry_status.json"
            if not result.approved:
                save_json(attempt_path, {"status": "started", "mode": "compact", "page": page.page_title})
                try:
                    retry_output = page_dir / "gemma_normalized_retry.json"
                    if retry_output.exists():
                        normalized = NormalizedGuide.model_validate_json(retry_output.read_text(encoding="utf-8"))
                        retry_status = "valid_completed_cached"
                    else:
                        if normalizer is None:
                            normalizer = GemmaNormalizer(settings.ollama_host, settings.normalization_model, prompt, max(settings.request_timeout, 600))
                        additional_gemma_calls += 1
                        normalized = normalizer.normalize_compact(page, qwen)
                        save_json(retry_output, normalized.model_dump(mode="json"))
                        retry_status = "valid_completed"
                    result = validator.validate(page, qwen, normalized)
                    if not result.approved and result.sanitized_guide.ordered_steps:
                        result = validator.validate(page, qwen, result.sanitized_guide)
                        retry_status += "_sanitized_revalidated"
                    save_json(attempt_path, {"status": retry_status, "mode": "compact", "approved": result.approved})
                except Exception as exc:
                    retry_status = "failed_deterministic_preserved"
                    retry_error = f"{type(exc).__name__}: {exc}"
                    result = validator.validate(page, qwen, deterministic)
                    save_json(attempt_path, {"status": retry_status, "mode": "compact", "error": retry_error})

            removed = previous.get("removed_unsupported_claims", [])
            language = [value for value in previous.get("warnings", []) if value.startswith("İngilizce içerik:")]
            diagnosis = {
                "page": page.page_title, "page_key": key,
                "initial_rejection_reason": previous.get("warnings", []) + previous.get("rejected_sentences", []),
                "initial_confidence": previous["confidence_score"],
                "qwen_result_status": "valid_complete" if len(qwen) == item["image_count"] else "missing",
                "qwen_result_count": len(qwen),
                "gemma_result_status": "valid" if gemma_path.exists() else ("truncated_invalid" if historical_truncated else "missing"),
                "gemma_json_truncated": historical_truncated,
                "unsupported_claims": removed,
                "unknown_controls": classify(removed, "Bilinmeyen kontrol:") + classify(removed, "Kontrol/alan kanıtı olmayan eylem:"),
                "language_issues": language,
                "menu_path_issues": classify(removed, "Desteklenmeyen menü yolu:"),
                "recovery_source": "gemma_compact_retry" if retry_status.startswith("valid_completed") else "deterministic_qwen_html",
                "gemma_retry_status": retry_status, "gemma_retry_error": retry_error,
                "final_confidence": result.confidence_score, "final_approved": result.approved,
                "removed_during_recovery": result.rejected_sentences + result.removed_unsupported_claims,
                "remaining_reasons": [] if result.approved else result.warnings + result.rejected_sentences,
            }
            diagnoses.append(diagnosis)
            save_json(report_root / "recovery_checkpoints" / f"{key}.json", diagnosis)
            item.update(confidence=result.confidence_score, approval_status="approved" if result.approved else "rejected", status="completed")
            if result.approved:
                recovered += 1
                approved_dir = root / "approved" / item["category_key"]
                approved_dir.mkdir(parents=True, exist_ok=True)
                (approved_dir / f"{key}.md").write_text(formatter.generate_pilot_approved(result.sanitized_guide, result.confidence_score), encoding="utf-8")
                rejected_path.unlink(missing_ok=True)
            else:
                save_json(rejected_path, result.model_dump(mode="json"))
            save_json(manifest_path, manifest)
    finally:
        if normalizer is not None:
            try:
                normalizer.unload()
            finally:
                normalizer.close()

    approved = [item for item in manifest if item["approval_status"] == "approved"]
    rejected = [item for item in manifest if item["approval_status"] == "rejected"]
    for diagnosis in diagnoses:
        if diagnosis["page_key"] != "ipsec-vpn-profilleri":
            continue
        page_dir = root / "vision_results" / diagnosis["page_key"]
        page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8"))
        qwen = [VisionExtraction.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(page_dir.glob("image-*.json"))]
        original = validator.validate(page, qwen, formatter.build_deterministic_guide(page, qwen))
        diagnosis["initial_confidence"] = original.confidence_score
        diagnosis["initial_rejection_reason"] = original.warnings + original.rejected_sentences
        diagnosis["unsupported_claims"] = original.removed_unsupported_claims
        diagnosis["unknown_controls"] = classify(original.removed_unsupported_claims, "Kontrol/alan kanıtı olmayan eylem:")
        diagnosis["language_issues"] = [value for value in original.warnings if value.startswith("İngilizce içerik:")]
        save_json(report_root / "recovery_checkpoints" / f"{diagnosis['page_key']}.json", diagnosis)
    elapsed_this_run = round(perf_counter() - started, 3)
    cumulative_gemma_calls = int(previous_report.get("additional_gemma_calls", 0)) + additional_gemma_calls
    elapsed = round(float(previous_report.get("additional_runtime_seconds", 0.0)) + elapsed_this_run, 3)
    recovery_report = {
        "pages_reviewed": len(TARGETS), "recovered_page_count": len([item for item in diagnoses if item["final_approved"]]),
        "still_rejected_page_count": len([item for item in diagnoses if not item["final_approved"]]),
        "additional_qwen_calls": 0, "additional_gemma_calls": cumulative_gemma_calls,
        "additional_runtime_seconds": elapsed, "final_approved_total": len(approved),
        "final_rejected_total": len(rejected),
        "ready_for_knowledge_base_promotion": not rejected,
        "pages": diagnoses,
    }
    save_json(report_root / "rejected_recovery_report.json", recovery_report)

    quality_path = report_root / "sprint19_quality_report.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    quality["initial_warnings"] = quality.get("warnings", [])
    quality.update({
        "approved_pages": len(approved), "rejected_pages": len(rejected),
        "average_confidence": round(sum(float(item["confidence"]) for item in manifest) / len(manifest), 3),
        "warnings": [reason for page in diagnoses if not page["final_approved"] for reason in page["remaining_reasons"]],
        "recovery_additional_qwen_calls": 0, "recovery_additional_gemma_calls": cumulative_gemma_calls,
        "recovery_duration_seconds": elapsed,
    })
    save_json(quality_path, quality)
    lines = ["# Sprint 19 Manuel İnceleme Kuyruğu", "", "## Reddedilen sayfalar", ""]
    lines.extend([*(f"- [{item['page_title']}]({item['url']}) — güven: {item['confidence']}" for item in rejected)] or ["- Yok."])
    lines.extend(["", "## Kurtarılan sayfalar", ""])
    lines.extend(f"- {page['page']} — güven: {page['final_confidence']}, kaynak: {page['recovery_source']}" for page in diagnoses if page["final_approved"])
    (report_root / "manual_review_queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return recovery_report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
