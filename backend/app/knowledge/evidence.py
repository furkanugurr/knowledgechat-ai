"""Shared rules for rejecting extraction placeholders as knowledge evidence."""

from __future__ import annotations

import re


_PLACEHOLDER = re.compile(
    r"^(?:görünür\s+)?(?:kullanım\s+adımı|adım|alan|kontrol|menü\s+yolu|uyarı)\s+"
    r"(?:bulunamadı|mevcut\s+değil|yer\s+almıyor)\.?$",
    re.IGNORECASE,
)


def is_placeholder_line(value: str) -> bool:
    """Return whether one Markdown line is an extraction absence marker."""
    cleaned = value.strip().lstrip("-*").strip().strip("`").strip()
    return bool(_PLACEHOLDER.fullmatch(cleaned))


def usable_evidence_text(value: str) -> str:
    """Remove headings and placeholder lines, retaining actual evidence."""
    lines = [
        line for line in value.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        and not is_placeholder_line(line)
    ]
    return "\n".join(lines).strip()


def has_usable_evidence(value: str) -> bool:
    """Return whether a chunk contains evidence beyond absence markers."""
    return bool(usable_evidence_text(value))
