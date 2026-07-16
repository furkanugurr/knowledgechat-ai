"""Post-Gemma evidence gate for review-only Markdown drafts."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from tools.visual_guide_extractor.quality.language_validation import LanguageValidator
from tools.visual_guide_extractor.schemas.extraction import GuidePage, NormalizedGuide, VisionExtraction


class FinalValidationResult(BaseModel):
    """Auditable result of the final guide quality gate."""

    confidence_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str]
    approved: bool
    rejected_sentences: list[str]
    removed_unsupported_claims: list[str]
    sanitized_guide: NormalizedGuide

    model_config = ConfigDict(extra="forbid")


class FinalQualityValidator:
    """Remove content that cannot be traced to HTML or Qwen observations."""

    _ACTION = re.compile(
        r"\b(tıklayın|basın|seçin|girin|yazın|ekleyin|silin|açın|kapatın|"
        r"kaydedin|işaretleyin|oluşturun|güncelleyin)\b",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.language = LanguageValidator()

    def validate(
        self,
        page: GuidePage,
        vision_results: list[VisionExtraction],
        normalized: NormalizedGuide,
    ) -> FinalValidationResult:
        controls = self._unique(item.name for result in vision_results for item in result.controls)
        fields = self._unique(item.name for result in vision_results for item in result.fields)
        all_labels = controls | fields
        evidence = self._evidence(page, vision_results)
        evidence_folded = evidence.casefold()
        rejected: list[str] = []
        removed: list[str] = []
        warnings: list[str] = []

        safe_controls = [item for item in normalized.controls if item.name.casefold() in controls]
        safe_fields = [item for item in normalized.fields if item.name.casefold() in fields]
        for item in normalized.controls:
            if item.name.casefold() not in controls:
                removed.append(f"Bilinmeyen kontrol: {item.name}")
        for item in normalized.fields:
            if item.name.casefold() not in fields:
                removed.append(f"Bilinmeyen alan: {item.name}")

        translations = self.language.translated_ui_labels(
            [item.name for item in (*normalized.controls, *normalized.fields)], all_labels
        )
        warnings.extend(f"Çevrilmiş UI etiketi: {item}" for item in translations)

        safe_paths: list[str] = []
        qwen_paths = {
            result.visible_navigation_path.strip().casefold()
            for result in vision_results
            if result.visible_navigation_path.strip()
        }
        for path in normalized.navigation_paths:
            if path.casefold() in qwen_paths or path.casefold() in page.html_context().casefold():
                safe_paths.append(path)
            else:
                removed.append(f"Desteklenmeyen menü yolu: {path}")

        safe_steps: list[str] = []
        qwen_steps = "\n".join(step for result in vision_results for step in result.ordered_steps).casefold()
        for step in normalized.ordered_steps:
            referenced = {label for label in all_labels if label in step.casefold()}
            action = bool(self._ACTION.search(step))
            supported_text = self._coverage(step, evidence) >= 0.45 or step.casefold() in qwen_steps
            if action and not referenced:
                rejected.append(step)
                removed.append(f"Kontrol/alan kanıtı olmayan eylem: {step}")
            elif not supported_text:
                rejected.append(step)
                removed.append(f"Kanıtla desteklenmeyen adım: {step}")
            else:
                safe_steps.append(step)

        prose = [normalized.overview, *safe_steps, *normalized.warnings,
                 *(item.description for item in safe_controls),
                 *(item.description for item in safe_fields)]
        english = self.language.english_sentences(prose)
        warnings.extend(f"İngilizce içerik: {item}" for item in english)

        overview = normalized.overview
        if overview in english or (overview and self._coverage(overview, evidence) < 0.45):
            if overview:
                removed.append(f"Desteklenmeyen genel bakış: {overview}")
            overview = ""

        safe_warnings = [item for item in normalized.warnings if item not in english and self._coverage(item, evidence) >= 0.45]
        for item in normalized.warnings:
            if item not in safe_warnings:
                removed.append(f"Desteklenmeyen uyarı: {item}")

        sanitized = normalized.model_copy(update={
            "overview": overview,
            "navigation_paths": safe_paths,
            "controls": safe_controls,
            "fields": safe_fields,
            "ordered_steps": [item for item in safe_steps if item not in english],
            "warnings": safe_warnings,
        })
        final_prose = [sanitized.overview, *sanitized.ordered_steps, *sanitized.warnings]
        final_english = self.language.english_sentences(final_prose)
        final_translations = self.language.translated_ui_labels(
            [item.name for item in (*sanitized.controls, *sanitized.fields)], all_labels
        )
        penalty = min(0.75, len(removed) * 0.06 + len(warnings) * 0.08)
        score = round(max(0.0, 1.0 - penalty), 2)
        critical = bool(final_english or final_translations)
        approved = not critical and score >= 0.80
        if not sanitized.ordered_steps and normalized.ordered_steps:
            approved = False
            warnings.append("Üretilen adımların hiçbiri son kalite kapısını geçemedi.")
        return FinalValidationResult(
            confidence_score=score,
            warnings=list(dict.fromkeys(warnings)),
            approved=approved,
            rejected_sentences=list(dict.fromkeys(rejected)),
            removed_unsupported_claims=list(dict.fromkeys(removed)),
            sanitized_guide=sanitized,
        )

    @staticmethod
    def _unique(values) -> set[str]:
        return {value.strip().casefold() for value in values if value.strip()}

    @staticmethod
    def _tokens(value: str) -> set[str]:
        stop = {"ve", "veya", "ile", "için", "bir", "bu", "şu", "olarak", "olan"}
        return {token.casefold() for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9]+", value) if len(token) > 2 and token.casefold() not in stop}

    def _coverage(self, claim: str, evidence: str) -> float:
        tokens = self._tokens(claim)
        return 1.0 if len(tokens) < 3 else len(tokens & self._tokens(evidence)) / len(tokens)

    @staticmethod
    def _evidence(page: GuidePage, results: list[VisionExtraction]) -> str:
        parts = [page.html_context()]
        for result in results:
            parts.extend([result.screen_name, result.purpose, result.visible_navigation_path,
                          *result.ordered_steps, *result.warnings, *result.uncertainties])
            for item in (*result.controls, *result.fields):
                parts.extend([item.name, item.description])
        return "\n".join(parts)
