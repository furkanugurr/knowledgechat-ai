"""Analyze the existing 15-image PoC dataset with Qwen and Gemma."""

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
from tools.visual_guide_extractor.quality import FinalQualityValidator, QualityValidator
from tools.visual_guide_extractor.quality.baseline import SPRINT_15_BASELINE
from tools.visual_guide_extractor.schemas.extraction import (
    GuidePage,
    NormalizedGuide,
    VisionExtraction,
)
from tools.visual_guide_extractor.vision import QwenVisionAdapter, VisionResultStore


PAGE_KEYS = ("simple_text", "form_ui_heavy", "multi_screenshot_steps")


def _load_pages(work_root: Path) -> dict[str, GuidePage]:
    pages: dict[str, GuidePage] = {}
    for page_key in PAGE_KEYS:
        path = work_root / "pages" / f"{page_key}.json"
        pages[page_key] = GuidePage.model_validate_json(path.read_text(encoding="utf-8"))
    return pages


def _save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_legacy_all_gemma() -> dict[str, object]:
    """Legacy comparison runner retained for Sprint 17 metrics only."""
    settings = ExtractionSettings.from_environment()
    settings.ensure_work_directories()
    pages = _load_pages(settings.work_root)
    prompt_root = REPOSITORY_ROOT / "tools" / "visual_guide_extractor" / "prompts"
    adapter = QwenVisionAdapter(
        settings.ollama_host,
        settings.vision_model,
        prompt_root / "vision_prompt.txt",
        settings.request_timeout,
        settings.vision_context_window,
    )
    store = VisionResultStore(settings.work_root / "vision_results")
    results_by_page: dict[str, list[VisionExtraction]] = {
        key: [] for key in PAGE_KEYS
    }
    durations: list[float] = []
    failures: list[dict[str, object]] = []
    pages_updated: set[str] = set()
    new_successes = 0
    previous_report_path = (
        settings.work_root / "reports" / "vision_quality_report.json"
    )
    previous_total_duration = 0.0
    if previous_report_path.exists():
        previous_report = json.loads(previous_report_path.read_text(encoding="utf-8"))
        previous_total_duration = float(
            previous_report.get("total_processing_time_seconds", 0.0)
        )

    try:
        for page_key, page in pages.items():
            for block in page.image_blocks:
                if block.image_index is None or block.local_image_path is None:
                    failures.append(
                        {
                            "page_key": page_key,
                            "image_index": block.image_index,
                            "error": "Image block has no local path",
                        }
                    )
                    continue
                image_path = settings.repository_root / block.local_image_path
                existing_path = (
                    settings.work_root
                    / "vision_results"
                    / page_key
                    / f"image-{block.image_index}.json"
                )
                if existing_path.exists() and not settings.force_vision:
                    try:
                        existing = VisionExtraction.model_validate_json(
                            existing_path.read_text(encoding="utf-8")
                        )
                        results_by_page[page_key].append(existing)
                        continue
                    except ValueError:
                        pass
                started_at = perf_counter()
                try:
                    result = adapter.analyze(
                        image_path=image_path,
                        page_title=page.page_title,
                        image_index=block.image_index,
                        html_context=page.context_for_image(block.image_index),
                        extraction_metadata={
                            "source_url": page.source_url,
                            "image_url": block.image_url,
                            "alt_text": block.alt_text,
                            "local_image_path": block.local_image_path,
                        },
                    )
                    store.save(page_key, result)
                    results_by_page[page_key].append(result)
                    pages_updated.add(page_key)
                    new_successes += 1
                except Exception as exc:
                    failures.append(
                        {
                            "page_key": page_key,
                            "image_index": block.image_index,
                            "image_path": block.local_image_path,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                finally:
                    durations.append(perf_counter() - started_at)
    finally:
        try:
            adapter.unload()
        finally:
            adapter.close()

    normalized_failures: list[dict[str, str]] = []
    normalizer = GemmaNormalizer(
        settings.ollama_host,
        settings.normalization_model,
        prompt_root / "normalization_prompt.txt",
        settings.request_timeout,
    )
    formatter = MarkdownGenerator()
    try:
        for page_key, page in pages.items():
            page_results = results_by_page[page_key]
            if not page_results:
                normalized_failures.append(
                    {"page_key": page_key, "error": "No successful Qwen results"}
                )
                continue
            if (
                not settings.force_normalization
                and page_key not in pages_updated
                and (
                settings.work_root / "normalized_results" / f"{page_key}.json"
                ).exists()
            ):
                continue
            try:
                normalized = normalizer.normalize(page, page_results)
                result_root = settings.work_root / "normalized_results"
                _save_json(
                    result_root / f"{page_key}.json",
                    normalized.model_dump(mode="json"),
                )
                (result_root / f"{page_key}.md").write_text(
                    formatter.generate_normalized(normalized),
                    encoding="utf-8",
                )
            except Exception as exc:
                normalized_failures.append(
                    {"page_key": page_key, "error": f"{type(exc).__name__}: {exc}"}
                )
    finally:
        try:
            normalizer.unload()
        finally:
            normalizer.close()

    successful_results = [result for values in results_by_page.values() for result in values]
    total_images = sum(len(page.image_blocks) for page in pages.values())
    cumulative_duration = previous_total_duration + sum(durations)
    quality_report: dict[str, object] = {
        "total_images_processed": total_images,
        "successful_analyses": len(successful_results),
        "failed_analyses": len(failures),
        "images_with_uncertainties": sum(
            1 for result in successful_results if result.uncertainties
        ),
        "average_processing_time_seconds": (
            round(cumulative_duration / total_images, 3) if total_images else 0.0
        ),
        "total_processing_time_seconds": round(cumulative_duration, 3),
        "images_processed_in_this_run": len(durations),
        "resumed_existing_results": len(successful_results) - new_successes,
        "model_used": settings.vision_model,
        "normalization_model": settings.normalization_model,
        "failures": failures,
        "normalization_failures": normalized_failures,
    }
    _save_json(
        settings.work_root / "reports" / "vision_quality_report.json",
        quality_report,
    )
    validator = QualityValidator()
    vision_metrics = validator.evaluate_vision_results(successful_results)
    page_findings: dict[str, object] = {}
    normalization_read_errors: list[str] = []
    for page_key, page in pages.items():
        normalized_path = (
            settings.work_root / "normalized_results" / f"{page_key}.json"
        )
        try:
            normalized = NormalizedGuide.model_validate_json(
                normalized_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            normalization_read_errors.append(f"{page_key}: {type(exc).__name__}: {exc}")
            continue
        page_findings[page_key] = validator.evaluate(
            page,
            results_by_page[page_key],
            normalized,
        )

    translated_labels = sum(
        len(value["english_ui_label_translations"])
        for value in page_findings.values()
    )
    remaining_warnings: list[str] = list(normalization_read_errors)
    if int(vision_metrics["english_prose_fragments"]) > 0:
        remaining_warnings.append(
            "Qwen English prose fragments remain: "
            f"{vision_metrics['english_prose_fragments']}"
        )
    for page_key, findings in page_findings.items():
        for category, values in findings.items():
            remaining_warnings.extend(
                f"{page_key}/{category}: {value}" for value in values
            )
    after_metrics: dict[str, object] = {
        **vision_metrics,
        "normalized_english_ui_labels": translated_labels,
        "quality_findings": page_findings,
    }
    fixed_issues: list[str] = []
    for metric, label in (
        ("english_prose_fragments", "Qwen English prose was removed"),
        ("control_field_overlap", "Control/field duplication was removed"),
        ("empty_field_locations", "Empty field locations were removed"),
        ("normalized_english_ui_labels", "Gemma UI-label translations were removed"),
    ):
        if int(SPRINT_15_BASELINE[metric]) > 0 and int(after_metrics[metric]) == 0:
            fixed_issues.append(label)
    before_after = {
        "before": SPRINT_15_BASELINE,
        "after": after_metrics,
        "fixed_issues": fixed_issues,
        "remaining_warnings": remaining_warnings,
        "ready_for_full_crawl": (
            len(successful_results) == total_images
            and not failures
            and not normalized_failures
            and not remaining_warnings
        ),
    }
    _save_json(
        settings.work_root / "reports" / "quality_before_after.json",
        before_after,
    )
    final_validator = FinalQualityValidator()
    final_results: dict[str, object] = {}
    rejected_sentences: list[dict[str, str]] = []
    removed_claims: list[dict[str, str]] = []
    approved_count = 0
    approved_root = settings.work_root / "approved_drafts"
    for stale in approved_root.glob("*.md"):
        stale.unlink()
    for page_key, page in pages.items():
        normalized_path = settings.work_root / "normalized_results" / f"{page_key}.json"
        try:
            normalized = NormalizedGuide.model_validate_json(normalized_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            final_results[page_key] = {"confidence_score": 0.0, "warnings": [f"Normalize çıktı okunamadı: {type(exc).__name__}: {exc}"], "approved": False}
            continue
        validation = final_validator.validate(page, results_by_page[page_key], normalized)
        payload = validation.model_dump(mode="json")
        final_results[page_key] = {key: value for key, value in payload.items() if key != "sanitized_guide"}
        _save_json(approved_root / f"{page_key}.validation.json", payload)
        rejected_sentences.extend({"page_key": page_key, "sentence": item} for item in validation.rejected_sentences)
        removed_claims.extend({"page_key": page_key, "claim": item} for item in validation.removed_unsupported_claims)
        if validation.approved:
            approved_count += 1
            (approved_root / f"{page_key}.md").write_text(
                formatter.generate_approved(validation.sanitized_guide, validation.confidence_score), encoding="utf-8"
            )

    scores = [float(item["confidence_score"]) for item in final_results.values()]
    confidence_distribution = {
        "per_guide": {key: value["confidence_score"] for key, value in final_results.items()},
        "minimum": min(scores, default=0.0), "maximum": max(scores, default=0.0),
        "average": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "high_0_80_to_1_00": sum(score >= 0.80 for score in scores),
        "medium_0_60_to_0_79": sum(0.60 <= score < 0.80 for score in scores),
        "low_below_0_60": sum(score < 0.60 for score in scores),
    }
    ready = len(successful_results) == total_images and not failures and not normalized_failures and approved_count == len(PAGE_KEYS)
    _save_json(settings.work_root / "reports" / "quality_final_report.json", {
        "previous_metrics": before_after["after"],
        "new_metrics": {"images_evaluated": len(successful_results), "guides_evaluated": len(final_results),
                        "approved_guide_count": approved_count, "rejected_guide_count": len(final_results) - approved_count,
                        "rejected_sentence_count": len(rejected_sentences), "removed_unsupported_claim_count": len(removed_claims)},
        "rejected_sentences": rejected_sentences, "removed_unsupported_claims": removed_claims,
        "confidence_distribution": confidence_distribution, "guide_results": final_results,
        "approved_guide_count": approved_count, "ready_for_full_crawl": ready,
    })
    return quality_report


if __name__ == "__main__":
    from tools.visual_guide_extractor.scripts.run_fallback_poc import run

    print(json.dumps(run(), ensure_ascii=False, indent=2))
