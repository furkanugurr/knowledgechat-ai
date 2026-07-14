"""Turkish language and immutable UI-label checks."""

from __future__ import annotations

import re
from collections.abc import Iterable


class LanguageValidator:
    """Detect English prose while allowing common technical terminology."""

    TRANSLATIONS = {
        "save": "Kaydet",
        "add": "Ekle",
        "cancel": "İptal",
        "status": "Durum",
        "target address": "Hedef Adres",
        "destination address": "Hedef Adres",
        "source address": "Kaynak Adres",
        "username": "Kullanıcı adı",
        "password": "Şifre",
        "login": "Giriş",
        "security settings": "Güvenlik Ayarları",
        "firewall settings": "Güvenlik Duvarı Ayarları",
    }
    ALLOWED_TECHNICAL_TERMS = {
        "ip", "dns", "nat", "firewall", "ipv4", "ipv6", "tcp", "udp",
        "vpn", "http", "https", "ssl", "ssh", "vrf", "lan", "wan",
    }
    _ENGLISH_WORDS = {
        "the", "this", "that", "with", "from", "select", "enter", "click",
        "button", "field", "allows", "used", "currently", "configuration",
        "screen", "settings", "default", "should", "visible", "option",
        "and", "then", "open", "press", "create", "new", "page", "source",
        "overview", "steps", "warnings", "uncertainties", "navigation",
        "cancel", "cancels", "save", "saves", "current", "operation", "entry",
    }
    _TOKEN = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9]+")

    def english_sentences(self, values: Iterable[str]) -> list[str]:
        """Return prose fragments that contain strong English signals."""
        findings: list[str] = []
        for value in values:
            tokens = {item.casefold() for item in self._TOKEN.findall(value)}
            tokens -= self.ALLOWED_TECHNICAL_TERMS
            if len(tokens & self._ENGLISH_WORDS) >= 2:
                findings.append(value)
        return list(dict.fromkeys(findings))

    def translated_ui_labels(
        self,
        values: Iterable[str],
        source_labels: Iterable[str],
    ) -> list[str]:
        """Find English replacements when the Turkish source label is known."""
        source = {label.strip().casefold() for label in source_labels}
        findings: list[str] = []
        for value in values:
            folded = value.strip().casefold()
            for english, turkish in self.TRANSLATIONS.items():
                if english in folded and turkish.casefold() in source:
                    findings.append(f"{value} -> kaynak etiketi: {turkish}")
        return list(dict.fromkeys(findings))
