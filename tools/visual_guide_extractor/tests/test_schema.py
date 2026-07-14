"""Tests for strict vision result validation."""

import unittest

from pydantic import ValidationError

from tools.visual_guide_extractor.schemas.extraction import VisionExtraction


class VisionExtractionTests(unittest.TestCase):
    def test_accepts_structured_observations(self) -> None:
        result = VisionExtraction(
            page_title="Güvenlik Kuralları",
            image_index=0,
            screen_name="Yeni Kayıt",
            purpose="Yeni kural alanlarını gösterir.",
            visible_navigation_path="Güvenlik Ayarları > Güvenlik Kuralları",
            controls=[
                {
                    "kind": "button",
                    "name": "Ekle",
                    "description": "Yeni kayıt açar.",
                }
            ],
            fields=[
                {
                    "kind": "selection",
                    "name": "Durum",
                    "description": "Aktiflik seçimi.",
                    "location": "Formun üst kısmı",
                }
            ],
            ordered_steps=["Ekle düğmesine basın."],
            warnings=[],
            uncertainties=["Alt alanın etiketi okunamıyor."],
        )
        self.assertEqual(result.image_index, 0)

    def test_rejects_control_field_overlap(self) -> None:
        with self.assertRaises(ValidationError):
            VisionExtraction(
                page_title="Example",
                image_index=0,
                screen_name="Form",
                purpose="Test",
                visible_navigation_path="",
                controls=[
                    {"kind": "button", "name": "Durum", "description": "Açar."}
                ],
                fields=[
                    {
                        "kind": "selection",
                        "name": "Durum",
                        "description": "Değer seçilir.",
                        "location": "Form",
                    }
                ],
                ordered_steps=[],
                warnings=[],
                uncertainties=[],
            )

    def test_rejects_unsupported_control_kind(self) -> None:
        with self.assertRaises(ValidationError):
            VisionExtraction(
                page_title="Example",
                image_index=0,
                screen_name="Form",
                purpose="Test",
                visible_navigation_path="",
                controls=[
                    {"kind": "text", "name": "Açıklama", "description": "Metin."}
                ],
                fields=[],
                ordered_steps=[],
                warnings=[],
                uncertainties=[],
            )

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            VisionExtraction.model_validate(
                {
                    "page_title": "Example",
                    "image_index": 0,
                    "screen_name": "Screen",
                    "purpose": "Purpose",
                    "visible_navigation_path": "",
                    "controls": [],
                    "fields": [],
                    "ordered_steps": [],
                    "warnings": [],
                    "uncertainties": [],
                    "invented": True,
                }
            )


if __name__ == "__main__":
    unittest.main()
