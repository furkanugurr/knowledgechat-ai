"""Resumable local runner for the second batch of unpromoted Antikor guides.

This script is intentionally designed for manual PowerShell execution.  It
persists its manifest and progress after every meaningful operation so Ctrl+C
followed by ``--resume`` does not repeat completed Qwen analyses.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from tools.visual_guide_extractor.config.settings import ExtractionSettings
from tools.visual_guide_extractor.crawler import GuidePageParser, PageLoader
from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.normalization import GemmaNormalizer
from tools.visual_guide_extractor.quality import FallbackDecisionEngine, FinalQualityValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction
from tools.visual_guide_extractor.scripts.run_batch_1 import (
    CATEGORY_NAMES,
    GUIDE_ROOT,
    complexity,
    discover,
    markdown_checks,
    normalize_url,
    promoted_urls,
    save_json,
)
from tools.visual_guide_extractor.vision import QwenVisionAdapter

BATCH_ROOT = ROOT / "work" / "visual_guide_extraction" / "batch_2"
MANIFEST_PATH = BATCH_ROOT / "batch_manifest.json"
PROGRESS_PATH = BATCH_ROOT / "progress.json"
FAILED_PATH = BATCH_ROOT / "failed_guides.json"
LOG_PATH = BATCH_ROOT / "run.log"

# Whole categories only: 7 + 8 + 8 + 8 + 8 = 39 guides on the 2026-07-20
# source inventory. A count guard below detects upstream site changes.
SELECTED_CATEGORIES = (
    "duyuru-ve-form-yonetimi",
    "eposta-guvenligi",
    "guvenlik-profilleri",
    "web-filtreleme",
    "yonlendirme-yonetimi",
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def configure_logging() -> logging.Logger:
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("batch_2")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger


def fresh_inventory(loader: PageLoader) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    discovered = discover(loader.load_page(GUIDE_ROOT))
    promoted = promoted_urls()
    seen_urls: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    remaining: list[dict[str, object]] = []
    selected: list[dict[str, object]] = []
    for raw in discovered:
        item = dict(raw)
        url = normalize_url(str(item["source_url"]))
        key = (str(item["category_key"]), str(item["slug"]))
        if url in seen_urls or key in seen_keys:
            continue
        seen_urls.add(url)
        seen_keys.add(key)
        if url in promoted:
            continue
        item.update(
            current_extraction_status="remaining",
            already_promoted=False,
            selected_for_batch_2=item["category_key"] in SELECTED_CATEGORIES,
            reason=(
                "included_complete_category_batch_2"
                if item["category_key"] in SELECTED_CATEGORIES
                else "deferred_to_later_batch"
            ),
        )
        remaining.append(item)
        if item["selected_for_batch_2"]:
            selected.append(item)
    if not 35 <= len(selected) <= 40:
        raise RuntimeError(
            f"Batch 2 must contain 35-40 unique remaining guides; discovered {len(selected)}. "
            "Review SELECTED_CATEGORIES before running."
        )
    save_json(BATCH_ROOT / "remaining_inventory.json", {
        "generated_at": utc_now(),
        "discovered_count": len(discovered),
        "promoted_count": len(promoted),
        "remaining_count": len(remaining),
        "selected_count": len(selected),
        "selected_categories": list(SELECTED_CATEGORIES),
        "guides": remaining,
    })
    return remaining, selected


def initial_item(item: dict[str, object]) -> dict[str, object]:
    return {
        **item,
        "status": "selected",
        "final_status": "pending",
        "estimated_screenshot_count": 0,
        "screenshots_processed": 0,
        "confidence": None,
        "used_gemma": False,
        "error": None,
        "started_at": None,
        "completed_at": None,
    }


def build_or_refresh_manifest(loader: PageLoader, resume: bool) -> dict[str, object]:
    _, selected = fresh_inventory(loader)
    prior: dict[str, dict[str, object]] = {}
    if resume and MANIFEST_PATH.exists():
        old = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        prior = {normalize_url(str(x["source_url"])): x for x in old.get("guides", [])}
    guides = []
    for page in selected:
        saved = prior.get(normalize_url(str(page["source_url"])))
        guides.append({**saved, **page} if saved else initial_item(page))
    manifest = {
        "batch": 2,
        "generated_at": utc_now(),
        "selected_guide_count": len(guides),
        "selected_categories": list(SELECTED_CATEGORIES),
        "guides": guides,
    }
    save_json(MANIFEST_PATH, manifest)
    return manifest


def load_vision(directory: Path) -> list[VisionExtraction]:
    return [
        VisionExtraction.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("image-*.json"))
    ]


class ProgressTracker:
    def __init__(self, manifest: dict[str, object], started: float) -> None:
        self.manifest = manifest
        self.started = started
        previous = json.loads(PROGRESS_PATH.read_text(encoding="utf-8")) if PROGRESS_PATH.exists() else {}
        self.qwen_calls = int(previous.get("qwen_calls", 0))
        self.gemma_calls = int(previous.get("gemma_fallback_calls", 0))
        self.screenshots = int(previous.get("total_screenshots_processed", 0))

    def write(self, current: dict[str, object] | None = None, screenshot: int | None = None) -> None:
        guides = list(self.manifest["guides"])
        completed = [x for x in guides if x.get("final_status") not in {None, "pending"}]
        successful = [x for x in guides if x.get("final_status") == "approved_candidate"]
        failed = [x for x in guides if x.get("final_status") in {"failed", "extraction_failed", "needs_targeted_retry"}]
        save_json(PROGRESS_PATH, {
            "updated_at": utc_now(),
            "total_selected": len(guides),
            "completed": len(completed),
            "successful": len(successful),
            "failed": len(failed),
            "currently_processing_guide": current.get("slug") if current else None,
            "current_screenshot_number": screenshot,
            "total_screenshots_processed": self.screenshots,
            "qwen_calls": self.qwen_calls,
            "gemma_fallback_calls": self.gemma_calls,
            "elapsed_seconds": round(perf_counter() - self.started, 2),
        })
        save_json(FAILED_PATH, {
            "updated_at": utc_now(),
            "failed_count": len(failed),
            "guides": [
                {k: x.get(k) for k in ("title", "slug", "category", "source_url", "final_status", "error")}
                for x in failed
            ],
        })
        save_json(MANIFEST_PATH, self.manifest)


def page_directory(item: dict[str, object]) -> Path:
    return BATCH_ROOT / "vision_results" / str(item["category_key"]) / str(item["slug"])


def crawl_page(item: dict[str, object], loader: PageLoader, parser: GuidePageParser) -> GuidePage:
    directory = page_directory(item)
    page_path = directory / "page.json"
    if page_path.exists():
        return GuidePage.model_validate_json(page_path.read_text(encoding="utf-8"))
    page = parser.parse(loader.load_page(str(item["source_url"])), str(item["source_url"]))
    image_dir = directory / "images"
    for block in page.image_blocks:
        if block.image_url is None or block.image_index is None:
            continue
        image_path = loader.download_image(block.image_url, image_dir)
        block.local_image_path = image_path.relative_to(ROOT).as_posix()
    save_json(page_path, page.model_dump(mode="json"))
    return page


def analyze_images(
    item: dict[str, object], page: GuidePage, qwen: QwenVisionAdapter, progress: ProgressTracker,
) -> list[VisionExtraction]:
    directory = page_directory(item)
    for ordinal, block in enumerate(page.image_blocks, start=1):
        result_path = directory / f"image-{block.image_index}.json"
        progress.write(item, ordinal)
        if result_path.exists():
            VisionExtraction.model_validate_json(result_path.read_text(encoding="utf-8"))
            continue
        if not block.local_image_path:
            raise RuntimeError(f"Image {block.image_index} has no local path")
        progress.qwen_calls += 1
        result = qwen.analyze(
            ROOT / str(block.local_image_path),
            page.page_title,
            int(block.image_index),
            page.context_for_image(int(block.image_index)),
            {"source_url": page.source_url, "image_url": block.image_url, "alt_text": block.alt_text},
        )
        save_json(result_path, result.model_dump(mode="json"))
        progress.screenshots += 1
        item["screenshots_processed"] = int(item.get("screenshots_processed", 0)) + 1
        progress.write(item, ordinal)
    return load_vision(directory)


def generate_candidate(
    item: dict[str, object], page: GuidePage, vision: list[VisionExtraction],
    settings: ExtractionSettings, progress: ProgressTracker,
) -> None:
    formatter = MarkdownGenerator()
    validator = FinalQualityValidator()
    deterministic = formatter.build_deterministic_guide(page, vision)
    initial = validator.validate(page, vision, deterministic)
    decision = FallbackDecisionEngine().decide(
        confidence_score=initial.confidence_score,
        warning_count=len(initial.warnings),
        uncertainty_count=len(deterministic.uncertainties),
        unsupported_claim_count=len(initial.removed_unsupported_claims),
        step_count=len(deterministic.ordered_steps),
        image_count=len(page.image_blocks),
    )
    selected: NormalizedGuide = deterministic
    normalized_path = page_directory(item) / "gemma_normalized.json"
    if decision.use_gemma:
        item["used_gemma"] = True
        if normalized_path.exists():
            selected = NormalizedGuide.model_validate_json(normalized_path.read_text(encoding="utf-8"))
        else:
            prompt = ROOT / "tools" / "visual_guide_extractor" / "prompts" / "normalization_prompt.txt"
            normalizer = GemmaNormalizer(
                settings.ollama_host, settings.normalization_model, prompt, max(settings.request_timeout, 600)
            )
            try:
                progress.gemma_calls += 1
                progress.write(item)
                selected = normalizer.normalize(page, vision)
                save_json(normalized_path, selected.model_dump(mode="json"))
            except Exception as exc:
                item["gemma_error"] = f"{type(exc).__name__}: {exc}"
                selected = deterministic
            finally:
                try:
                    normalizer.unload()
                finally:
                    normalizer.close()
    final = validator.validate(page, vision, selected)
    if not final.approved or final.confidence_score < initial.confidence_score:
        final = initial
    if not final.approved:
        retry = validator.validate(page, vision, final.sanitized_guide)
        if retry.approved and retry.confidence_score >= final.confidence_score:
            final = retry
    candidate = BATCH_ROOT / "candidates" / str(item["category_key"]) / f"{item['slug']}.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(
        formatter.generate_pilot_approved(final.sanitized_guide, final.confidence_score), encoding="utf-8"
    )
    failures = markdown_checks(candidate, str(item["source_url"]))
    if not final.approved:
        failures.append("final_quality_not_approved")
    item.update(
        confidence=final.confidence_score,
        candidate_path=candidate.relative_to(ROOT).as_posix(),
        fallback_reasons=decision.reasons,
        final_status="approved_candidate" if not failures else "needs_targeted_retry",
        error="; ".join(failures) if failures else None,
    )


def select_targets(manifest: dict[str, object], args: argparse.Namespace) -> list[dict[str, object]]:
    guides = list(manifest["guides"])
    if args.slug:
        matches = [x for x in guides if x["slug"] == args.slug]
        if not matches:
            raise SystemExit(f"Unknown Batch 2 slug: {args.slug}")
        return matches
    if args.retry_failed:
        guides = [x for x in guides if x.get("final_status") in {"failed", "extraction_failed", "needs_targeted_retry"}]
    elif args.resume:
        guides = [x for x in guides if x.get("final_status") != "approved_candidate"]
    if args.limit is not None:
        guides = guides[: args.limit]
    return guides


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the resumable 39-guide Antikor Batch 2 extraction.")
    parser.add_argument("--resume", action="store_true", help="Continue from persisted page, image and result files.")
    parser.add_argument("--limit", type=int, metavar="N", help="Process at most N selected guides.")
    parser.add_argument("--slug", help="Process one selected guide by exact slug.")
    parser.add_argument("--retry-failed", action="store_true", help="Retry only failed/review-required guides.")
    parser.add_argument("--dry-run", action="store_true", help="Refresh inventory/manifest without images or model calls.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.slug and args.limit is not None:
        parser.error("--slug and --limit cannot be combined")
    return args


def run(args: argparse.Namespace) -> int:
    started = perf_counter()
    logger = configure_logging()
    settings = ExtractionSettings.from_environment()
    for name in ("candidates", "vision_results", "reports", "failed"):
        (BATCH_ROOT / name).mkdir(parents=True, exist_ok=True)
    with PageLoader(timeout=45, retries=3, rate_limit_seconds=0.5) as loader:
        manifest = build_or_refresh_manifest(loader, resume=args.resume or args.retry_failed or bool(args.slug))
        progress = ProgressTracker(manifest, started)
        targets = select_targets(manifest, args)
        progress.write()
        counts = Counter(str(x["category_key"]) for x in manifest["guides"])
        logger.info("Batch 2 selected=%s categories=%s targets=%s", len(manifest["guides"]), dict(counts), len(targets))
        if args.dry_run:
            logger.info("Dry run complete; no page images or model calls were made")
            return 0
        parser = GuidePageParser()
        prompt = ROOT / "tools" / "visual_guide_extractor" / "prompts" / "vision_prompt.txt"
        qwen = QwenVisionAdapter(
            settings.ollama_host, settings.vision_model, prompt,
            settings.request_timeout, settings.vision_context_window,
        )
        try:
            for item in targets:
                item.update(status="processing", started_at=item.get("started_at") or utc_now(), error=None)
                progress.write(item)
                logger.info("Starting %s (%s)", item["slug"], item["source_url"])
                try:
                    page = crawl_page(item, loader, parser)
                    item.update(
                        estimated_screenshot_count=len(page.image_blocks),
                        expected_complexity=complexity(len(page.image_blocks)), status="crawled",
                    )
                    progress.write(item)
                    vision = analyze_images(item, page, qwen, progress)
                    item["status"] = "vision_complete"
                    progress.write(item)
                    generate_candidate(item, page, vision, settings, progress)
                    item.update(status="completed", completed_at=utc_now())
                    logger.info("Completed %s status=%s", item["slug"], item["final_status"])
                except KeyboardInterrupt:
                    item.update(status="interrupted", error="Interrupted by user; run again with --resume")
                    progress.write(item)
                    logger.warning("Interrupted safely; cached outputs were retained")
                    return 130
                except Exception as exc:
                    item.update(
                        status="failed", final_status="failed", completed_at=utc_now(),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    logger.exception("Guide failed without stopping batch: %s", item["slug"])
                progress.write(item)
        finally:
            try:
                qwen.unload()
            finally:
                qwen.close()
        progress.write()
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
