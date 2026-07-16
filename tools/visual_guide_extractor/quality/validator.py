"""Evidence-based checks for Qwen and Gemma outputs."""

from __future__ import annotations

import re
from collections.abc import Iterable

from tools.visual_guide_extractor.schemas.extraction import (
    GuidePage,
    NormalizedGuide,
    VisionExtraction,
)


class QualityValidator:
    """Detect translations, unknown controls, and weakly supported claims."""

    _TRANSLATED_LABELS = {
        "save": "Kaydet",
        "cancel": "İptal",
        "username": "Kullanıcı adı",
        "password": "Şifre",
        "login": "Giriş",
        "security settings": "Güvenlik Ayarları",
        "firewall settings": "Güvenlik Duvarı Ayarları",
        "security rules": "Güvenlik Kuralları",
        "nat configuration": "NAT Yapılandırması",
        "default rule": "Varsayılan Kural",
        "logging": "Loglama",
        "source address": "Kaynak Adres",
        "destination address": "Hedef Adres",
        "services": "Servisler",
        "description": "Açıklama",
        "status": "Durum",
        "action": "İşlem",
    }
    _STOPWORDS = {
        "ve", "veya", "ile", "için", "bir", "bu", "şu", "the", "and",
        "or", "to", "of", "in", "on", "is", "are", "olarak", "olan",
        "kullanılan", "kullanılır", "alan", "seçenek", "ekran", "ilgili",
    }
    _QUOTED_LABEL = re.compile(r"[`'\"]([^`'\"]{2,80})[`'\"]")
    _TOKEN = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+")
    _ENGLISH_PROSE = {
        "the", "this", "that", "with", "from", "select", "enter", "click",
        "button", "field", "allows", "used", "currently", "configuration",
        "screen", "settings", "default", "should", "visible", "option",
    }

    def evaluate_vision_results(
        self,
        results: Iterable[VisionExtraction],
    ) -> dict[str, int]:
        """Return aggregate language and structural metrics for Qwen output."""
        english_fragments = 0
        overlaps = 0
        empty_locations = 0
        steps = 0
        uncertainties = 0
        for result in results:
            fragments = [
                result.purpose,
                result.visible_navigation_path,
                *result.ordered_steps,
                *result.warnings,
                *result.uncertainties,
                *(item.description for item in result.controls),
                *(item.description for item in result.fields),
            ]
            english_fragments += sum(self._looks_english(item) for item in fragments)
            overlaps += len(
                {item.name.casefold() for item in result.controls}
                & {item.name.casefold() for item in result.fields}
            )
            empty_locations += sum(not item.location.strip() for item in result.fields)
            steps += len(result.ordered_steps)
            uncertainties += len(result.uncertainties)
        return {
            "english_prose_fragments": english_fragments,
            "control_field_overlap": overlaps,
            "empty_field_locations": empty_locations,
            "ordered_steps": steps,
            "uncertainties": uncertainties,
        }

    def evaluate(
        self,
        page: GuidePage,
        vision_results: list[VisionExtraction],
        normalized: NormalizedGuide,
    ) -> dict[str, object]:
        """Return deterministic quality findings for one normalized page."""
        evidence = self._evidence_text(page, vision_results)
        known_labels = self._known_labels(vision_results)
        normalized_labels = [
            item.name for item in (*normalized.controls, *normalized.fields)
        ]
        english_translations = self._translated_labels(
            normalized_labels + normalized.navigation_paths,
            evidence,
        )
        unknown_controls = self._unknown_step_controls(
            normalized.ordered_steps,
            known_labels,
            evidence,
        )
        claims = [
            normalized.overview,
            *normalized.ordered_steps,
            *normalized.warnings,
            *(item.description for item in normalized.controls),
            *(item.description for item in normalized.fields),
        ]
        unsupported = [
            claim
            for claim in claims
            if claim.strip() and not self._claim_supported(claim, evidence)
        ]
        return {
            "english_ui_label_translations": english_translations,
            "steps_referencing_unknown_controls": unknown_controls,
            "weakly_supported_claims": unsupported,
            "control_field_overlap": sorted(
                {item.name.casefold() for item in normalized.controls}
                & {item.name.casefold() for item in normalized.fields}
            ),
        }

    def _translated_labels(self, values: Iterable[str], evidence: str) -> list[str]:
        findings: list[str] = []
        evidence_folded = evidence.casefold()
        for value in values:
            folded = value.casefold()
            for english, turkish in self._TRANSLATED_LABELS.items():
                if english in folded and turkish.casefold() in evidence_folded:
                    findings.append(f"{value} -> expected visible label: {turkish}")
        return sorted(set(findings))

    def _unknown_step_controls(
        self,
        steps: Iterable[str],
        known_labels: set[str],
        evidence: str,
    ) -> list[str]:
        findings: list[str] = []
        evidence_folded = evidence.casefold()
        for step in steps:
            for candidate in self._QUOTED_LABEL.findall(step):
                key = candidate.strip().casefold()
                if key not in known_labels and key not in evidence_folded:
                    findings.append(f"{candidate}: {step}")
        return sorted(set(findings))

    def _claim_supported(self, claim: str, evidence: str) -> bool:
        claim_tokens = self._tokens(claim)
        if len(claim_tokens) < 3:
            return True
        evidence_tokens = self._tokens(evidence)
        coverage = len(claim_tokens & evidence_tokens) / len(claim_tokens)
        return coverage >= 0.45

    def _tokens(self, value: str) -> set[str]:
        return {
            token.casefold()
            for token in self._TOKEN.findall(value)
            if len(token) > 2 and token.casefold() not in self._STOPWORDS
        }

    def _looks_english(self, value: str) -> bool:
        tokens = {token.casefold() for token in self._TOKEN.findall(value)}
        return len(tokens & self._ENGLISH_PROSE) >= 2

    @staticmethod
    def _known_labels(results: Iterable[VisionExtraction]) -> set[str]:
        return {
            item.name.strip().casefold()
            for result in results
            for item in (*result.controls, *result.fields)
        }

    @staticmethod
    def _evidence_text(
        page: GuidePage,
        results: Iterable[VisionExtraction],
    ) -> str:
        parts = [page.html_context()]
        for result in results:
            parts.extend(
                [
                    result.screen_name,
                    result.purpose,
                    result.visible_navigation_path,
                    *result.ordered_steps,
                    *result.warnings,
                    *result.uncertainties,
                ]
            )
            for item in (*result.controls, *result.fields):
                parts.extend([item.name, item.description])
        return "\n".join(parts)
