"""Run the three-page Visual Guide Extraction proof of concept."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.visual_guide_extractor.config.settings import ExtractionSettings
from tools.visual_guide_extractor.crawler import GuidePageParser, PageLoader
from tools.visual_guide_extractor.formatter.markdown_generator import MarkdownGenerator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, VisionExtraction
from tools.visual_guide_extractor.vision import QwenVisionAdapter


POC_PAGES = (
    (
        "simple_text",
        "https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/nat-yapilandirmasi/dinamik-nat/",
    ),
    (
        "form_ui_heavy",
        "https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/guvenlik-ayarlari/guvenlik-kurallari/",
    ),
    (
        "multi_screenshot_steps",
        "https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/02-hizli-kurulum-kilavuzu/",
    ),
)


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")


def _save_page(page: GuidePage, output_path: Path) -> None:
    output_path.write_text(page.model_dump_json(indent=2) + "\n", encoding="utf-8")


def run() -> dict[str, object]:
    """Process exactly the three approved representative pages."""
    settings = ExtractionSettings.from_environment()
    settings.ensure_work_directories()
    parser = GuidePageParser()
    formatter = MarkdownGenerator()
    prompt_path = REPOSITORY_ROOT / "tools" / "visual_guide_extractor" / "prompts" / "vision_prompt.txt"
    adapter = (
        QwenVisionAdapter(
            settings.ollama_host,
            settings.vision_model,
            prompt_path,
            settings.request_timeout,
            settings.vision_context_window,
        )
        if settings.run_vision
        else None
    )

    summary: dict[str, object] = {"vision_enabled": settings.run_vision, "pages": []}
    with PageLoader(timeout=settings.request_timeout) as loader:
        for page_key, url in POC_PAGES:
            html = loader.load_page(url)
            page = parser.parse(html, url)
            image_directory = settings.work_root / "images" / page_key
            vision_results: list[VisionExtraction] = []

            for block in page.image_blocks:
                if block.image_url is None or block.image_index is None:
                    continue
                local_path = loader.download_image(block.image_url, image_directory)
                block.local_image_path = local_path.relative_to(settings.repository_root).as_posix()
                if adapter is not None:
                    result = adapter.analyze(
                        local_path,
                        page.page_title,
                        block.image_index,
                        page.html_context(),
                    )
                    vision_results.append(result)
                    result_path = (
                        settings.work_root
                        / "vision_results"
                        / f"{page_key}-image-{block.image_index}.json"
                    )
                    result_path.write_text(
                        result.model_dump_json(indent=2) + "\n",
                        encoding="utf-8",
                    )

            _save_page(page, settings.work_root / "pages" / f"{page_key}.json")
            preview = formatter.generate(page, vision_results)
            (settings.work_root / "reports" / f"{page_key}-future-preview.md").write_text(
                preview,
                encoding="utf-8",
            )
            summary["pages"].append(
                {
                    "key": page_key,
                    "title": page.page_title,
                    "url": url,
                    "blocks": len(page.blocks),
                    "images": len(page.image_blocks),
                    "vision_results": len(vision_results),
                }
            )

    summary_path = settings.work_root / "reports" / "poc_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
