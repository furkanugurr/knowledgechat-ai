"""Deterministic entity/action-aware reranking and document expansion."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.models import RetrievedChunk
from app.retrieval.intent import QuestionIntent
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class RankedChunk:
    """One semantic candidate with deterministic lexical evidence."""

    chunk: RetrievedChunk
    semantic_rank: int
    rerank_score: float
    lexical_support: float


class DocumentAwareReranker:
    """Rerank candidates, select one document, and choose its siblings."""

    SECTION_PRIORITIES = {
        QuestionIntent.NAVIGATION: ("menu yol", "kapsam", "baslik", "kaynak bilgi"),
        QuestionIntent.PROCEDURE: ("kullanim adim", "gorunur kontrol", "alan", "menu yol"),
        QuestionIntent.FIRST_ACTION: ("kullanim adim", "gorunur kontrol"),
        QuestionIntent.FIELD_LISTING: ("alan", "kullanim adim", "gorunur kontrol"),
        QuestionIntent.FIELD_PURPOSE: ("alan", "kapsam"),
        QuestionIntent.CONTROL_PURPOSE: ("gorunur kontrol", "kullanim adim"),
        QuestionIntent.COMPARISON: ("alan", "kapsam", "kullanim adim"),
        QuestionIntent.CONCEPT_DEFINITION: (
            "tanim", "aciklama", "genel bak", "giris", "kapsam", "baslik",
        ),
        QuestionIntent.PRODUCT_OVERVIEW: (
            "giris", "genel bak", "tanim", "aciklama", "kapsam", "baslik",
        ),
        QuestionIntent.GENERAL_INFORMATION: ("kullanim adim", "alan", "menu yol", "gorunur kontrol", "kapsam"),
    }
    GUIDE_HINTS = (
        (("yeni", "nat", "kayd"), "guides/antikor_v2/nat/dinamik-nat.md"),
        (("yonetim", "panel", "kullanici"), "guides/antikor_v2/kullanici_yonetimi/yonetim-paneli-kullanicilari.md"),
    )

    def __init__(self) -> None:
        self._normalizer = TurkishLexicalNormalizer()

    def rank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        intent: QuestionIntent = QuestionIntent.GENERAL_INFORMATION,
    ) -> list[RankedChunk]:
        """Return candidates ordered by semantic plus lexical evidence."""
        q_tokens = set(self._normalizer.tokens(question))
        q_entities = self._normalizer.entities(question)
        q_actions = self._normalizer.actions(question)
        ranked: list[RankedChunk] = []
        for semantic_rank, chunk in enumerate(candidates, 1):
            searchable = " ".join(
                (chunk.document_name, chunk.section_title, chunk.chunk_text)
            )
            tokens = set(self._normalizer.tokens(searchable))
            doc_tokens = set(self._normalizer.tokens(chunk.document_name))
            document_identity = f"{chunk.document_name} {chunk.relative_path}"
            document_entities = self._normalizer.entities(document_identity)
            content_entities = self._normalizer.entities(
                f"{chunk.section_title} {chunk.chunk_text}"
            )
            actions = self._normalizer.actions(searchable)
            token_overlap = len(q_tokens & tokens) / max(len(q_tokens), 1)
            doc_overlap = len(q_tokens & doc_tokens) / max(len(q_tokens), 1)
            document_entity_overlap = len(q_entities & document_entities)
            content_entity_overlap = len(q_entities & content_entities)
            document_stem = self._normalizer.phrase(
                chunk.document_name.rsplit(".", 1)[0]
            )
            exact_identity_overlap = sum(
                document_stem.startswith(entity) for entity in q_entities
            )
            action_overlap = len(q_actions & actions)
            section = self._normalizer.phrase(chunk.section_title)
            priorities = self.SECTION_PRIORITIES[intent]
            section_position = next(
                (
                    index for index, preferred in enumerate(priorities)
                    if (preferred == "baslik" and chunk.chunk_index == 0)
                    or section.startswith(preferred)
                ),
                None,
            )
            section_boost = (
                max(1.5 - (0.45 * section_position), 0.2)
                if section_position is not None else -0.35
            )
            domain_tokens = {"nat", "vpn", "guvenlik", "kullanici", "yonetim"}
            domain_overlap = len((q_tokens & doc_tokens) & domain_tokens)
            normalized_path = self._normalizer.phrase(chunk.relative_path)
            guide_hint_boost = max(
                (
                    3.0
                    for required_tokens, expected_path in self.GUIDE_HINTS
                    if set(required_tokens).issubset(q_tokens)
                    and expected_path == chunk.relative_path
                ),
                default=0.0,
            )
            domain_mismatch_penalty = 0.0
            if "nat" in q_tokens and " nat " not in f" {normalized_path} ":
                domain_mismatch_penalty += 1.2
            if {"yonetim", "panel", "kullanici"}.issubset(q_tokens) and "kullanici yonetim" not in normalized_path:
                domain_mismatch_penalty += 1.2
            lexical_support = (
                (2.5 * document_entity_overlap)
                + (2.0 * exact_identity_overlap)
                + (0.6 * content_entity_overlap)
                + (0.9 * doc_overlap)
                + (0.8 * token_overlap)
                + (0.25 * action_overlap)
                + section_boost
                + (0.9 * domain_overlap)
                + guide_hint_boost
                - domain_mismatch_penalty
            )
            generic_only_penalty = (
                0.45
                if not document_entity_overlap and not content_entity_overlap
                and doc_overlap == 0 and token_overlap <= 0.25
                else 0.0
            )
            ranked.append(
                RankedChunk(
                    chunk=chunk,
                    semantic_rank=semantic_rank,
                    rerank_score=(
                        chunk.similarity_score
                        + lexical_support
                        - generic_only_penalty
                    ),
                    lexical_support=lexical_support,
                )
            )
        return sorted(
            ranked,
            key=lambda item: (-item.rerank_score, item.semantic_rank),
        )

    def hinted_path(self, question: str) -> str | None:
        """Resolve a bounded product workflow hint even outside semantic top-k."""
        question_tokens = set(self._normalizer.tokens(question))
        return next(
            (
                expected_path
                for required_tokens, expected_path in self.GUIDE_HINTS
                if set(required_tokens).issubset(question_tokens)
            ),
            None,
        )

    @staticmethod
    def dominant_path(ranked: list[RankedChunk]) -> str | None:
        """Select a document only when deterministic support is meaningful."""
        if not ranked:
            return None
        document_support: dict[str, float] = {}
        for item in ranked:
            path = item.chunk.relative_path
            document_support[path] = max(
                document_support.get(path, 0.0), item.lexical_support
            )
        best_path, support = max(
            document_support.items(), key=lambda item: item[1]
        )
        return best_path if support >= 0.35 else None

    @staticmethod
    def top_document_paths(
        ranked: list[RankedChunk],
        limit: int,
    ) -> list[str]:
        """Return distinct document paths in reranked evidence order."""
        paths: list[str] = []
        for item in ranked:
            if item.chunk.relative_path not in paths:
                paths.append(item.chunk.relative_path)
            if len(paths) >= limit:
                break
        return paths

    def select_siblings(
        self,
        question: str,
        dominant_candidates: list[RetrievedChunk],
        siblings: list[RetrievedChunk],
        max_chunks: int,
        intent: QuestionIntent = QuestionIntent.GENERAL_INFORMATION,
    ) -> list[RetrievedChunk]:
        """Choose bounded evidence sections and preserve source chunk order."""
        combined: dict[int, RetrievedChunk] = {
            item.chunk_index: item for item in [*dominant_candidates, *siblings]
        }
        chosen: list[RetrievedChunk] = []
        priorities = self.SECTION_PRIORITIES[intent]
        if intent == QuestionIntent.NAVIGATION:
            priorities = ("menu yol", "baslik")
        elif intent == QuestionIntent.PROCEDURE:
            priorities = ("kullanim adim", "gorunur kontrol", "alan")
        elif intent == QuestionIntent.FIELD_LISTING:
            priorities = ("alan",)
        elif intent == QuestionIntent.FIELD_PURPOSE:
            priorities = ("alan",)
        elif intent == QuestionIntent.CONTROL_PURPOSE:
            priorities = ("gorunur kontrol",)
        # First take one chunk from each evidence type so a long procedure
        # section cannot crowd controls and fields out of the final context.
        for preferred in priorities:
            matching = [
                item
                for item in combined.values()
                if (
                    preferred == "baslik"
                    and item.chunk_index == 0
                ) or self._normalizer.phrase(item.section_title).startswith(preferred)
            ]
            if matching:
                best = max(
                    matching,
                    key=lambda item: (
                        self._label_overlap(question, item.chunk_text),
                        -item.chunk_index,
                    ),
                )
                if best not in chosen:
                    chosen.append(best)
                if len(chosen) >= max_chunks:
                    return sorted(chosen, key=lambda chunk: chunk.chunk_index)
        # Then add remaining chunks in source order within priority sections.
        for preferred in priorities:
            matching = [
                item for item in combined.values()
                if (preferred == "baslik" and item.chunk_index == 0)
                or self._normalizer.phrase(item.section_title).startswith(preferred)
            ]
            for item in sorted(matching, key=lambda chunk: chunk.chunk_index):
                if item not in chosen:
                    chosen.append(item)
                if len(chosen) >= max_chunks:
                    return sorted(chosen, key=lambda chunk: chunk.chunk_index)
        if intent in {
            QuestionIntent.NAVIGATION,
            QuestionIntent.FIELD_LISTING,
            QuestionIntent.FIELD_PURPOSE,
            QuestionIntent.CONTROL_PURPOSE,
        }:
            return sorted(chosen, key=lambda chunk: chunk.chunk_index)
        for item in dominant_candidates:
            if item not in chosen:
                chosen.append(item)
            if len(chosen) >= max_chunks:
                break
        return sorted(chosen, key=lambda chunk: chunk.chunk_index)

    def _label_overlap(self, question: str, content: str) -> int:
        """Score exact requested-label evidence inside one sibling chunk."""
        question_tokens = set(self._normalizer.tokens(question))
        content_tokens = set(self._normalizer.tokens(content))
        return len(question_tokens & content_tokens)

    @staticmethod
    def strongest_direct_chunks(
        ranked: list[RankedChunk],
        max_chunks: int,
    ) -> list[RetrievedChunk]:
        """Avoid padding low-confidence context with unrelated candidates."""
        direct = [item.chunk for item in ranked if item.lexical_support >= 0.35]
        if not direct and len(ranked) == 1:
            direct = [ranked[0].chunk]
        return direct[:max_chunks]
