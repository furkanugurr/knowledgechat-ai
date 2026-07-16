"""Lightweight Turkish-aware lexical normalization for retrieval reranking."""

from __future__ import annotations

import re

_TURKISH_ASCII = str.maketrans(
    {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"}
)
_TOKEN = re.compile(r"[a-z0-9]+")
_SAFE_SUFFIXES = (
    "larindan", "lerinden", "larina", "lerine", "lari", "leri",
    "lardan", "lerden", "lar", "ler", "nin", "nun", "nün", "in",
    "un", "den", "dan", "ine", "ina", "de", "da", "yi", "ni", "nu", "i", "u",
)


class TurkishLexicalNormalizer:
    """Normalize Turkish UI/search text without external NLP dependencies."""

    ENTITY_PHRASES = (
        "Güvenlik Kuralları",
        "Hedef Adres",
        "Kaynak Adres",
        "Dinamik NAT",
        "IPSec VPN",
        "SSL VPN",
        "Site to Site VPN",
        "Yönetim Paneli Kullanıcıları",
        "NAT",
    )
    ACTION_ROOTS = (
        "olustur", "ekle", "kaydet", "yapilandir", "tanimla", "sec", "gir",
    )
    ACTION_VARIANTS = {"kaydet": ("kaydet", "kayded")}

    @classmethod
    def canonical(cls, value: str) -> str:
        """Return lowercase, punctuation-free, Turkish-safe text."""
        lowered = value.casefold().translate(_TURKISH_ASCII)
        return " ".join(_TOKEN.findall(lowered))

    @classmethod
    def token(cls, value: str) -> str:
        """Apply conservative suffix removal to one canonical token."""
        canonical = cls.canonical(value)
        if not canonical or " " in canonical:
            return canonical
        protected = {
            "butonu": "buton",
            "butonun": "buton",
            "kullanici": "kullanici",
        }
        if canonical in protected:
            return protected[canonical]
        for suffix in _SAFE_SUFFIXES:
            if len(canonical) - len(suffix) >= 4 and canonical.endswith(suffix):
                return canonical[: -len(suffix)]
        return canonical

    @classmethod
    def tokens(cls, value: str) -> tuple[str, ...]:
        """Return stable normalized tokens while preserving source order."""
        return tuple(cls.token(item) for item in cls.canonical(value).split())

    @classmethod
    def phrase(cls, value: str) -> str:
        """Return a normalized multi-word phrase."""
        return " ".join(cls.tokens(value))

    @classmethod
    def entities(cls, value: str) -> set[str]:
        """Return known multi-word entities explicitly present in text."""
        phrase = cls.phrase(value)
        tokens = set(phrase.split())
        return {
            normalized
            for entity in cls.ENTITY_PHRASES
            if (
                (normalized := cls.phrase(entity)) in phrase
                or set(normalized.split()).issubset(tokens)
            )
        }

    @classmethod
    def actions(cls, value: str) -> set[str]:
        """Return supported procedural action roots present in text."""
        tokens = cls.tokens(value)
        return {
            root
            for root in cls.ACTION_ROOTS
            if any(
                token.startswith(variant)
                for token in tokens
                for variant in cls.ACTION_VARIANTS.get(root, (root,))
            )
        }
