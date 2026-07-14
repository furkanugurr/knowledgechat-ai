"""Tests for evidence-based extraction quality checks."""

import unittest

from tools.visual_guide_extractor.quality import QualityValidator
from tools.visual_guide_extractor.schemas.extraction import (
    ContentBlock,
    GuidePage,
    NormalizedGuide,
    VisionExtraction,
)


class QualityValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = GuidePage(
            page_title="Dinamik NAT",
            source_url="https://example.test/nat",
            blocks=[
                ContentBlock(kind="paragraph", text="Kaydet düğmesine basınız.")
            ],
        )
        self.vision = VisionExtraction(
            page_title="Dinamik NAT",
            image_index=0,
            screen_name="Yeni Kayıt",
            purpose="Kayıt formunu gösterir.",
            visible_navigation_path="",
            controls=[
                {
                    "kind": "button",
                    "name": "Kaydet",
                    "description": "Formu kaydeden düğme.",
                }
            ],
            fields=[],
            ordered_steps=["Kaydet düğmesine basınız."],
            warnings=[],
            uncertainties=[],
        )

    def test_detects_translated_ui_label(self) -> None:
        normalized = NormalizedGuide(
            page_title="Dinamik NAT",
            source_url="https://example.test/nat",
            overview="Kayıt formu.",
            navigation_paths=[],
            controls=[
                {
                    "kind": "button",
                    "name": "Save Button",
                    "description": "Formu kaydeder.",
                }
            ],
            fields=[],
            ordered_steps=[],
            warnings=[],
            uncertainties=[],
        )
        report = QualityValidator().evaluate(self.page, [self.vision], normalized)
        self.assertTrue(report["english_ui_label_translations"])

    def test_detects_step_with_unknown_quoted_control(self) -> None:
        normalized = NormalizedGuide(
            page_title="Dinamik NAT",
            source_url="https://example.test/nat",
            overview="Kayıt formu.",
            navigation_paths=[],
            controls=self.vision.controls,
            fields=[],
            ordered_steps=["`Uygula` düğmesine basınız."],
            warnings=[],
            uncertainties=[],
        )
        report = QualityValidator().evaluate(self.page, [self.vision], normalized)
        self.assertTrue(report["steps_referencing_unknown_controls"])

    def test_detects_claim_not_supported_by_evidence(self) -> None:
        normalized = NormalizedGuide(
            page_title="Dinamik NAT",
            source_url="https://example.test/nat",
            overview="Bulut lisansı otomatik olarak uzaktan yenilenir.",
            navigation_paths=[],
            controls=self.vision.controls,
            fields=[],
            ordered_steps=[],
            warnings=[],
            uncertainties=[],
        )
        report = QualityValidator().evaluate(self.page, [self.vision], normalized)
        self.assertIn(
            "Bulut lisansı otomatik olarak uzaktan yenilenir.",
            report["weakly_supported_claims"],
        )


if __name__ == "__main__":
    unittest.main()
