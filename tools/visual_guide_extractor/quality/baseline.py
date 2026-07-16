"""Recorded Sprint 15 quality baseline for before/after comparison."""

SPRINT_15_BASELINE: dict[str, object] = {
    "images": 15,
    "english_prose_fragments": 59,
    "control_field_overlap": 26,
    "empty_field_locations": 12,
    "normalized_english_ui_labels": 12,
    "ordered_steps": 69,
    "uncertainties": 18,
    "issues": [
        "Qwen sometimes wrote English descriptions for Turkish screens.",
        "The same label appeared in both controls and fields.",
        "Some fields had no visible location.",
        "Qwen inferred steps from visible controls instead of explicit evidence.",
        "Gemma translated Turkish UI labels into English.",
        "Gemma added or strengthened claims beyond the supplied evidence.",
    ],
}
