"""Corpus-derived technical concept and acronym resolution."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.intent import IntentClassifier
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class ConceptMatch:
    """One exact concept alias backed by indexed source paths."""

    term: str
    display_term: str
    relative_paths: tuple[str, ...]
    acronym: bool


class ConceptCatalog:
    """Resolve only aliases that were discovered in indexed evidence."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        self._normalizer = TurkishLexicalNormalizer()
        self._entries = {
            record["alias"]: ConceptMatch(
                term=record["alias"],
                display_term=record.get("display_term", record["alias"]),
                relative_paths=tuple(filter(None, record.get("relative_paths", "").split("|"))),
                acronym=record.get("acronym") == "true",
            )
            for record in records
            if record.get("alias") and record.get("relative_paths")
        }

    def resolve(self, question: str) -> ConceptMatch | None:
        """Return an exact corpus alias for one definition question."""
        term = IntentClassifier.definition_term(question)
        if not term:
            return None
        return self._entries.get(self._normalizer.phrase(term))

    @property
    def aliases(self) -> frozenset[str]:
        """Return discovered normalized aliases for diagnostics/tests."""
        return frozenset(self._entries)
