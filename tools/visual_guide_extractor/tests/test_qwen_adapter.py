"""Tests for strict Qwen JSON response handling."""

import json
import unittest

from tools.visual_guide_extractor.vision.qwen_adapter import QwenVisionAdapter


def valid_payload() -> dict[str, object]:
    return {
        "page_title": "ignored",
        "image_index": 99,
        "screen_name": "Güvenlik Kuralları",
        "purpose": "Kuralları listeler.",
        "visible_navigation_path": "",
        "controls": [
            {"kind": "button", "name": "Ekle", "description": "Yeni kayıt açar."}
        ],
        "fields": [],
        "ordered_steps": [],
        "warnings": [],
        "uncertainties": [],
    }


class QwenAdapterParsingTests(unittest.TestCase):
    def test_parses_valid_qwen_json(self) -> None:
        result = QwenVisionAdapter.parse_content(
            json.dumps(valid_payload(), ensure_ascii=False),
            "Authoritative title",
            2,
        )
        self.assertEqual(result.page_title, "Authoritative title")
        self.assertEqual(result.image_index, 2)
        self.assertEqual(result.controls[0].name, "Ekle")

    def test_rejects_invalid_json(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            QwenVisionAdapter.parse_content("not-json", "Page", 0)

    def test_rejects_missing_fields(self) -> None:
        payload = valid_payload()
        del payload["fields"]
        with self.assertRaisesRegex(ValueError, "does not match"):
            QwenVisionAdapter.parse_content(json.dumps(payload), "Page", 0)

    def test_prefers_field_when_model_duplicates_a_label(self) -> None:
        payload = valid_payload()
        payload["controls"].append(
            {"kind": "dropdown", "name": "Durum", "description": "Seçim."}
        )
        payload["fields"] = [
            {
                "kind": "selection",
                "name": "Durum",
                "description": "Yapılandırma değeri.",
                "location": "Form",
            }
        ]

        result = QwenVisionAdapter.parse_content(json.dumps(payload), "Page", 0)

        self.assertNotIn("Durum", [item.name for item in result.controls])
        self.assertEqual(result.fields[0].name, "Durum")
        self.assertTrue(result.uncertainties)

    def test_removes_empty_steps_and_duplicate_controls(self) -> None:
        payload = valid_payload()
        payload["ordered_steps"] = ["", "Ekle düğmesine tıklayın.", "Ekle düğmesine tıklayın."]
        payload["controls"].append(payload["controls"][0].copy())
        result = QwenVisionAdapter.parse_content(json.dumps(payload), "Page", 0)
        self.assertEqual(["Ekle düğmesine tıklayın."], result.ordered_steps)
        self.assertEqual(1, len(result.controls))


if __name__ == "__main__":
    unittest.main()
