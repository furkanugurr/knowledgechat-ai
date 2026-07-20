"""Validate structured RAG answers and build evidence-only fallbacks."""
from __future__ import annotations
import re

from app.retrieval.intent import QuestionIntent
from app.retrieval.models import RetrievedChunk
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer
from app.knowledge.evidence import has_usable_evidence


class GroundedAnswerGuard:
    """Reject common groundedness failures without another model call."""

    _LIMITATIONS = (
        "bilgi bulunamadı", "açıkça yer almıyor", "mevcut değil",
        "yer almamaktadır", "sağlanmamıştır",
    )
    _LABEL = re.compile(chr(96) + "([^" + chr(96) + "]+)" + chr(96))
    _STEP = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
    _BULLET = re.compile(r"^\s*-\s+(.+?)\s*$", re.MULTILINE)

    def __init__(self) -> None:
        self._normalizer = TurkishLexicalNormalizer()

    def structured_fast_path(
        self,
        question: str,
        intent: QuestionIntent,
        chunks: list[RetrievedChunk],
        navigation_hint: str | None = None,
        creation_hint: str | None = None,
    ) -> tuple[str, list[RetrievedChunk]] | None:
        """Build an evidence-only answer for safe, structured intents."""
        if intent not in {
            QuestionIntent.NAVIGATION,
            QuestionIntent.FIRST_ACTION,
            QuestionIntent.FIELD_LISTING,
        }:
            return None
        if len({item.relative_path for item in chunks}) != 1:
            return None
        supporting = [
            item for item in chunks
            if self._section_matches(intent, item.section_title)
            and has_usable_evidence(item.chunk_text)
        ]
        if intent == QuestionIntent.FIRST_ACTION and creation_hint not in {
            None, "unavailable"
        }:
            control_chunks = [
                item for item in supporting
                if creation_hint.casefold() in item.chunk_text.casefold()
            ]
            if control_chunks:
                supporting = control_chunks
        if not supporting or not any(item.chunk_text.strip() for item in supporting):
            return None
        answer = self._fallback(
            question, intent, supporting, navigation_hint, creation_hint
        )
        return (answer, supporting) if answer else None

    def ensure_grounded(
        self,
        question: str,
        intent: QuestionIntent,
        chunks: list[RetrievedChunk],
        answer: str,
        navigation_hint: str | None = None,
        creation_hint: str | None = None,
    ) -> str:
        evidence = "\n".join(item.chunk_text for item in chunks)
        evidence_folded = evidence.casefold()
        answer_folded = answer.casefold()
        labels = self._LABEL.findall(evidence)
        requested = [
            label for label in labels
            if self._normalizer.phrase(label) in self._normalizer.phrase(question)
        ]
        unknown = [
            label for label in self._LABEL.findall(answer)
            if label.casefold() not in evidence_folded
        ]
        false_limitation = any(item in answer_folded for item in self._LIMITATIONS)
        missing_requested = bool(requested) and any(
            label.casefold() not in answer_folded for label in requested
        )
        missing_shape_evidence = self._missing_shape_evidence(
            intent, evidence, answer
        )
        structured = intent in {
            QuestionIntent.NAVIGATION, QuestionIntent.PROCEDURE,
            QuestionIntent.FIRST_ACTION, QuestionIntent.FIELD_LISTING,
            QuestionIntent.FIELD_PURPOSE, QuestionIntent.CONTROL_PURPOSE,
            QuestionIntent.GENERAL_INFORMATION,
        }
        if not structured or not (
            unknown or false_limitation or missing_requested
            or missing_shape_evidence
        ):
            return answer
        fallback = self._fallback(
            question, intent, chunks, navigation_hint, creation_hint
        )
        return fallback or answer

    def _missing_shape_evidence(
        self,
        intent: QuestionIntent,
        evidence: str,
        answer: str,
    ) -> bool:
        """Require the minimum source facts for each structured answer shape."""
        normalized_answer = self._normalizer.phrase(answer)
        if intent == QuestionIntent.NAVIGATION:
            bullets = self._BULLET.findall(evidence)
            paths = [item for item in bullets if ">" in item]
            marker = paths[0] if paths else (bullets[0] if bullets else "")
            return bool(marker) and (
                self._normalizer.phrase(marker) not in normalized_answer
                or answer.count(">") > 1
            )
        if intent == QuestionIntent.FIELD_LISTING:
            labels = list(dict.fromkeys(self._LABEL.findall(evidence)))
            return bool(labels) and any(
                self._normalizer.phrase(label) not in normalized_answer
                for label in labels
            )
        if intent in {QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION}:
            steps = [text.strip() for _, text in self._STEP.findall(evidence)]
            if not steps:
                return False
            required_steps = steps[:1] if intent == QuestionIntent.FIRST_ACTION else [steps[0], steps[-1]]
            for step in required_steps:
                labels = self._LABEL.findall(step)
                marker = labels[0] if labels else " ".join(step.split()[:3])
                if self._normalizer.phrase(marker) not in normalized_answer:
                    return True
        return False

    def _fallback(
        self,
        question: str,
        intent: QuestionIntent,
        chunks: list[RetrievedChunk],
        navigation_hint: str | None = None,
        creation_hint: str | None = None,
    ) -> str | None:
        ordered = sorted(chunks, key=lambda item: item.chunk_index)
        ordered = [item for item in ordered if has_usable_evidence(item.chunk_text)]
        relevant = [
            item.chunk_text for item in ordered
            if self._section_matches(intent, item.section_title)
        ]
        evidence = "\n".join(relevant)
        if intent == QuestionIntent.NAVIGATION:
            bullets = self._BULLET.findall(evidence)
            paths = [item for item in bullets if ">" in item]
            normalized_question = self._normalizer.phrase(question)
            matching = [
                item for item in bullets
                if any(
                    self._normalizer.phrase(part) in normalized_question
                    or (
                        len(set(self._normalizer.tokens(part))) >= 2
                        and len(
                            set(self._normalizer.tokens(part))
                            & set(self._normalizer.tokens(question))
                        ) / len(set(self._normalizer.tokens(part))) >= 0.6
                    )
                    for part in item.strip(chr(96)).split(">")
                    if self._normalizer.phrase(part)
                )
            ]
            if matching:
                return min(matching, key=len).strip().strip(chr(96))
            if navigation_hint and navigation_hint != "unavailable":
                return navigation_hint
            if paths:
                return paths[0].strip().strip(chr(96))
            return bullets[0].strip().strip(chr(96)) if bullets else None
        if intent in {QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION}:
            if (
                intent == QuestionIntent.FIRST_ACTION
                and creation_hint and creation_hint != "unavailable"
            ):
                return creation_hint
            steps = [text.strip() for _, text in self._STEP.findall(evidence)]
            steps = list(dict.fromkeys(steps))
            if not steps:
                return None
            if intent == QuestionIntent.FIRST_ACTION:
                return (
                    creation_hint
                    if creation_hint and creation_hint != "unavailable"
                    else steps[0]
                )
            if creation_hint and creation_hint != "unavailable" and not any(
                creation_hint.casefold() in step.casefold() for step in steps
            ):
                steps.insert(0, creation_hint)
            return "\n".join(f"{index}. {step}" for index, step in enumerate(steps, 1))
        if intent == QuestionIntent.FIELD_LISTING:
            labels = list(dict.fromkeys(self._LABEL.findall(evidence)))
            if not labels:
                return None
            return "Desteklenen alanlar:\n" + "\n".join(f"- {label}" for label in labels)
        if intent == QuestionIntent.GENERAL_INFORMATION:
            content = "\n".join(
                item.chunk_text for item in ordered
                if "kapsam" in item.section_title.casefold()
            )
            content = re.sub(r"^##\s+Kapsam\s*", "", content).strip()
            return content or None
        bullets = self._BULLET.findall(evidence)
        if not bullets:
            return None
        question_tokens = set(self._normalizer.tokens(question))
        best = max(
            bullets,
            key=lambda item: len(question_tokens & set(self._normalizer.tokens(item))),
        )
        return best.strip()

    @staticmethod
    def _section_matches(intent: QuestionIntent, section: str) -> bool:
        folded = section.casefold()
        if intent == QuestionIntent.NAVIGATION:
            return "menü yolu" in folded
        if intent in {QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION}:
            return (
                "kullanım adımları" in folded
                or (
                    intent == QuestionIntent.FIRST_ACTION
                    and "görünür kontroller" in folded
                )
            )
        if intent in {QuestionIntent.FIELD_LISTING, QuestionIntent.FIELD_PURPOSE}:
            return "alanlar" in folded
        return "görünür kontroller" in folded
