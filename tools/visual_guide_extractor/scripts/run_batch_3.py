"""Prepare and run the final resumable Antikor extraction batch locally.

The long-running mode is intended for manual PowerShell execution. Batch 2's
proven crawl, cache, Qwen, Gemma-fallback and quality functions are reused;
this module owns only final-inventory selection and Batch 3 orchestration.
"""
from __future__ import annotations

import argparse
import json
import logging
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
from tools.visual_guide_extractor.scripts import run_batch_1 as batch_1
from tools.visual_guide_extractor.scripts import run_batch_2 as batch_2
from tools.visual_guide_extractor.vision import QwenVisionAdapter

BATCH_ROOT = ROOT / "work" / "visual_guide_extraction" / "batch_3"
MANIFEST_PATH = BATCH_ROOT / "batch_manifest.json"
INVENTORY_PATH = BATCH_ROOT / "remaining_inventory.json"
PROGRESS_PATH = BATCH_ROOT / "progress.json"
FAILED_PATH = BATCH_ROOT / "failed_guides.json"
LOG_PATH = BATCH_ROOT / "run.log"
SELECTED_CATEGORIES = ("raporlar", "sistem-ayarlari", "tanimlar")
CATEGORY_NAMES = {
    "raporlar": "Raporlar",
    "sistem-ayarlari": "Sistem Ayarları",
    "tanimlar": "Tanımlar",
}

# Batch 2 helpers resolve these module globals at runtime. Redirect them before
# any helper is called, keeping every generated artifact inside batch_3/.
batch_2.BATCH_ROOT = BATCH_ROOT
batch_2.MANIFEST_PATH = MANIFEST_PATH
batch_2.PROGRESS_PATH = PROGRESS_PATH
batch_2.FAILED_PATH = FAILED_PATH
batch_2.LOG_PATH = LOG_PATH
batch_1.CATEGORY_NAMES.update(CATEGORY_NAMES)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def configure_logging() -> logging.Logger:
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("batch_3")
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


def fresh_inventory(loader: PageLoader) -> tuple[dict[str, object], list[dict[str, object]]]:
    discovered = batch_2.discover(loader.load_page(batch_2.GUIDE_ROOT))
    promoted = batch_2.promoted_urls()
    seen_urls: set[str] = set()
    seen_slugs: set[str] = set()
    selected: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    reasons: Counter[str] = Counter()
    for raw in discovered:
        item = dict(raw)
        url = batch_2.normalize_url(str(item["source_url"]))
        slug = str(item["slug"]).casefold()
        reason: str | None = None
        if url in promoted:
            reason = "already_promoted"
        elif url in seen_urls:
            reason = "duplicate_source_url"
        elif slug in seen_slugs:
            reason = "duplicate_slug"
        elif item["category_key"] not in SELECTED_CATEGORIES:
            reason = "non_final_batch_category"
        if reason:
            reasons[reason] += 1
            excluded.append({**item, "included": False, "exclusion_reason": reason})
            continue
        seen_urls.add(url)
        seen_slugs.add(slug)
        selected.append({
            **item, "category": CATEGORY_NAMES[str(item["category_key"])],
            "included": True, "inclusion_reason": "valid_unpromoted_final_batch_guide",
            "estimated_screenshot_count": 0, "estimated_complexity": "unknown",
        })
    if not 35 <= len(selected) <= 40:
        raise RuntimeError(
            f"Expected approximately 35-40 final guides, discovered {len(selected)}; review inventory"
        )
    payload: dict[str, object] = {
        "generated_at": utc_now(), "total_source_guides": len(discovered),
        "already_promoted_count": reasons["already_promoted"],
        "selected_batch_3_count": len(selected), "excluded_count": len(excluded),
        "exclusion_reasons": dict(reasons), "selected_categories": list(SELECTED_CATEGORIES),
        "selected_guides": selected, "excluded_guides": excluded,
    }
    return payload, selected


def new_manifest_item(item: dict[str, object]) -> dict[str, object]:
    return {
        **item, "status": "selected", "final_status": "pending",
        "screenshots_processed": 0, "confidence": None, "used_gemma": False,
        "error": None, "started_at": None, "completed_at": None,
    }


def build_or_refresh_manifest(loader: PageLoader, resume: bool) -> dict[str, object]:
    inventory, selected = fresh_inventory(loader)
    prior: dict[str, dict[str, object]] = {}
    if resume and MANIFEST_PATH.exists():
        old = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        prior = {batch_2.normalize_url(str(x["source_url"])): x for x in old.get("guides", [])}
    parser = GuidePageParser()
    guides: list[dict[str, object]] = []
    for item in selected:
        saved = prior.get(batch_2.normalize_url(str(item["source_url"])))
        record = {**saved, **item} if saved else new_manifest_item(item)
        if not int(record.get("estimated_screenshot_count", 0)):
            try:
                page = parser.parse(loader.load_page(str(item["source_url"])), str(item["source_url"]))
                count = len(page.image_blocks)
                record.update(
                    title=page.page_title,
                    estimated_screenshot_count=count,
                    estimated_complexity=batch_2.complexity(count),
                )
            except Exception as exc:
                record["inventory_warning"] = f"{type(exc).__name__}: {exc}"
        guides.append(record)
    by_url = {str(x["source_url"]): x for x in guides}
    for item in inventory["selected_guides"]:
        record = by_url[str(item["source_url"])]
        item.update(
            estimated_screenshot_count=record["estimated_screenshot_count"],
            estimated_complexity=record["estimated_complexity"],
        )
    batch_2.save_json(INVENTORY_PATH, inventory)
    manifest = {
        "batch": 3, "generated_at": utc_now(), "selected_guide_count": len(guides),
        "selected_categories": list(SELECTED_CATEGORIES), "guides": guides,
    }
    batch_2.save_json(MANIFEST_PATH, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the resumable 38-guide final Antikor Batch 3 extraction."
    )
    parser.add_argument("--resume", action="store_true", help="Continue from persisted page, image and result files.")
    parser.add_argument("--limit", type=int, metavar="N", help="Process at most N selected guides.")
    parser.add_argument("--slug", help="Process one selected guide by exact slug.")
    parser.add_argument("--retry-failed", action="store_true", help="Retry only failed/review-required guides.")
    parser.add_argument("--dry-run", action="store_true", help="Refresh inventory/manifest without image or model calls.")
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
        manifest = build_or_refresh_manifest(
            loader, resume=args.resume or args.retry_failed or bool(args.slug)
        )
        progress = batch_2.ProgressTracker(manifest, started)
        targets = batch_2.select_targets(manifest, args)
        progress.write()
        counts = Counter(str(x["category_key"]) for x in manifest["guides"])
        logger.info(
            "Batch 3 selected=%s categories=%s targets=%s",
            len(manifest["guides"]), dict(counts), len(targets),
        )
        if args.dry_run:
            logger.info("Dry run complete; no images or model calls were made")
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
                    page = batch_2.crawl_page(item, loader, parser)
                    item.update(
                        estimated_screenshot_count=len(page.image_blocks),
                        estimated_complexity=batch_2.complexity(len(page.image_blocks)),
                        status="crawled",
                    )
                    progress.write(item)
                    vision = batch_2.analyze_images(item, page, qwen, progress)
                    item["status"] = "vision_complete"
                    progress.write(item)
                    batch_2.generate_candidate(item, page, vision, settings, progress)
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
