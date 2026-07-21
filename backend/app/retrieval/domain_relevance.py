"""Deterministic Antikor-domain relevance scoring for retrieved evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.retrieval.models import RetrievedChunk
from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class DomainRelevanceDecision:
    """Internal domain gate result; never exposed through the public API."""

    domain_relevant: bool
    reason: str | None
    top_similarity: float
    lexical_overlap: float
    guide_confidence: float
    confidence_tier: str
    entity_signal: bool
    ui_label_signal: bool
    category_signal: bool
    lexical_signal: bool
    semantic_signal: bool
    guide_agreement_signal: bool
    final_decision_reason: str


class DomainRelevanceGate:
    """Classify questions from several independent retrieval signals."""

    DOMAIN_TERMS = frozenset({
        "antikor", "ag", "arayuz", "baglanti", "dhcp", "dns", "ethernet",
        "firewall", "guvenlik", "hotspot", "ip", "ipsec", "kullanici",
        "log", "nat", "profil", "proxy", "rapor", "sdwan", "sertifika",
        "ssl", "trafik", "vpn", "yonlendirme",
    })
    QUERY_STOPWORDS = frozenset({
        "acaba", "alan", "ayari", "ayar", "ekran", "faydali", "hangi",
        "icin", "ile", "mi", "miyim", "nasil", "nedir", "nerede",
        "nereden", "olur", "soru", "yarin",
    })
    MARKDOWN_LABEL = re.compile(
        r"`([^`]+)`|\*\*([^*]+)\*\*|^\s*[-*]\s+([^:\n]{2,80})\s*:",
        re.MULTILINE,
    )

    def __init__(
        self,
        min_similarity: float,
        min_lexical_overlap: float,
        min_guide_confidence: float,
    ) -> None:
        self._min_similarity = min_similarity
        self._medium_similarity = max(0.55, min_similarity - 0.10)
        self._min_lexical_overlap = min_lexical_overlap
        self._min_guide_confidence = min_guide_confidence
        self._normalizer = TurkishLexicalNormalizer()

    def evaluate(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        retrieval_diagnostics: dict[str, object] | None = None,
    ) -> DomainRelevanceDecision:
        """Decide relevance without allowing semantic score to veto identity."""
        if not chunks:
            return self._decision(
                False, "no_retrieved_evidence", 0.0, 0.0, 0.0,
                "low_confidence_or_out_of_domain", False, False, False,
                False, False, False,
            )

        diagnostics = retrieval_diagnostics or {}
        top_similarity = max(item.similarity_score for item in chunks)
        question_tokens = self._meaningful_tokens(question)
        evidence = " ".join(
            " ".join((item.document_name, item.relative_path,
                      item.section_title, item.chunk_text))
            for item in chunks
        )
        evidence_tokens = set(self._normalizer.tokens(evidence))
        matched = {
            token for token in question_tokens
            if any(self._tokens_match(token, candidate) for candidate in evidence_tokens)
        }
        lexical_overlap = len(matched) / max(len(question_tokens), 1)
        lexical_signal = lexical_overlap >= self._min_lexical_overlap
        semantic_signal = top_similarity >= self._min_similarity
        medium_semantic_signal = top_similarity >= self._medium_similarity
        normalized_question = self._normalizer.phrase(question)
        ui_labels = self._ui_labels(evidence)
        ui_label_signal = any(
            label and len(label) >= 3 and label in normalized_question
            for label in ui_labels
        )
        category_signal = bool(question_tokens & self.DOMAIN_TERMS)

        selected_paths = {item.relative_path for item in chunks}
        selected_path = next(iter(selected_paths)) if len(selected_paths) == 1 else None
        resolved_path = diagnostics.get("resolved_guide")
        dominant_path = diagnostics.get("dominant_path")
        guide_agreement_signal = bool(
            selected_path
            and (resolved_path == selected_path or dominant_path == selected_path)
        )
        comparison_agreement = bool(
            IntentClassifier.classify(question) == QuestionIntent.COMPARISON
            and 1 < len(selected_paths) <= 2
            and dominant_path in selected_paths
        )
        guide_agreement_signal = guide_agreement_signal or comparison_agreement
        entity_signal = bool(
            diagnostics.get("guide_entity_match")
            and (not resolved_path or resolved_path in selected_paths)
        )
        if entity_signal and selected_path and not (resolved_path or dominant_path):
            # Supports small test doubles and older internal callers that only
            # supplied the original entity flag. Production retrieval supplies
            # both paths and therefore still requires explicit agreement.
            guide_agreement_signal = True
        document_tokens = set(self._normalizer.tokens(chunks[0].document_name))
        document_overlap = bool(question_tokens & document_tokens)
        guide_confidence = float(diagnostics.get("guide_confidence", 0.0) or 0.0)
        if entity_signal:
            guide_confidence = max(guide_confidence, 1.0)
        elif guide_agreement_signal and document_overlap:
            guide_confidence = max(guide_confidence, 0.8)
        elif guide_agreement_signal and category_signal and lexical_signal:
            guide_confidence = max(guide_confidence, 0.6)

        # Exact/near-exact guide identity or an exact visible label is stronger
        # evidence than an embedding score and may safely bypass its strict tier.
        if guide_agreement_signal and (entity_signal or ui_label_signal):
            return self._decision(
                True, None, top_similarity, lexical_overlap, guide_confidence,
                "high_confidence_in_domain", entity_signal, ui_label_signal,
                category_signal, lexical_signal, semantic_signal,
                guide_agreement_signal,
            )

        # Without identity, require several independent signals and retain a
        # conservative (but lower) semantic floor.
        medium_relevant = bool(
            guide_agreement_signal
            and (category_signal or document_overlap)
            and (
                lexical_overlap >= max(self._min_lexical_overlap, 0.60)
                or guide_confidence >= 0.90
            )
            and medium_semantic_signal
            and guide_confidence >= self._min_guide_confidence
        )
        if medium_relevant:
            return self._decision(
                True, None, top_similarity, lexical_overlap, guide_confidence,
                "medium_confidence_in_domain", entity_signal, ui_label_signal,
                category_signal, lexical_signal, semantic_signal,
                guide_agreement_signal,
            )

        if not (entity_signal or ui_label_signal or category_signal):
            reason = "no_antikor_domain_signal"
        elif not guide_agreement_signal:
            reason = "retrieval_guide_agreement_missing"
        elif not lexical_signal:
            reason = "meaningful_lexical_overlap_below_threshold"
        elif not medium_semantic_signal:
            reason = "semantic_similarity_below_conservative_threshold"
        elif guide_confidence < self._min_guide_confidence:
            reason = "guide_confidence_below_threshold"
        else:
            reason = "insufficient_combined_domain_evidence"
        return self._decision(
            False, reason, top_similarity, lexical_overlap, guide_confidence,
            "low_confidence_or_out_of_domain", entity_signal, ui_label_signal,
            category_signal, lexical_signal, semantic_signal,
            guide_agreement_signal,
        )

    def _decision(
        self, relevant: bool, reason: str | None, top_similarity: float,
        lexical_overlap: float, guide_confidence: float, tier: str,
        entity: bool, ui_label: bool, category: bool, lexical: bool,
        semantic: bool, agreement: bool,
    ) -> DomainRelevanceDecision:
        final_reason = (
            "strong_entity_or_ui_label_with_guide_agreement"
            if tier == "high_confidence_in_domain"
            else "combined_category_lexical_semantic_guide_evidence"
            if tier == "medium_confidence_in_domain"
            else reason or "insufficient_combined_domain_evidence"
        )
        return DomainRelevanceDecision(
            relevant, reason, round(top_similarity, 6),
            round(lexical_overlap, 6), round(guide_confidence, 6), tier,
            entity, ui_label, category, lexical, semantic, agreement,
            final_reason,
        )

    def _ui_labels(self, evidence: str) -> set[str]:
        labels: set[str] = set()
        for match in self.MARKDOWN_LABEL.findall(evidence):
            value = next((part for part in match if part), "")
            normalized = self._normalizer.phrase(value)
            if normalized:
                labels.add(normalized)
        return labels

    def _meaningful_tokens(self, value: str) -> set[str]:
        return {
            token for token in self._normalizer.tokens(value)
            if len(token) >= 2 and token not in self.QUERY_STOPWORDS
        }

    @staticmethod
    def _tokens_match(first: str, second: str) -> bool:
        return first == second or (
            len(first) >= 5 and len(second) >= 5 and first[:5] == second[:5]
        )
