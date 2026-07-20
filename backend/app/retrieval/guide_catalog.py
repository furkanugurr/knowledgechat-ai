"""Deterministic guide entity resolution from indexed metadata."""
from __future__ import annotations
from dataclasses import dataclass

from app.retrieval.turkish_lexical import TurkishLexicalNormalizer
from app.retrieval.intent import QuestionIntent


@dataclass(frozen=True, slots=True)
class GuideEntity:
    title: str
    normalized_title: str
    relative_path: str
    category: str
    tokens: frozenset[str]
    category_tokens: frozenset[str]
    available_sections: frozenset[str]
    source_url: str


class GuideEntityCatalog:
    """Resolve exact and near-exact guide titles without hand-written aliases."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        normalizer = TurkishLexicalNormalizer()
        self._normalizer = normalizer
        self._entities = [
            GuideEntity(
                title=self._canonical_title(item["title"]),
                normalized_title=normalizer.phrase(self._canonical_title(item["title"])),
                relative_path=item["relative_path"],
                category=item["category"],
                tokens=frozenset(normalizer.tokens(item["title"])),
                category_tokens=frozenset(
                    set(normalizer.tokens(item.get("category", "")))
                    - set(normalizer.tokens(self._canonical_title(item["title"])))
                    - {"yonetim", "ayar", "islem", "yapilandirma"}
                ),
                available_sections=frozenset(
                    normalizer.phrase(section)
                    for section in item.get("available_sections", "").split("|")
                    if section
                ),
                source_url=item.get("source_url", ""),
            )
            for item in records
            if item.get("title") and item.get("relative_path")
        ]

    @staticmethod
    def _canonical_title(value: str) -> str:
        """Remove a crawler-added site suffix without changing UI wording."""
        return value.split(" - ePati", 1)[0].strip()

    def resolve(
        self, question: str, limit: int = 1,
        intent: QuestionIntent = QuestionIntent.GENERAL_INFORMATION,
    ) -> list[GuideEntity]:
        normalized = self._normalizer.phrase(question)
        question_tokens = set(self._normalizer.tokens(question))
        scored: list[tuple[float, GuideEntity]] = []
        for entity in self._entities:
            exact = entity.normalized_title in normalized
            overlap = len(question_tokens & entity.tokens) / max(len(entity.tokens), 1)
            if not exact and (len(entity.tokens) < 2 or overlap < 0.8):
                continue
            category_overlap = len(question_tokens & entity.category_tokens)
            expected_section = {
                QuestionIntent.NAVIGATION: "menü yolu",
                QuestionIntent.PROCEDURE: "kullanım adımları",
                QuestionIntent.FIRST_ACTION: "görünür kontroller",
                QuestionIntent.FIELD_LISTING: "alanlar",
                QuestionIntent.FIELD_PURPOSE: "alanlar",
                QuestionIntent.CONTROL_PURPOSE: "görünür kontroller",
            }.get(intent)
            section_support = 0.25 if expected_section in entity.available_sections else 0.0
            specificity = len(entity.tokens) / 100
            scored.append(((10 if exact else 4) + overlap + specificity
                           + (2.0 * category_overlap) + section_support, entity))
        scored.sort(key=lambda item: (-item[0], -len(item[1].tokens), item[1].relative_path))
        if scored:
            top_score = scored[0][0]
            tied = [entity for score, entity in scored if score == top_score]
            if len(tied) > 1 and len({entity.normalized_title for entity in tied}) == 1:
                return []
        selected: list[GuideEntity] = []
        for _, entity in scored:
            if entity.relative_path not in {item.relative_path for item in selected}:
                selected.append(entity)
            if len(selected) >= limit:
                break
        return selected
