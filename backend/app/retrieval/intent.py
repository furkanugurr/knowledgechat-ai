"""Deterministic question-intent classification for retrieval."""

from __future__ import annotations

from enum import StrEnum

from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


class QuestionIntent(StrEnum):
    NAVIGATION = "navigation"
    PROCEDURE = "procedure"
    FIRST_ACTION = "first_action"
    FIELD_LISTING = "field_listing"
    FIELD_PURPOSE = "field_purpose"
    CONTROL_PURPOSE = "control_purpose"
    COMPARISON = "comparison"
    CONCEPT_DEFINITION = "concept_definition"
    PRODUCT_OVERVIEW = "product_overview"
    GENERAL_INFORMATION = "general_information"


class IntentClassifier:
    """Classify common Turkish guide questions without an LLM call."""

    @classmethod
    def classify(cls, question: str) -> QuestionIntent:
        phrase = TurkishLexicalNormalizer.phrase(question)
        if cls._contains(phrase, "ilk hangi buton", "once neye bas", "ilk neye bas"):
            return QuestionIntent.FIRST_ACTION
        if cls._contains(
            phrase,
            "hangi menu", "menu alt", "menu yolu", "nasil git", "nasil gider", "nereden ulas", "nerede bul",
        ):
            return QuestionIntent.NAVIGATION
        if cls._contains(
            phrase,
            "hangi alan", "neleri doldur", "alanlari doldur", "alan list",
        ):
            return QuestionIntent.FIELD_LISTING
        if cls._contains(phrase, "arasindaki fark", "farki ne", "karsilastir"):
            return QuestionIntent.COMPARISON
        if cls._contains(phrase, "ne ise yarar", "amaci ne"):
            if cls._contains(phrase, "buton", "dugme", "kontrol"):
                return QuestionIntent.CONTROL_PURPOSE
            if cls._contains(phrase, "hedef adres", "kaynak adres", "alan"):
                return QuestionIntent.FIELD_PURPOSE
        definition_term = cls.definition_term(question)
        if definition_term == "antikor":
            return QuestionIntent.PRODUCT_OVERVIEW
        if definition_term:
            return QuestionIntent.CONCEPT_DEFINITION
        if TurkishLexicalNormalizer.actions(question) & {
            "olustur", "ekle", "yapilandir", "tanimla",
        } and cls._contains(
            phrase, "nasil", "olusturulur", "eklenir", "tanimlanir"
        ) or cls._contains(phrase, "nasil yap"):
            return QuestionIntent.PROCEDURE
        return QuestionIntent.GENERAL_INFORMATION

    @classmethod
    def definition_term(cls, question: str) -> str | None:
        """Return the requested short definition term, when present."""
        phrase = TurkishLexicalNormalizer.phrase(question)
        suffixes = (
            "acilimi nedir", "ne ise yarar", "ne demek", "nedir",
        )
        for suffix in suffixes:
            normalized_suffix = TurkishLexicalNormalizer.phrase(suffix)
            if phrase == normalized_suffix or not phrase.endswith(
                f" {normalized_suffix}"
            ):
                continue
            term = phrase[: -(len(normalized_suffix) + 1)].strip()
            if 1 <= len(term.split()) <= 4:
                return term
        return None

    @staticmethod
    def _contains(value: str, *patterns: str) -> bool:
        return any(
            TurkishLexicalNormalizer.phrase(pattern) in value
            for pattern in patterns
        )
