"""Checkpointed critical-category extraction pilot for Antikor v2."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from time import perf_counter

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.visual_guide_extractor.config.settings import ExtractionSettings
from tools.visual_guide_extractor.crawler import CriticalCategoryDiscovery, GuidePageParser, PageLoader
from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.normalization import GemmaNormalizer
from tools.visual_guide_extractor.quality import FallbackDecisionEngine, FinalQualityValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction
from tools.visual_guide_extractor.vision import QwenVisionAdapter

GUIDE_ROOT = "https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def slugify(value: str) -> str:
    value = value.replace("ı", "i").replace("İ", "I")
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def load_vision(directory: Path) -> list[VisionExtraction]:
    return [VisionExtraction.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("image-*.json"))]


def run() -> dict[str, object]:
    run_started = perf_counter()
    settings = ExtractionSettings.from_environment()
    sprint_root = settings.work_root / "sprint19"
    manifest_path = settings.work_root / "sprint19_manifest.json"
    for directory in ("approved", "rejected", "vision_results", "reports"):
        (sprint_root / directory).mkdir(parents=True, exist_ok=True)

    discovery = CriticalCategoryDiscovery()
    parser = GuidePageParser()
    with PageLoader(timeout=45, retries=3, rate_limit_seconds=0.5) as loader:
        pages = discovery.discover(loader.load_page(GUIDE_ROOT), GUIDE_ROOT)
        existing = {}
        if manifest_path.exists():
            existing = {item["url"]: item for item in json.loads(manifest_path.read_text(encoding="utf-8"))}
        manifest = []
        for page in pages:
            prior = existing.get(page.url, {})
            manifest.append({
                "page_title": page.title, "category": page.category,
                "category_key": page.category_key, "url": page.url,
                "page_key": prior.get("page_key", slugify(page.title)),
                "status": prior.get("status", "discovered"),
                "image_count": prior.get("image_count", 0),
                "confidence": prior.get("confidence"),
                "approval_status": prior.get("approval_status", "pending"),
                "error": prior.get("error"),
            })
        save_json(manifest_path, manifest)

        for item in manifest:
            page_dir = sprint_root / "vision_results" / item["page_key"]
            page_json = page_dir / "page.json"
            if page_json.exists() and item["status"] not in {"crawl_failed", "discovered"}:
                continue
            try:
                guide = parser.parse(loader.load_page(item["url"]), item["url"])
                image_dir = page_dir / "images"
                for block in guide.image_blocks:
                    if block.image_url is None or block.image_index is None:
                        continue
                    image_path = loader.download_image(block.image_url, image_dir)
                    block.local_image_path = image_path.relative_to(REPOSITORY_ROOT).as_posix()
                save_json(page_json, guide.model_dump(mode="json"))
                item.update(status="crawled", image_count=len(guide.image_blocks), page_title=guide.page_title, error=None)
            except Exception as exc:
                item.update(status="crawl_failed", approval_status="rejected", error=f"{type(exc).__name__}: {exc}")
            save_json(manifest_path, manifest)

    prompt_root = REPOSITORY_ROOT / "tools" / "visual_guide_extractor" / "prompts"
    qwen = QwenVisionAdapter(settings.ollama_host, settings.vision_model, prompt_root / "vision_prompt.txt", settings.request_timeout, settings.vision_context_window)
    qwen_calls = 0
    qwen_seconds = 0.0
    try:
        for item in manifest:
            if item["status"] == "crawl_failed":
                continue
            page_dir = sprint_root / "vision_results" / item["page_key"]
            page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8"))
            failed = False
            for block in page.image_blocks:
                result_path = page_dir / f"image-{block.image_index}.json"
                if result_path.exists():
                    continue
                try:
                    started = perf_counter()
                    result = qwen.analyze(
                        REPOSITORY_ROOT / str(block.local_image_path), page.page_title,
                        int(block.image_index), page.context_for_image(int(block.image_index)),
                        {"source_url": page.source_url, "image_url": block.image_url, "alt_text": block.alt_text},
                    )
                    qwen_seconds += perf_counter() - started
                    qwen_calls += 1
                    save_json(result_path, result.model_dump(mode="json"))
                    item["status"] = "vision_partial"
                    save_json(manifest_path, manifest)
                except Exception as exc:
                    failed = True
                    item.update(status="vision_failed", approval_status="rejected", error=f"{type(exc).__name__}: {exc}")
                    save_json(manifest_path, manifest)
                    break
            if not failed:
                item["status"] = "vision_complete"
                save_json(manifest_path, manifest)
    finally:
        try:
            qwen.unload()
        finally:
            qwen.close()

    formatter = MarkdownGenerator()
    validator = FinalQualityValidator()
    decision_engine = FallbackDecisionEngine()
    normalizer: GemmaNormalizer | None = None
    gemma_usage: list[dict[str, object]] = []
    unsupported_removed = 0
    warnings: list[str] = []
    gemma_calls = 0
    try:
        for item in manifest:
            if item["status"] in {"crawl_failed", "vision_failed"}:
                continue
            page_dir = sprint_root / "vision_results" / item["page_key"]
            page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8"))
            vision = load_vision(page_dir)
            deterministic = formatter.build_deterministic_guide(page, vision)
            initial = validator.validate(page, vision, deterministic)
            decision = decision_engine.decide(
                confidence_score=initial.confidence_score, warning_count=len(initial.warnings),
                uncertainty_count=len(deterministic.uncertainties),
                unsupported_claim_count=len(initial.removed_unsupported_claims),
                step_count=len(deterministic.ordered_steps), image_count=len(page.image_blocks),
            )
            selected = deterministic
            gemma_duration = 0.0
            if decision.use_gemma:
                normalized_path = page_dir / "gemma_normalized.json"
                try:
                    if normalized_path.exists():
                        selected = NormalizedGuide.model_validate_json(normalized_path.read_text(encoding="utf-8"))
                    else:
                        if normalizer is None:
                            normalizer = GemmaNormalizer(settings.ollama_host, settings.normalization_model, prompt_root / "normalization_prompt.txt", max(settings.request_timeout, 600))
                        started = perf_counter()
                        selected = normalizer.normalize(page, vision)
                        gemma_duration = perf_counter() - started
                        gemma_calls += 1
                        save_json(normalized_path, selected.model_dump(mode="json"))
                except Exception as exc:
                    warnings.append(f"{page.page_title}: Gemma fallback failed: {exc}")
                    selected = deterministic
            gemma_usage.append({"page": page.page_title, "url": page.source_url, "reason": decision.reasons, "used_gemma": decision.use_gemma, "duration_seconds": round(gemma_duration, 3)})
            final = validator.validate(page, vision, selected)
            unsupported_removed += len(final.removed_unsupported_claims)
            item.update(confidence=final.confidence_score, approval_status="approved" if final.approved else "rejected", status="completed")
            category_dir = sprint_root / "approved" / item["category_key"]
            if final.approved:
                category_dir.mkdir(parents=True, exist_ok=True)
                (category_dir / f"{item['page_key']}.md").write_text(formatter.generate_pilot_approved(final.sanitized_guide, final.confidence_score), encoding="utf-8")
            else:
                rejected_dir = sprint_root / "rejected"
                rejected_dir.mkdir(parents=True, exist_ok=True)
                save_json(rejected_dir / f"{item['page_key']}.json", final.model_dump(mode="json"))
            save_json(manifest_path, manifest)
    finally:
        if normalizer is not None:
            try:
                normalizer.unload()
            finally:
                normalizer.close()

    save_json(sprint_root / "reports" / "gemma_usage.json", gemma_usage)
    processed = [item for item in manifest if item["status"] == "completed"]
    approved = [item for item in processed if item["approval_status"] == "approved"]
    rejected = [item for item in manifest if item["approval_status"] == "rejected"]
    low = [item for item in processed if float(item["confidence"] or 0) < 0.85]
    review_lines = ["# Sprint 19 Manuel İnceleme Kuyruğu", ""]
    for heading, values in (("Reddedilen sayfalar", rejected), ("Düşük güvenli sayfalar", low)):
        review_lines.extend([f"## {heading}", ""])
        review_lines.extend([*(f"- [{item['page_title']}]({item['url']}) — durum: {item['status']}, güven: {item['confidence']}" for item in values)] or ["- Yok."])
        review_lines.append("")
    (sprint_root / "reports" / "manual_review_queue.md").write_text("\n".join(review_lines), encoding="utf-8")
    duration = round(perf_counter() - run_started, 3)
    quality = {
        "discovered_pages": len(manifest), "processed_pages": len(processed),
        "image_count": sum(int(item["image_count"]) for item in manifest),
        "qwen_calls": qwen_calls, "gemma_calls": gemma_calls,
        "approved_pages": len(approved), "rejected_pages": len(rejected),
        "average_confidence": round(sum(float(item["confidence"]) for item in processed) / len(processed), 3) if processed else 0.0,
        "warnings": warnings, "unsupported_claims_removed": unsupported_removed,
        "processing_duration_seconds": duration,
    }
    save_json(sprint_root / "reports" / "sprint19_quality_report.json", quality)
    return quality


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
