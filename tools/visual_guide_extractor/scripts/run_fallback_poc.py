"""Run the 15-image PoC with deterministic output and optional Gemma fallback."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from time import perf_counter

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.visual_guide_extractor.config.settings import ExtractionSettings
from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.normalization import GemmaNormalizer
from tools.visual_guide_extractor.quality import FallbackDecisionEngine, FinalQualityValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction

PAGE_KEYS = ("simple_text", "form_ui_heavy", "multi_screenshot_steps")


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run() -> dict[str, object]:
    started = perf_counter()
    settings = ExtractionSettings.from_environment()
    settings.ensure_work_directories()
    formatter = MarkdownGenerator()
    validator = FinalQualityValidator()
    decisions = FallbackDecisionEngine()
    output_root = settings.work_root / "approved_drafts"
    for stale in output_root.glob("*.md"):
        stale.unlink()

    normalizer: GemmaNormalizer | None = None
    live_gemma_calls = 0
    cached_gemma_results = 0
    page_reports: dict[str, object] = {}
    fallback_reasons: dict[str, list[str]] = {}
    approved = rejected = 0
    qwen_results_used = 0

    try:
        for page_key in PAGE_KEYS:
            page = GuidePage.model_validate_json(
                (settings.work_root / "pages" / f"{page_key}.json").read_text(encoding="utf-8")
            )
            vision = [
                VisionExtraction.model_validate_json(path.read_text(encoding="utf-8"))
                for path in sorted((settings.work_root / "vision_results" / page_key).glob("image-*.json"))
            ]
            qwen_results_used += len(vision)
            deterministic = formatter.build_deterministic_guide(page, vision)
            initial = validator.validate(page, vision, deterministic)
            decision = decisions.decide(
                confidence_score=initial.confidence_score,
                warning_count=len(initial.warnings),
                uncertainty_count=len(deterministic.uncertainties),
                unsupported_claim_count=len(initial.removed_unsupported_claims),
                step_count=len(deterministic.ordered_steps),
                image_count=len(page.image_blocks),
            )
            selected = deterministic
            source = "deterministic"
            if decision.use_gemma:
                fallback_reasons[page_key] = decision.reasons
                cache = settings.work_root / "normalized_results" / f"{page_key}.json"
                force = os.getenv("VISUAL_GUIDE_FORCE_NORMALIZATION", "false").lower() in {"1", "true", "yes"}
                if cache.exists() and not force:
                    selected = NormalizedGuide.model_validate_json(cache.read_text(encoding="utf-8"))
                    cached_gemma_results += 1
                    source = "gemma_fallback_cache"
                else:
                    if normalizer is None:
                        normalizer = GemmaNormalizer(
                            settings.ollama_host, settings.normalization_model,
                            REPOSITORY_ROOT / "tools" / "visual_guide_extractor" / "prompts" / "normalization_prompt.txt",
                            settings.request_timeout,
                        )
                    call_started = perf_counter()
                    selected = normalizer.normalize(page, vision)
                    live_gemma_calls += 1
                    save_json(cache, selected.model_dump(mode="json"))
                    source = "gemma_fallback_live"
                    gemma_seconds = perf_counter() - call_started
            final = validator.validate(page, vision, selected)
            save_json(output_root / f"{page_key}.validation.json", final.model_dump(mode="json"))
            if final.approved:
                approved += 1
                (output_root / f"{page_key}.md").write_text(
                    formatter.generate_approved(final.sanitized_guide, final.confidence_score), encoding="utf-8"
                )
            else:
                rejected += 1
            page_reports[page_key] = {
                "source": source,
                "use_gemma": decision.use_gemma,
                "fallback_reasons": decision.reasons,
                "page_complexity": decision.page_complexity,
                "initial_confidence": initial.confidence_score,
                "final_confidence": final.confidence_score,
                "approved": final.approved,
                "image_count": len(page.image_blocks),
                "uncertainty_count": len(deterministic.uncertainties),
            }
    finally:
        if normalizer is not None:
            try:
                normalizer.unload()
            finally:
                normalizer.close()

    elapsed = round(perf_counter() - started, 3)
    gemma_pages = sum(bool(item["use_gemma"]) for item in page_reports.values())
    report = {
        "total_processed_pages": len(page_reports),
        "pages_requiring_gemma": gemma_pages,
        "pages_without_gemma": len(page_reports) - gemma_pages,
        "fallback_reasons": fallback_reasons,
        "processing_time_comparison": {
            "before_all_gemma_seconds": 757.3,
            "after_optional_pipeline_seconds": elapsed,
            "note": "After run reused validated Qwen JSON and cached Gemma fallback results where available.",
        },
        "qwen_api_calls": 0,
        "qwen_results_reused": qwen_results_used,
        "gemma_calls_before": 3,
        "gemma_fallback_pages_after": gemma_pages,
        "gemma_live_api_calls_after": live_gemma_calls,
        "gemma_cached_results_after": cached_gemma_results,
        "approved_drafts": approved,
        "rejected_drafts": rejected,
        "confidence_scores": {key: item["final_confidence"] for key, item in page_reports.items()},
        "pages": page_reports,
        "total_runtime_seconds": elapsed,
        "ready_for_full_crawl": approved == len(PAGE_KEYS) and rejected == 0,
    }
    save_json(settings.work_root / "reports" / "gemma_usage_report.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
