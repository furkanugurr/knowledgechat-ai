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
            "hangi menu", "menu alt", "nasil git", "nasil gider", "nereden ulas", "nerede bul",
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
            return QuestionIntent.FIELD_PURPOSE
        if TurkishLexicalNormalizer.actions(question) & {
            "olustur", "ekle", "yapilandir", "tanimla",
        } or cls._contains(phrase, "nasil yap"):
            return QuestionIntent.PROCEDURE
        return QuestionIntent.GENERAL_INFORMATION

    @staticmethod
    def _contains(value: str, *patterns: str) -> bool:
        return any(
            TurkishLexicalNormalizer.phrase(pattern) in value
            for pattern in patterns
        )
