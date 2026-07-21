"""Build final prompts from managed prompt files and user messages."""

from collections.abc import Sequence
from pathlib import Path
import re

from app.retrieval.models import RetrievedChunk
from app.retrieval.intent import IntentClassifier, QuestionIntent


class PromptBuilder:
    """Combine system, developer, and user prompt sections."""

    def __init__(
        self,
        system_prompt_path: Path,
        developer_prompt_path: Path,
    ) -> None:
        self._system_prompt = self._read_prompt(system_prompt_path)
        self._developer_prompt = self._read_prompt(developer_prompt_path)

    @classmethod
    def from_defaults(cls) -> "PromptBuilder":
        """Create a builder using the application's default prompt files."""
        app_directory = Path(__file__).resolve().parent.parent
        return cls(
            system_prompt_path=(
                app_directory / "system_prompts" / "default.txt"
            ),
            developer_prompt_path=(
                app_directory / "developer_prompts" / "default.txt"
            ),
        )

    def build(
        self,
        user_message: str,
        retrieved_context: Sequence[RetrievedChunk] | None = None,
    ) -> str:
        """Return one final prompt with optional knowledge context."""
        sections = [
            f"SYSTEM PROMPT\n{self._system_prompt}",
            f"DEVELOPER PROMPT\n{self._developer_prompt}",
        ]
        intent: QuestionIntent | None = None
        evidence_available = False
        navigation_hint = "not applicable"
        creation_hint = "not applicable"
        if retrieved_context:
            intent = IntentClassifier.classify(user_message)
            expected_sections = {
                QuestionIntent.NAVIGATION: ("Menü yolu",),
                QuestionIntent.PROCEDURE: ("Kullanım adımları",),
                QuestionIntent.FIRST_ACTION: ("Kullanım adımları", "Görünür kontroller"),
                QuestionIntent.FIELD_LISTING: ("Alanlar",),
                QuestionIntent.FIELD_PURPOSE: ("Alanlar",),
                QuestionIntent.CONTROL_PURPOSE: ("Görünür kontroller",),
                QuestionIntent.COMPARISON: ("Alanlar", "Kapsam"),
                QuestionIntent.CONCEPT_DEFINITION: (
                    "Tanım", "Açıklama", "Genel Bakış", "Giriş", "Kapsam",
                ),
                QuestionIntent.PRODUCT_OVERVIEW: (
                    "Giriş", "Genel Bakış", "Tanım", "Açıklama", "Kapsam",
                ),
                QuestionIntent.GENERAL_INFORMATION: (),
            }[intent]
            evidence_available = any(
                any(
                    expected.casefold() in chunk.section_title.casefold()
                    for expected in expected_sections
                )
                for chunk in retrieved_context
            ) if expected_sections else bool(retrieved_context)
            if intent in {
                QuestionIntent.CONCEPT_DEFINITION,
                QuestionIntent.PRODUCT_OVERVIEW,
            }:
                evidence_available = any(
                    chunk.definition_evidence
                    or chunk.concept_evidence_level == "synthesis_sufficient"
                    for chunk in retrieved_context
                )
            answer_shapes = {
                QuestionIntent.NAVIGATION: "Give the exact supported menu path, then add one brief explanatory sentence. Use 2-4 sentences total.",
                QuestionIntent.PROCEDURE: "Return ordered supported steps in source order and briefly explain each supported step.",
                QuestionIntent.FIRST_ACTION: "State the first supported button or action directly, then briefly explain what happens next. Use 2-4 sentences.",
                QuestionIntent.FIELD_LISTING: "Return a clean list of supported fields and briefly explain important field purposes when the evidence supports them.",
                QuestionIntent.FIELD_PURPOSE: "Explain only the requested field's supported purpose naturally in 1-3 paragraphs.",
                QuestionIntent.CONTROL_PURPOSE: "Explain only the requested control's supported purpose naturally in 1-3 paragraphs.",
                QuestionIntent.COMPARISON: "Explain both supported concepts separately, then state their difference clearly in a structured answer.",
                QuestionIntent.CONCEPT_DEFINITION: "Explain the requested concept's definition, purpose, Antikor context, and practical use when explicitly supported. Use 2-4 concise paragraphs; do not add procedures or menu paths.",
                QuestionIntent.PRODUCT_OVERVIEW: "Provide a 3-6 paragraph overview covering the supported definition, purpose, main capabilities, and typical use areas.",
                QuestionIntent.GENERAL_INFORMATION: "Use the most directly relevant supported answer form.",
            }
            navigation_hint = (
                self._navigation_path_hint(retrieved_context)
                if intent == QuestionIntent.NAVIGATION else "not applicable"
            )
            creation_hint = (
                self._creation_control_hint(retrieved_context)
                if intent in (QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION)
                else "not applicable"
            )
            sections.append(
                "QUESTION INTENT METADATA\n"
                f"QUESTION_INTENT: {intent.value}\n"
                f"EVIDENCE_AVAILABLE: {str(evidence_available).lower()}\n"
                "EXPECTED_EVIDENCE_SECTION: "
                f"{', '.join(expected_sections) if expected_sections else 'directly relevant context'}\n"
                f"ANSWER_SHAPE: {answer_shapes[intent]}\n"
                f"NAVIGATION_PATH_HINT: {navigation_hint}\n"
                f"CREATION_CONTROL_HINT: {creation_hint}\n"
                "If EVIDENCE_AVAILABLE is true, never claim that the requested information is missing. "
                "For navigation, when NAVIGATION_PATH_HINT is not unavailable, preserve that exact path and add only one brief supported explanation. "
                "For procedure or first_action, when CREATION_CONTROL_HINT is not unavailable, begin with that exact control and continue only with supported steps. "
                "For navigation, reject descriptive menu text that does not form a path for the exact guide entity; "
                "the exact guide title and matching source URL path segments may be used as navigation evidence."
            )
            if intent in {
                QuestionIntent.CONCEPT_DEFINITION,
                QuestionIntent.PRODUCT_OVERVIEW,
            }:
                requested_term = IntentClassifier.definition_term(user_message)
                evidence_level = next(
                    (
                        chunk.concept_evidence_level
                        for chunk in retrieved_context
                        if chunk.concept_evidence_level != "insufficient"
                    ),
                    "insufficient",
                )
                sections.append(
                    "DEFINITION EVIDENCE CONTRACT\n"
                    f"REQUESTED_TERM: {requested_term or user_message}\n"
                    f"CONCEPT_EVIDENCE_LEVEL: {evidence_level}\n"
                    "The first sentence must begin with REQUESTED_TERM and directly define it. "
                    "Do not primarily define another concept merely because it appears nearby. "
                    "When CONCEPT_EVIDENCE_LEVEL is synthesis_sufficient, the sources may not contain a single dictionary-style definition. "
                    "Infer a concise technical definition only from the supplied evidence by combining purpose, fields, controls, and procedure details. "
                    "Explain what it is, what it does, why it is used, and how it appears in Antikor; add a brief practical example only when supported. "
                    "Use only sources containing the exact requested term. "
                    "Prefer product documents and explicit definition or introduction sections. "
                    "Do not answer from menu paths, controls, fields, or procedures. "
                    "Do not provide a generic definition from model knowledge."
                )
            sections.append(
                "KNOWLEDGE CONTEXT\n"
                f"{self._format_context(retrieved_context)}"
            )
            has_arrow_workflow = any(
                "->" in chunk.chunk_text for chunk in retrieved_context
            )
            has_ordered_steps = any(
                "kullanım adımları" in chunk.section_title.casefold()
                for chunk in retrieved_context
            )
            if has_arrow_workflow or has_ordered_steps:
                sections.append(
                    "EVIDENCE SUFFICIENCY NOTE\n"
                    "The directly relevant context contains an explicit "
                    "workflow or a Kullanım adımları section. Treat it as "
                    "sufficient procedural evidence. Do not claim that the "
                    "requested steps are unavailable. Present supported "
                    "actions in source order without adding steps, and include "
                    "a visible creation control when the context explicitly "
                    "describes it as creating a new record."
                )
        sections.append(
            "ANSWER FOCUS CONTRACT\n"
            "Treat the exact user question below as a strict boundary. "
            "Answer naturally, clearly, and with useful completeness in Turkish. "
            "Use only context that directly answers its entity and action. "
            "Preserve exact UI labels. Never mention retrieval, context, prompts, or internal mechanics. "
            "If the requested procedure or button behavior is not explicitly "
            "present, give one concise limitation in the same language as the "
            "question and stop. For a Turkish question, never switch to English. "
            "Do not append adjacent topics or generic background."
        )
        if intent is not None:
            mandatory = (
                "Because evidence is available, do not use a missing-information limitation."
                if evidence_available else
                "Do not claim evidence exists beyond the supplied context."
            )
            if intent == QuestionIntent.NAVIGATION and navigation_hint != "unavailable":
                mandatory += (
                    f" Include this exact path: {navigation_hint}. Add one brief evidence-supported explanatory sentence."
                )
            elif intent in (QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION) and creation_hint != "unavailable":
                mandatory += f" Begin the answer with this control: {creation_hint}"
            sections.append(
                "MANDATORY INTENT OUTPUT CONTRACT\n"
                f"INTENT: {intent.value}\n{mandatory}"
            )
        sections.append(f"USER MESSAGE\n{user_message}")
        return "\n\n".join(sections)

    @staticmethod
    def _navigation_path_hint(
        retrieved_context: Sequence[RetrievedChunk],
    ) -> str:
        """Derive a conservative path hint directly from menu evidence."""
        if not retrieved_context:
            return "unavailable"
        for chunk in retrieved_context:
            if "menü yolu" not in chunk.section_title.casefold():
                continue
            labels = re.findall(r"`([^`]+)`", chunk.chunk_text)
            paths = [
                label.strip() for label in labels
                if " > " in label and "->" not in label
            ]
            if paths:
                return paths[0]
            screens = [
                label.strip() for label in labels
                if "->" not in label and len(label.strip()) <= 100
            ]
            if screens:
                return screens[0]
        return "unavailable"

    @staticmethod
    def _creation_control_hint(
        retrieved_context: Sequence[RetrievedChunk],
    ) -> str:
        """Return an explicitly visible control described as creating a record."""
        labels: list[str] = []
        for chunk in retrieved_context:
            if "görünür kontroller" not in chunk.section_title.casefold():
                continue
            for line in chunk.chunk_text.splitlines():
                if "ekle" not in line.casefold():
                    continue
                match = re.search(r"`([^`]+)`", line)
                if match and "ekle" in match.group(1).casefold():
                    labels.append(match.group(1).strip())
        if not labels:
            return "unavailable"
        return next((label for label in labels if label.startswith("+")), labels[0])

    @staticmethod
    def _format_context(
        retrieved_context: Sequence[RetrievedChunk],
    ) -> str:
        """Format retrieved chunks as clearly separated prompt sources."""
        sources = []
        for source_index, chunk in enumerate(
            retrieved_context,
            start=1,
        ):
            sources.append(
                "\n".join(
                    (
                        f"### Source {source_index}",
                        f"Document: {chunk.relative_path}",
                        f"Section: {chunk.section_title}",
                        "Content:",
                        chunk.chunk_text,
                    )
                )
            )
        return "\n\n".join(
            (
                "## Knowledge Context",
                *sources,
            )
        )

    @staticmethod
    def _read_prompt(path: Path) -> str:
        """Read and validate one managed prompt file."""
        prompt = path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise ValueError(f"Prompt file cannot be empty: {path}")
        return prompt
