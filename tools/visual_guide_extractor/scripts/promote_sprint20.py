"""Validate and promote approved Sprint 19 Markdown into the knowledge base."""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

SOURCE = REPOSITORY_ROOT / "work" / "visual_guide_extraction" / "sprint19" / "approved"
WORK = REPOSITORY_ROOT / "work" / "visual_guide_extraction" / "sprint20"
DESTINATION = REPOSITORY_ROOT / "knowledge_base" / "guides" / "antikor_v2"
MANIFEST = REPOSITORY_ROOT / "work" / "visual_guide_extraction" / "sprint19_manifest.json"
REQUIRED_SECTIONS = (
    "Kapsam", "Menü yolu", "Kullanım adımları", "Alanlar",
    "Görünür kontroller", "Uyarılar", "Kaynak bilgisi",
)
PLACEHOLDERS = {
    "Kaynak sayfadaki görünür içerik.",
    "- Görünür menü yolu bulunamadı.",
    "- Görünür kullanım adımı bulunamadı.",
    "- Görünür alan bulunamadı.",
    "- Görünür kontrol bulunamadı.",
    "- Görünür uyarı bulunamadı.",
}


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate() -> tuple[dict[str, object], list[Path]]:
    files = sorted(SOURCE.rglob("*.md"))
    all_files = [path for path in SOURCE.rglob("*") if path.is_file()]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    approved_keys = {item["page_key"] for item in manifest if item["approval_status"] == "approved"}
    invalid: list[str] = []
    titles: list[str] = []
    urls: list[str] = []
    confidences: list[float] = []
    missing_sections = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        title = re.search(r"(?m)^#\s+(.+)$", text)
        source = re.search(r"(?m)^- Sayfa:\s+(https?://\S+)\s*$", text)
        confidence = re.search(r"(?m)^- Güven puanı:\s+([01](?:\.\d+)?)\s*$", text)
        missing = [section for section in REQUIRED_SECTIONS if f"## {section}" not in text]
        missing_sections += len(missing)
        if not title or not source or not confidence or missing or path.stem not in approved_keys:
            invalid.append(path.relative_to(SOURCE).as_posix())
            continue
        titles.append(title.group(1).strip())
        urls.append(source.group(1).strip())
        confidences.append(float(confidence.group(1)))
    title_duplicates = sum(count - 1 for count in Counter(titles).values() if count > 1)
    url_duplicates = sum(count - 1 for count in Counter(urls).values() if count > 1)
    non_markdown = [path.relative_to(SOURCE).as_posix() for path in all_files if path.suffix.lower() != ".md"]
    report = {
        "approved_file_count": len(files),
        "invalid_file_count": len(invalid) + len(non_markdown),
        "invalid_files": invalid,
        "non_markdown_files": non_markdown,
        "duplicate_title_count": title_duplicates,
        "duplicate_source_url_count": url_duplicates,
        "missing_section_count": missing_sections,
        "minimum_confidence": min(confidences, default=0.0),
        "average_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
    }
    save_json(WORK / "pre_promotion_validation.json", report)
    critical = len(files) != 42 or report["invalid_file_count"] or title_duplicates or url_duplicates or missing_sections
    if critical:
        raise RuntimeError("Critical pre-promotion validation failed")
    return report, files


def clean_markdown(text: str) -> str:
    lines = text.splitlines()
    title_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, current))
            current_heading = line[3:].strip()
            current = []
        elif current_heading is None:
            title_lines.append(line)
        else:
            current.append(line)
    if current_heading is not None:
        sections.append((current_heading, current))

    output = [line for line in title_lines if "TASLAK:" not in line]
    for heading, content in sections:
        cleaned = [
            line for line in content
            if line.strip() not in PLACEHOLDERS
            and "Otomatik kalite kapısından geçmiş taslak" not in line
        ]
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        if not cleaned:
            continue
        while output and not output[-1].strip():
            output.pop()
        output.extend(["", f"## {heading}", "", *cleaned])
    return "\n".join(output).strip() + "\n"


def run() -> dict[str, object]:
    report, files = validate()
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    for source in files:
        destination = DESTINATION / source.relative_to(SOURCE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(clean_markdown(source.read_text(encoding="utf-8")), encoding="utf-8")
    return {**report, "promoted_file_count": len(files), "destination": str(DESTINATION)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
