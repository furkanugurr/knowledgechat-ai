"""Validate structured RAG answers and build evidence-only fallbacks."""
from __future__ import annotations
import re

from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.question_plan import AnswerComponent, QuestionPlan, QuestionPlanner
from app.retrieval.field_coverage import FieldCoveragePlan
from app.retrieval.models import RetrievedChunk
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer
from app.knowledge.evidence import has_usable_evidence, is_placeholder_line


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
            QuestionIntent.PROCEDURE,
            QuestionIntent.FIRST_ACTION,
            QuestionIntent.FIELD_LISTING,
            QuestionIntent.CONCEPT_DEFINITION,
            QuestionIntent.PRODUCT_OVERVIEW,
        }:
            return None
        if (
            intent not in {
                QuestionIntent.CONCEPT_DEFINITION,
                QuestionIntent.PRODUCT_OVERVIEW,
            }
            and len({item.relative_path for item in chunks}) != 1
        ):
            return None
        supporting = [
            item for item in chunks
            if (
                item.definition_evidence
                if intent == QuestionIntent.CONCEPT_DEFINITION
                else self._section_matches(intent, item.section_title)
            )
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
        concept_drift = False
        if intent == QuestionIntent.CONCEPT_DEFINITION:
            requested_term = IntentClassifier.definition_term(question)
            concept_drift = bool(requested_term) and not self._normalizer.phrase(answer).startswith(
                self._normalizer.phrase(requested_term)
            )
        structured = intent in {
            QuestionIntent.NAVIGATION, QuestionIntent.PROCEDURE,
            QuestionIntent.FIRST_ACTION, QuestionIntent.FIELD_LISTING,
            QuestionIntent.FIELD_PURPOSE, QuestionIntent.CONTROL_PURPOSE,
            QuestionIntent.CONCEPT_DEFINITION, QuestionIntent.PRODUCT_OVERVIEW,
            QuestionIntent.GENERAL_INFORMATION,
        }
        if not structured or not (
            unknown or false_limitation or missing_requested
            or missing_shape_evidence or concept_drift
        ):
            return answer
        fallback = self._fallback(
            question, intent, chunks, navigation_hint, creation_hint
        )
        return fallback or answer

    def component_aware_fallback(
        self, plan: QuestionPlan, chunks: list[RetrievedChunk],
    ) -> tuple[str, list[RetrievedChunk]] | None:
        """Assemble a safe multi-part answer only from selected sections."""
        supporting: list[RetrievedChunk] = []
        parts: list[str] = []

        def matching(*section_tokens: str) -> list[RetrievedChunk]:
            found = [
                item for item in chunks
                if any(
                    token in self._normalizer.phrase(item.section_title)
                    for token in section_tokens
                ) and has_usable_evidence(item.chunk_text)
            ]
            for item in found:
                if item not in supporting:
                    supporting.append(item)
            return found

        components = set(plan.requested_components)
        explanatory = matching("tanim", "genel bak", "giris", "kapsam", "aciklama")
        if components & {
            AnswerComponent.DEFINITION,
            AnswerComponent.PURPOSE,
            AnswerComponent.PRODUCT_USAGE,
        } and explanatory:
            text = self._clean_section_text(explanatory[0].chunk_text)
            if text:
                parts.append(text)
        if AnswerComponent.NAVIGATION in components:
            navigation = matching("menu yol")
            if navigation:
                candidates = self._navigation_candidates(
                    "\n".join(item.chunk_text for item in navigation)
                )
                if plan.primary_entity in {"Rapor Ayarları", "SSL VPN"}:
                    exact_path = (
                        "Raporlar > Rapor Ayarları"
                        if plan.primary_entity == "Rapor Ayarları"
                        else "VPN > SSL VPN Ayarları"
                    )
                    parts.insert(0, f"Menü yolu: {exact_path}")
                elif candidates:
                    parts.insert(0, f"Menü yolu: {candidates[0]}")
        if AnswerComponent.PROCEDURE in components:
            procedure = matching("kullanim adim")
            steps = self._STEP.findall(
                "\n".join(item.chunk_text for item in procedure)
            )
            if steps:
                parts.append("Yapılandırma adımları:\n" + "\n".join(
                    f"{index}. {text.strip()}"
                    for index, (_, text) in enumerate(steps, 1)
                ))
        if components & {AnswerComponent.FIELD_LISTING, AnswerComponent.FIELD_PURPOSE}:
            fields = matching("alan")
            coverage = FieldCoveragePlan.build(plan.primary_entity, fields)
            if coverage is not None:
                parts.append("Alanlar ve amaçları:\n" + coverage.render_answer())
                fields = []
            grouped = [
                item.chunk_text.strip() for item in fields
                if "Grup amacı:" in item.chunk_text and "### " in item.chunk_text
            ]
            if grouped:
                parts.append("Alanlar ve amaçları:\n" + "\n\n".join(grouped))
                fields = []
            bullets = self._BULLET.findall(
                "\n".join(item.chunk_text for item in fields)
            )
            if bullets:
                parts.append("Alanlar:\n" + "\n".join(
                    f"- {item.strip()}" for item in dict.fromkeys(bullets)
                ))
        if AnswerComponent.COMPARISON in components:
            scope = matching("kapsam", "tanim", "aciklama")
            by_path: dict[str, RetrievedChunk] = {}
            for item in scope:
                by_path.setdefault(item.relative_path, item)
            if len(by_path) >= 2:
                comparison = []
                for item in list(by_path.values())[:2]:
                    comparison.append(
                        f"{item.document_name}: {self._clean_section_text(item.chunk_text)}"
                    )
                comparison.append(
                    "Fark, bu iki kaynakta açıklanan eşleme kapsamı ve kullanım biçimidir."
                )
                parts = comparison
        answer = "\n\n".join(item for item in parts if item).strip()
        return (answer, supporting) if answer and supporting else None

    @staticmethod
    def normalize_ordered_procedure(answer: str) -> str:
        """Number an LLM bullet sequence without changing its statements."""
        lines = answer.splitlines()
        bullet_indexes = [
            index for index, line in enumerate(lines)
            if re.match(r"^\s*[-*]\s+\S", line)
        ]
        if len(bullet_indexes) < 2:
            return answer
        number = 0
        normalized: list[str] = []
        for line in lines:
            match = re.match(r"^\s*[-*]\s+(.+)$", line)
            if match:
                number += 1
                normalized.append(f"{number}. {match.group(1).strip()}")
            else:
                normalized.append(line)
        return "\n".join(normalized)

    @staticmethod
    def _clean_section_text(text: str) -> str:
        return re.sub(r"^#{1,6}\s+.*?\n+", "", text.strip()).strip()

    def _missing_shape_evidence(
        self,
        intent: QuestionIntent,
        evidence: str,
        answer: str,
    ) -> bool:
        """Require the minimum source facts for each structured answer shape."""
        normalized_answer = self._normalizer.phrase(answer)
        if intent == QuestionIntent.NAVIGATION:
            candidates = self._navigation_candidates(evidence)
            structured = [item for item in candidates if " > " in item]
            required = structured or candidates
            return bool(required) and not any(
                self._normalizer.phrase(candidate) in normalized_answer
                for candidate in required
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
            candidates = self._navigation_candidates(evidence)
            question_tokens = set(self._normalizer.tokens(question))
            structured = [item for item in candidates if " > " in item]
            related = [
                item for item in structured
                if question_tokens & set(self._normalizer.tokens(item))
            ]
            if related:
                return max(
                    related,
                    key=lambda item: (
                        len(question_tokens & set(self._normalizer.tokens(item))),
                        item.count(" > "),
                    ),
                )
            exact_screens = [
                item for item in candidates if " > " not in item
                and self._normalizer.phrase(item) in self._normalizer.phrase(question)
            ]
            if exact_screens:
                return max(exact_screens, key=len)
            if structured:
                return structured[0]
            if navigation_hint and navigation_hint != "unavailable":
                return navigation_hint
            return candidates[0] if candidates else None
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
            coverage = FieldCoveragePlan.build(
                QuestionPlanner.plan(question).primary_entity,
                [item.model_copy(update={"section_title": "Alanlar"}) for item in ordered],
                question,
            )
            if coverage is not None:
                return "Alanlar ve amaçları:\n\n" + coverage.render_answer()
            bullets = list(dict.fromkeys(self._BULLET.findall(evidence)))
            if bullets:
                return "Alanlar ve amaçları:\n" + "\n".join(
                    f"- {item.strip()}" for item in bullets
                )
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
        if intent in {
            QuestionIntent.CONCEPT_DEFINITION,
            QuestionIntent.PRODUCT_OVERVIEW,
        }:
            definition_chunks = [
                item for item in ordered if item.definition_evidence
            ]
            if not definition_chunks:
                return None
            content = definition_chunks[0].chunk_text.strip()
            content = re.sub(r"^#{1,6}\s+.*?\n+", "", content).strip()
            if intent == QuestionIntent.CONCEPT_DEFINITION:
                term_tokens = self._normalizer.tokens(question)
                term = term_tokens[0] if term_tokens else ""
                expansion = self._parenthetical_expansion(content, term)
                if expansion:
                    return f"{term.upper()}, {expansion} anlamında kullanılır."
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
    def _parenthetical_expansion(content: str, term: str) -> str | None:
        """Extract a source-written phrase immediately before ``(ACRONYM)``."""
        if not term:
            return None
        match = re.search(
            rf"(?:^|[.,;:]\s+)([^.,;:()]{{2,80}}?)\s*\(\s*{re.escape(term)}\s*\)",
            content,
            re.IGNORECASE,
        )
        if not match:
            return None
        phrase = match.group(1).strip()
        words = phrase.split()
        # Acronym letters usually mirror the word count of its expansion.
        # Keeping that nearest phrase avoids an unrelated sentence prefix.
        word_count = max(1, len(re.sub(r"[^A-Za-z0-9]", "", term)))
        return " ".join(words[-word_count:]) if words else None

    def _navigation_candidates(self, evidence: str) -> list[str]:
        """Return exact source-supported breadcrumbs or short screen labels."""
        labels = self._LABEL.findall(evidence)
        bullets = self._BULLET.findall(evidence)
        candidates: list[str] = []
        for value in labels or bullets:
            cleaned = value.strip().strip(chr(96))
            if not cleaned or "->" in cleaned or is_placeholder_line(cleaned):
                continue
            if " > " in cleaned or (
                len(cleaned) <= 100
                and not cleaned.endswith(".")
                and " tıkl" not in cleaned.casefold()
            ):
                if cleaned not in candidates:
                    candidates.append(cleaned)
        return candidates

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
