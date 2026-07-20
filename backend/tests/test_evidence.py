"""Tests for central extraction-placeholder rejection."""

from app.knowledge.evidence import (
    has_usable_evidence,
    is_placeholder_line,
    usable_evidence_text,
)


def test_detects_supported_extraction_placeholders() -> None:
    assert is_placeholder_line("- Görünür kullanım adımı bulunamadı.")
    assert is_placeholder_line("- Görünür alan bulunamadı.")
    assert is_placeholder_line("- Görünür kontrol bulunamadı.")
    assert is_placeholder_line("- Görünür menü yolu bulunamadı.")


def test_placeholder_only_section_is_not_usable_evidence() -> None:
    assert not has_usable_evidence("## Alanlar\n\n- Görünür alan bulunamadı.")


def test_mixed_section_retains_real_evidence_only() -> None:
    text = "## Alanlar\n\n- Görünür alan bulunamadı.\n- `Hedef Adres`: hedef IP"
    assert has_usable_evidence(text)
    assert usable_evidence_text(text) == "- `Hedef Adres`: hedef IP"
