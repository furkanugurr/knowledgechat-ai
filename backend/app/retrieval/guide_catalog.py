"""Deterministic guide entity resolution from indexed metadata."""
from __future__ import annotations
from dataclasses import dataclass

from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class GuideEntity:
    title: str
    normalized_title: str
    relative_path: str
    category: str
    tokens: frozenset[str]


class GuideEntityCatalog:
    """Resolve exact and near-exact guide titles without hand-written aliases."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        normalizer = TurkishLexicalNormalizer()
        self._normalizer = normalizer
        self._entities = [
            GuideEntity(
                title=item["title"],
                normalized_title=normalizer.phrase(item["title"]),
                relative_path=item["relative_path"],
                category=item["category"],
                tokens=frozenset(normalizer.tokens(item["title"])),
            )
            for item in records
            if item.get("title") and item.get("relative_path")
        ]

    def resolve(self, question: str, limit: int = 1) -> list[GuideEntity]:
        normalized = self._normalizer.phrase(question)
        question_tokens = set(self._normalizer.tokens(question))
        scored: list[tuple[float, GuideEntity]] = []
        for entity in self._entities:
            exact = entity.normalized_title in normalized
            overlap = len(question_tokens & entity.tokens) / max(len(entity.tokens), 1)
            if not exact and (len(entity.tokens) < 2 or overlap < 0.8):
                continue
            specificity = len(entity.tokens) / 100
            scored.append(((10 if exact else 4) + overlap + specificity, entity))
        scored.sort(key=lambda item: (-item[0], -len(item[1].tokens), item[1].relative_path))
        selected: list[GuideEntity] = []
        for _, entity in scored:
            if entity.relative_path not in {item.relative_path for item in selected}:
                selected.append(entity)
            if len(selected) >= limit:
                break
        return selected
