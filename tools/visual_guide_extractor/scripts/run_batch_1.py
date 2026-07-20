"""Extract the first economical batch of unpromoted Antikor guides."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

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
from tools.visual_guide_extractor.vision import QwenVisionAdapter
from app.knowledge.evidence import has_usable_evidence, is_placeholder_line

GUIDE_ROOT = "https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/"
BATCH_ROOT = ROOT / "work" / "visual_guide_extraction" / "batch_1"
PREFERRED_CATEGORIES = (
    "anlik-gozlem", "araclar", "bildirim-yonetimi", "dns-denetimi",
    "dmz-yonetimi", "performans", "hotspot-islemleri",
    "karantina-ve-saldiri-tespit-yonetimi",
    "kimlik-dogrulama-kurallari", "sd-wan",
)
CATEGORY_NAMES = {
    "anlik-gozlem": "Anlık Gözlem", "araclar": "Araçlar",
    "bildirim-yonetimi": "Bildirim Yönetimi", "dns-denetimi": "DNS Denetimi",
    "dmz-yonetimi": "DMZ Yönetimi", "performans": "Performans",
    "hotspot-islemleri": "Hotspot İşlemleri",
    "karantina-ve-saldiri-tespit-yonetimi": "Karantina ve Saldırı Tespit Yönetimi",
    "kimlik-dogrulama-kurallari": "Kimlik Doğrulama Kuralları", "sd-wan": "SD-WAN",
}


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    path = "/".join(segment for segment in parts.path.split("/") if segment)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), "/" + path + "/", "", ""))


def slugify(value: str) -> str:
    value = value.replace("ı", "i").replace("İ", "I")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def discover(html: str) -> list[dict[str, object]]:
    root = normalize_url(GUIDE_ROOT)
    root_parts = urlsplit(root)
    root_path = root_parts.path
    found: dict[str, dict[str, object]] = {}
    for anchor in BeautifulSoup(html, "html.parser").select("a[href]"):
        url = normalize_url(urljoin(root, anchor.get("href", "")))
        parts = urlsplit(url)
        if parts.netloc != root_parts.netloc or not parts.path.startswith(root_path):
            continue
        relative = unquote(parts.path[len(root_path):]).strip("/")
        segments = relative.split("/")
        title = anchor.get_text(" ", strip=True)
        if len(segments) != 2 or not title:
            continue
        category, raw_slug = segments
        found[url.casefold()] = {
            "title": title, "source_url": url, "category": CATEGORY_NAMES.get(
                category.casefold(), category.replace("-", " ").title()
            ), "category_key": category.casefold(), "slug": slugify(raw_slug),
        }
    return sorted(found.values(), key=lambda item: (str(item["category_key"]), str(item["title"]).casefold()))


def promoted_urls() -> set[str]:
    urls: set[str] = set()
    for path in (ROOT / "knowledge_base" / "guides" / "antikor_v2").rglob("*.md"):
        match = re.search(r"^-\s+Sayfa:\s+(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            urls.add(normalize_url(match.group(1)))
    return urls


def build_inventory(html: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    promoted = promoted_urls()
    inventory = discover(html)
    selected: list[dict[str, object]] = []
    for item in inventory:
        is_promoted = normalize_url(str(item["source_url"])) in promoted
        include = not is_promoted and item["category_key"] in PREFERRED_CATEGORIES
        item.update({
            "current_extraction_status": "promoted" if is_promoted else "remaining",
            "already_promoted": is_promoted,
            "reason": (
                "excluded_already_promoted" if is_promoted else
                "included_complete_reliable_category_batch_1" if include else
                "excluded_deferred_to_later_batch"
            ),
        })
        if include:
            selected.append(item)
    if not 45 <= len(selected) <= 50:
        raise RuntimeError(f"Batch selection must contain 45-50 pages, got {len(selected)}")
    save_json(BATCH_ROOT / "remaining_inventory.json", inventory)
    return inventory, selected


def load_vision(directory: Path) -> list[VisionExtraction]:
    return [
        VisionExtraction.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("image-*.json"))
    ]


def markdown_checks(path: Path, expected_url: str) -> list[str]:
    if not path.exists():
        return ["markdown_missing"]
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not re.search(r"^#\s+\S", text, re.MULTILINE): failures.append("title_missing")
    if normalize_url(expected_url) not in normalize_url(text.split("Sayfa:", 1)[-1].splitlines()[0].strip()) if "Sayfa:" in text else True:
        failures.append("source_url_missing_or_mismatched")
    if not text.strip(): failures.append("empty_file")
    if len(text.strip()) < 220: failures.append("suspiciously_short")
    sections = re.split(r"^##\s+.+?\s*$", text, flags=re.MULTILINE)[1:]
    if not any(has_usable_evidence(section) for section in sections):
        failures.append("no_usable_evidence_section")
    if any(is_placeholder_line(line) for line in text.splitlines()):
        failures.append("placeholder_evidence_present")
    if any(marker in text for marker in ("Ã", "Ä", "Å", "??")):
        failures.append("turkish_text_corruption")
    if not re.search(r"^##\s+Kaynak bilgisi\s*$", text, re.MULTILINE):
        failures.append("source_metadata_missing")
    return failures


def complexity(image_count: int) -> str:
    return "complex" if image_count >= 6 else "medium" if image_count >= 3 else "simple"


def run() -> dict[str, object]:
    started = perf_counter()
    settings = ExtractionSettings.from_environment()
    for name in ("candidates", "vision_results", "reports", "failed"):
        (BATCH_ROOT / name).mkdir(parents=True, exist_ok=True)
    parser = GuidePageParser()
    with PageLoader(timeout=45, retries=3, rate_limit_seconds=0.5) as loader:
        inventory, selected = build_inventory(loader.load_page(GUIDE_ROOT))
        prior_manifest = {}
        manifest_path = BATCH_ROOT / "batch_manifest.json"
        if manifest_path.exists():
            prior_manifest = {x["source_url"]: x for x in json.loads(manifest_path.read_text(encoding="utf-8")).get("guides", [])}
        manifest: list[dict[str, object]] = []
        for page in selected:
            prior = prior_manifest.get(page["source_url"], {})
            item = {**page, "estimated_screenshot_count": prior.get("estimated_screenshot_count", 0),
                    "expected_complexity": prior.get("expected_complexity", "unknown"),
                    "status": prior.get("status", "selected"), "final_status": prior.get("final_status", "pending"),
                    "confidence": prior.get("confidence"), "error": prior.get("error"),
                    "retry_attempts": prior.get("retry_attempts", 0), "retry_records": prior.get("retry_records", [])}
            manifest.append(item)
        save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})

        for item in manifest:
            page_dir = BATCH_ROOT / "vision_results" / str(item["category_key"]) / str(item["slug"])
            page_json = page_dir / "page.json"
            if page_json.exists():
                page = GuidePage.model_validate_json(page_json.read_text(encoding="utf-8"))
                item.update(estimated_screenshot_count=len(page.image_blocks), expected_complexity=complexity(len(page.image_blocks)))
                continue
            try:
                page = parser.parse(loader.load_page(str(item["source_url"])), str(item["source_url"]))
                image_dir = page_dir / "images"
                for block in page.image_blocks:
                    if block.image_url is None or block.image_index is None: continue
                    image_path = loader.download_image(block.image_url, image_dir)
                    block.local_image_path = image_path.relative_to(ROOT).as_posix()
                save_json(page_json, page.model_dump(mode="json"))
                item.update(status="crawled", estimated_screenshot_count=len(page.image_blocks),
                            expected_complexity=complexity(len(page.image_blocks)), title=page.page_title, error=None)
            except Exception as exc:
                item.update(status="extraction_failed", final_status="extraction_failed", error=f"{type(exc).__name__}: {exc}")
            save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})

    prompt_root = ROOT / "tools" / "visual_guide_extractor" / "prompts"
    qwen = QwenVisionAdapter(settings.ollama_host, settings.vision_model, prompt_root / "vision_prompt.txt", settings.request_timeout, settings.vision_context_window)
    qwen_calls = qwen_seconds = 0
    try:
        for item in manifest:
            if item["status"] == "extraction_failed": continue
            page_dir = BATCH_ROOT / "vision_results" / str(item["category_key"]) / str(item["slug"])
            page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8"))
            failed = False
            for block in page.image_blocks:
                result_path = page_dir / f"image-{block.image_index}.json"
                if result_path.exists(): continue
                for attempt in range(1, 3):
                    tick = perf_counter(); qwen_calls += 1
                    try:
                        result = qwen.analyze(ROOT / str(block.local_image_path), page.page_title, int(block.image_index),
                            page.context_for_image(int(block.image_index)), {"source_url": page.source_url, "image_url": block.image_url, "alt_text": block.alt_text})
                        qwen_seconds += perf_counter() - tick
                        save_json(result_path, result.model_dump(mode="json"))
                        if attempt > 1:
                            item["retry_records"].append({"initial_failure_reason": item.get("error"), "retry_method": "qwen_image_retry", "retry_attempts": attempt - 1, "final_status": "recovered"})
                        break
                    except Exception as exc:
                        qwen_seconds += perf_counter() - tick
                        item.update(error=f"{type(exc).__name__}: {exc}")
                        if attempt == 2:
                            failed = True
                            item["retry_attempts"] = int(item["retry_attempts"]) + 1
                            item["retry_records"].append({"initial_failure_reason": item["error"], "retry_method": "qwen_image_retry", "retry_attempts": 1, "final_status": "failed"})
                save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})
                if failed: break
            item.update(status="extraction_failed" if failed else "vision_complete", final_status="extraction_failed" if failed else "pending")
            save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})
    finally:
        try: qwen.unload()
        finally: qwen.close()

    formatter = MarkdownGenerator(); validator = FinalQualityValidator(); decisions = FallbackDecisionEngine()
    normalizer: GemmaNormalizer | None = None; gemma_calls = 0; gemma_seconds = 0.0
    try:
        for item in manifest:
            if item["status"] == "extraction_failed": continue
            page_dir = BATCH_ROOT / "vision_results" / str(item["category_key"]) / str(item["slug"])
            page = GuidePage.model_validate_json((page_dir / "page.json").read_text(encoding="utf-8")); vision = load_vision(page_dir)
            deterministic = formatter.build_deterministic_guide(page, vision); initial = validator.validate(page, vision, deterministic)
            decision = decisions.decide(confidence_score=initial.confidence_score, warning_count=len(initial.warnings),
                uncertainty_count=len(deterministic.uncertainties), unsupported_claim_count=len(initial.removed_unsupported_claims),
                step_count=len(deterministic.ordered_steps), image_count=len(page.image_blocks))
            selected_guide: NormalizedGuide = deterministic
            if decision.use_gemma:
                try:
                    normalized_path = page_dir / "gemma_normalized.json"
                    if normalized_path.exists(): selected_guide = NormalizedGuide.model_validate_json(normalized_path.read_text(encoding="utf-8"))
                    else:
                        if normalizer is None: normalizer = GemmaNormalizer(settings.ollama_host, settings.normalization_model, prompt_root / "normalization_prompt.txt", max(settings.request_timeout, 600))
                        tick = perf_counter(); gemma_calls += 1; selected_guide = normalizer.normalize(page, vision); gemma_seconds += perf_counter() - tick
                        save_json(normalized_path, selected_guide.model_dump(mode="json"))
                except Exception as exc:
                    item["retry_records"].append({"initial_failure_reason": f"Gemma: {exc}", "retry_method": "deterministic_fallback", "retry_attempts": 0, "final_status": "deterministic_retained"})
                    selected_guide = deterministic
            final = validator.validate(page, vision, selected_guide)
            # Gemma is only a fallback editor. Never replace stronger deterministic
            # evidence with a lower-quality or rejected normalization result.
            if decision.use_gemma and (not final.approved or final.confidence_score < initial.confidence_score):
                item["retry_records"].append({
                    "initial_failure_reason": "gemma_quality_regression",
                    "retry_method": "retain_deterministic_result",
                    "retry_attempts": 0,
                    "final_status": "deterministic_retained",
                })
                final = initial

            # The validator may safely remove language/claim violations. Validate
            # that sanitized evidence once more before requesting another model call.
            if not final.approved:
                sanitized_retry = validator.validate(page, vision, final.sanitized_guide)
                if sanitized_retry.approved and sanitized_retry.confidence_score >= final.confidence_score:
                    item["retry_attempts"] = int(item["retry_attempts"]) + 1
                    item["retry_records"].append({
                        "initial_failure_reason": "final_quality_not_approved",
                        "retry_method": "deterministic_sanitized_revalidation",
                        "retry_attempts": 1,
                        "final_status": "recovered",
                    })
                    final = sanitized_retry
            candidate = BATCH_ROOT / "candidates" / str(item["category_key"]) / f"{item['slug']}.md"
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(formatter.generate_pilot_approved(final.sanitized_guide, final.confidence_score), encoding="utf-8")
            failures = markdown_checks(candidate, str(item["source_url"]))
            if not final.approved: failures.append("final_quality_not_approved")
            severe = [x for x in failures if x not in {"suspiciously_short", "no_usable_evidence_section"}]
            status = "approved_candidate" if not failures else "source_limited" if not severe else "needs_targeted_retry"
            item.update(status="completed", final_status=status, confidence=final.confidence_score,
                        error="; ".join(failures) if failures else None, candidate_path=candidate.relative_to(ROOT).as_posix(),
                        fallback_reasons=decision.reasons, used_gemma=decision.use_gemma)
            save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})
    finally:
        if normalizer:
            try: normalizer.unload()
            finally: normalizer.close()

    # Candidates that still fail after the bounded deterministic recovery require
    # human review; do not spend additional vision/normalization calls on them.
    for item in manifest:
        if item["final_status"] != "needs_targeted_retry": continue
        if int(item["retry_attempts"]) == 0:
            item["retry_attempts"] = 1
            item["retry_records"].append({"initial_failure_reason": item["error"], "retry_method": "bounded_deterministic_recovery", "retry_attempts": 1, "final_status": "still_failed"})
        item["final_status"] = "extraction_failed"
    save_json(manifest_path, {"selected_guide_count": len(manifest), "guides": manifest})

    approved = [x for x in manifest if x["final_status"] == "approved_candidate"]
    validation_cases = []
    intent_sections = (("navigation", "Menü yolu"), ("first_action", "Görünür kontroller"),
                       ("field_listing", "Alanlar"), ("procedure", "Kullanım adımları"))
    for item in approved:
        text = (ROOT / str(item["candidate_path"])).read_text(encoding="utf-8")
        for intent, section in intent_sections:
            match = re.search(rf"^##\s+{re.escape(section)}\s*$([\s\S]*?)(?=^##\s+|\Z)", text, re.MULTILINE)
            if match and match.group(1).strip() and not any(x["intent"] == intent and x["category"] == item["category"] for x in validation_cases):
                required = re.findall(r"`([^`]+)`", match.group(1))[:3]
                if not required: required = [line.strip("- 0123456789.") for line in match.group(1).splitlines() if line.strip().startswith(("-", "1."))][:2]
                validation_cases.append({"title": item["title"], "category": item["category"], "intent": intent,
                    "expected_section": section, "required_terms": required, "source_url": item["source_url"],
                    "candidate_path": item["candidate_path"], "passed": bool(required), "mode": "pre_promotion_structured_source_grounding"})
                break
        if len(validation_cases) >= 10: break

    counts = Counter(str(x["final_status"]) for x in manifest); screenshots = sum(int(x["estimated_screenshot_count"]) for x in manifest)
    summary = {"selected_guide_count": len(manifest), "extracted_guide_count": sum(x["status"] == "completed" for x in manifest),
        "approved_candidate_count": counts["approved_candidate"], "targeted_retry_count": sum(int(x["retry_attempts"]) > 0 for x in manifest),
        "source_limited_count": counts["source_limited"], "failed_count": counts["extraction_failed"],
        "category_distribution": dict(Counter(str(x["category"]) for x in manifest)), "total_screenshots": screenshots,
        "average_screenshots_per_guide": round(screenshots / max(len(manifest), 1), 2), "vision_model_calls": qwen_calls,
        "fallback_model_calls": gemma_calls, "vision_duration_seconds": round(qwen_seconds, 3), "fallback_duration_seconds": round(gemma_seconds, 3),
        "lightweight_validation": {"mode": "pre_promotion_structured_source_grounding", "total": len(validation_cases),
            "passed": sum(x["passed"] for x in validation_cases), "failed": sum(not x["passed"] for x in validation_cases), "cases": validation_cases},
        "estimated_remaining_guide_count": sum(not bool(x["already_promoted"]) for x in inventory) - len(manifest),
        "processing_duration_seconds": round(perf_counter() - started, 3),
        "ready_for_promotion": counts["approved_candidate"] == len(manifest) and len(validation_cases) >= 8 and all(x["passed"] for x in validation_cases)}
    save_json(BATCH_ROOT / "batch_summary.json", summary)
    lines = ["# Batch 1 Özeti", "", *[f"- {key}: {value}" for key, value in summary.items() if key not in {"category_distribution", "lightweight_validation"}], "", "## Kategori dağılımı", ""]
    lines += [f"- {key}: {value}" for key, value in summary["category_distribution"].items()]
    (BATCH_ROOT / "batch_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    retry_lines = ["# Başarısız veya Retry Gerektiren Rehberler", ""]
    retry_lines += [f"- {x['title']} ({x['final_status']}): {x.get('error') or 'retry ile kurtarıldı'}" for x in manifest if x["final_status"] != "approved_candidate" or int(x["retry_attempts"]) > 0] or ["- Yok."]
    (BATCH_ROOT / "failed_or_retry_guides.md").write_text("\n".join(retry_lines) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
