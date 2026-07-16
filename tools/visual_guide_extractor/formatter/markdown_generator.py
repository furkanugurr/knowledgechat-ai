"""Deterministic future Markdown preview generator."""

from __future__ import annotations

from collections.abc import Sequence

from tools.visual_guide_extractor.schemas.extraction import (
    GuidePage,
    NormalizedGuide,
    VisionExtraction,
)
from tools.visual_guide_extractor.quality.language_validation import LanguageValidator


class MarkdownGenerator:
    """Generate a review-only Markdown preview; never write to knowledge_base."""

    def build_deterministic_guide(
        self, page: GuidePage, vision_results: Sequence[VisionExtraction]
    ) -> NormalizedGuide:
        """Build guide data by copying evidence verbatim without model editing."""
        def unique(items, key):
            seen: set[str] = set()
            output = []
            for item in items:
                marker = key(item).strip().casefold()
                if marker and marker not in seen:
                    seen.add(marker)
                    output.append(item)
            return output

        controls = unique(
            [item for result in vision_results for item in result.controls],
            lambda item: item.name,
        )
        fields = unique(
            [item for result in vision_results for item in result.fields],
            lambda item: item.name,
        )
        language = LanguageValidator()
        controls = [
            item.model_copy(update={"description": item.name})
            if language.english_sentences([item.description]) else item
            for item in controls
        ]
        fields = [
            item.model_copy(update={"description": item.name})
            if language.english_sentences([item.description]) else item
            for item in fields
        ]
        paths = unique(
            [result.visible_navigation_path for result in vision_results if result.visible_navigation_path.strip()],
            lambda item: item,
        )
        return NormalizedGuide(
            page_title=page.page_title,
            source_url=page.source_url,
            overview=next((block.text for block in page.blocks if block.kind == "paragraph" and block.text), ""),
            navigation_paths=paths,
            controls=controls,
            fields=fields,
            ordered_steps=unique(
                [item for block in page.blocks if block.kind == "ordered_list" for item in block.items]
                + [item for result in vision_results for item in result.ordered_steps],
                lambda item: item,
            ),
            warnings=unique(
                [item for result in vision_results for item in result.warnings],
                lambda item: item,
            ),
            uncertainties=unique(
                [item for result in vision_results for item in result.uncertainties],
                lambda item: item,
            ),
        )

    def generate(self, page: GuidePage, vision_results: Sequence[VisionExtraction]) -> str:
        """Combine authoritative HTML text and validated observations."""
        lines = [
            f"# {page.page_title}",
            "",
            "> DRAFT: Review required. This file is not approved for indexing.",
            "",
            "## Source",
            "",
            f"- Page: {page.source_url}",
            "- Method: Static HTML plus structured screenshot analysis",
            "",
            "## Extracted guide content",
            "",
        ]
        for block in page.blocks:
            if block.kind == "heading" and block.level:
                lines.extend([f"{'#' * min(block.level + 1, 6)} {block.text}", ""])
            elif block.kind == "paragraph" and block.text:
                lines.extend([block.text, ""])
            elif block.kind in {"ordered_list", "unordered_list"}:
                for index, item in enumerate(block.items, start=1):
                    prefix = f"{index}." if block.kind == "ordered_list" else "-"
                    lines.append(f"{prefix} {item}")
                lines.append("")

        if vision_results:
            lines.extend(["## Screenshot observations", ""])
            for result in vision_results:
                heading = result.screen_name or f"Screenshot {result.image_index}"
                lines.extend([f"### {heading}", ""])
                if result.purpose:
                    lines.extend([result.purpose, ""])
                if result.visible_navigation_path:
                    lines.extend([f"Navigation: `{result.visible_navigation_path}`", ""])
                if result.ordered_steps:
                    lines.extend(["Steps:", ""])
                    lines.extend(
                        f"{index}. {step}"
                        for index, step in enumerate(result.ordered_steps, start=1)
                    )
                    lines.append("")
                if result.uncertainties:
                    lines.extend(["Uncertainties:", ""])
                    lines.extend(f"- {item}" for item in result.uncertainties)
                    lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def generate_normalized(self, guide: NormalizedGuide) -> str:
        """Render Gemma's validated editorial JSON as review-only Markdown."""
        lines = [
            f"# {guide.page_title}",
            "",
            "> DRAFT: Gemma-edited output. Human review is required before indexing.",
            "",
            "## Source",
            "",
            f"- Page: {guide.source_url}",
            "- Evidence: Static HTML and validated Qwen JSON only",
        ]
        if guide.overview:
            lines.extend(["", "## Overview", "", guide.overview])
        if guide.navigation_paths:
            lines.extend(["", "## Visible navigation", ""])
            lines.extend(f"- `{path}`" for path in guide.navigation_paths)
        if guide.ordered_steps:
            lines.extend(["", "## Steps", ""])
            lines.extend(
                f"{index}. {step}"
                for index, step in enumerate(guide.ordered_steps, start=1)
            )
        if guide.controls:
            lines.extend(["", "## Visible controls", ""])
            lines.extend(
                f"- `{control.name}`: {control.description}"
                for control in guide.controls
            )
        if guide.fields:
            lines.extend(["", "## Visible fields", ""])
            lines.extend(
                f"- `{field.name}` ({field.location}): {field.description}"
                for field in guide.fields
            )
        if guide.warnings:
            lines.extend(["", "## Warnings", ""])
            lines.extend(f"- {warning}" for warning in guide.warnings)
        if guide.uncertainties:
            lines.extend(["", "## Uncertainties", ""])
            lines.extend(f"- {item}" for item in guide.uncertainties)
        return "\n".join(lines).rstrip() + "\n"

    def generate_approved(self, guide: NormalizedGuide, confidence: float) -> str:
        """Render only content already sanitized by the final quality gate."""
        lines = [
            f"# {guide.page_title}", "",
            "> TASLAK: Son otomatik kalite kontrolünden geçmiştir; indekslenmemiştir.", "",
            "## Kaynak", "", f"- Sayfa: {guide.source_url}",
            f"- Güven puanı: {confidence:.2f}",
        ]
        if guide.overview:
            lines.extend(["", "## Genel Bakış", "", guide.overview])
        if guide.navigation_paths:
            lines.extend(["", "## Görünür Menü Yolları", ""])
            lines.extend(f"- `{path}`" for path in guide.navigation_paths)
        if guide.ordered_steps:
            lines.extend(["", "## Adımlar", ""])
            lines.extend(f"{index}. {step}" for index, step in enumerate(guide.ordered_steps, 1))
        if guide.controls:
            lines.extend(["", "## Görünür Kontroller", ""])
            for item in guide.controls:
                if LanguageValidator().english_sentences([item.description]):
                    lines.append(f"- `{item.name}`")
                else:
                    lines.append(f"- `{item.name}`: {item.description}")
        if guide.fields:
            lines.extend(["", "## Görünür Alanlar", ""])
            for item in guide.fields:
                if LanguageValidator().english_sentences([item.description]):
                    lines.append(f"- `{item.name}` ({item.location})")
                else:
                    lines.append(f"- `{item.name}` ({item.location}): {item.description}")
        if guide.warnings:
            lines.extend(["", "## Uyarılar", ""])
            lines.extend(f"- {item}" for item in guide.warnings)
        if guide.uncertainties:
            lines.extend(["", "## Belirsizlikler", ""])
            lines.extend(f"- {item}" for item in guide.uncertainties)
        return "\n".join(lines).rstrip() + "\n"

    def generate_pilot_approved(self, guide: NormalizedGuide, confidence: float) -> str:
        """Render the fixed Sprint 19 promotion-review section contract."""
        language = LanguageValidator()
        lines = [f"# {guide.page_title}", "", "## Kapsam", "", guide.overview or "Kaynak sayfadaki görünür içerik."]
        lines.extend(["", "## Menü yolu", ""])
        lines.extend([*(f"- `{item}`" for item in guide.navigation_paths)] or ["- Görünür menü yolu bulunamadı."])
        lines.extend(["", "## Kullanım adımları", ""])
        lines.extend([*(f"{index}. {item}" for index, item in enumerate(guide.ordered_steps, 1))] or ["- Görünür kullanım adımı bulunamadı."])
        lines.extend(["", "## Alanlar", ""])
        for item in guide.fields:
            description = "" if language.english_sentences([item.description]) else f": {item.description}"
            lines.append(f"- `{item.name}` ({item.location}){description}")
        if not guide.fields:
            lines.append("- Görünür alan bulunamadı.")
        lines.extend(["", "## Görünür kontroller", ""])
        for item in guide.controls:
            description = "" if language.english_sentences([item.description]) else f": {item.description}"
            lines.append(f"- `{item.name}`{description}")
        if not guide.controls:
            lines.append("- Görünür kontrol bulunamadı.")
        lines.extend(["", "## Uyarılar", ""])
        lines.extend([*(f"- {item}" for item in [*guide.warnings, *guide.uncertainties])] or ["- Görünür uyarı bulunamadı."])
        lines.extend(["", "## Kaynak bilgisi", "", f"- Sayfa: {guide.source_url}", f"- Güven puanı: {confidence:.2f}", "- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir."])
        return "\n".join(lines).rstrip() + "\n"
