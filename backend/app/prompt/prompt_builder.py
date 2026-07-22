"""Build final prompts from managed prompt files and user messages."""

from collections.abc import Sequence
from pathlib import Path
import re

from app.retrieval.models import RetrievedChunk
from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.question_plan import AnswerComponent, QuestionPlanner
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


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
            plan = QuestionPlanner.plan(user_message)
            intent = plan.primary_intent
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
            if (
                intent == QuestionIntent.NAVIGATION
                and plan.primary_entity in {"Rapor Ayarları", "SSL VPN"}
                and any(
                    chunk.relative_path.replace("\\", "/").endswith(
                        "/raporlar/rapor-ayarlari.md"
                        if plan.primary_entity == "Rapor Ayarları"
                        else "/vpn/ssl-vpn-ayarlari.md"
                    )
                    for chunk in retrieved_context
                )
            ):
                navigation_hint = (
                    "Raporlar > Rapor Ayarları"
                    if plan.primary_entity == "Rapor Ayarları"
                    else "VPN > SSL VPN Ayarları"
                )
            creation_hint = (
                self._creation_control_hint(retrieved_context)
                if intent in (QuestionIntent.PROCEDURE, QuestionIntent.FIRST_ACTION)
                else "not applicable"
            )
            sections.append(
                "QUESTION INTENT METADATA\n"
                f"QUESTION_INTENT: {intent.value}\n"
                f"PRIMARY_ENTITY: {plan.primary_entity}\n"
                "REQUESTED_COMPONENTS: "
                f"{', '.join(item.value for item in plan.requested_components)}\n"
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
                requested_term = plan.primary_entity
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
                    "Use only the section types required by REQUESTED_COMPONENTS; "
                    "procedures or menu paths are allowed only when explicitly requested. "
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
            if plan.is_multi_part:
                sections.append(
                    "MULTI-PART ANSWER CONTRACT\n"
                    f"PRIMARY_ENTITY: {plan.primary_entity}\n"
                    "Cover every requested component exactly once and keep all clauses "
                    "scoped to PRIMARY_ENTITY. Do not let generic words such as amaç, "
                    "ayar, ekran, işlem or kullanılır introduce another source family.\n"
                    + self._component_format_contract(plan.requested_components)
                )
            if intent == QuestionIntent.PRODUCT_OVERVIEW:
                phrase = TurkishLexicalNormalizer.phrase(user_message)
                product_scope = (
                    "security_capabilities" if "temel guvenlik ozellik" in phrase
                    else "concrete_functions" if "ne ise yarar" in phrase
                    else "definition_and_overview"
                )
                sections.append(
                    "PRODUCT OVERVIEW BALANCE CONTRACT\n"
                    f"REQUESTED_PRODUCT_SCOPE: {product_scope}\n"
                    "Describe Antikor as the overall product first. Cover at least three "
                    "distinct supported core security capability categories when available. "
                    "SD-WAN is at most one brief supporting example. For concrete_functions, "
                    "lead with concrete security functions rather than national-production "
                    "positioning. For security_capabilities, use a structured capability list "
                    "and omit marketing statements. For definition_and_overview, present direct "
                    "definition, security purpose, broad capabilities and institutional use in "
                    "that order. Never add unsupported capabilities."
                )
            if (
                AnswerComponent.FIELD_LISTING in plan.requested_components
                and AnswerComponent.FIELD_PURPOSE in plan.requested_components
            ):
                sections.append(
                    "COMPLETE FIELD COVERAGE CONTRACT\n"
                    "The context may contain headings beginning with `###` followed by `Grup amacı:`. "
                    "Represent every such group and its stated purpose; do not stop after the first "
                    "chunk or group. Keep every UI label exactly as supplied. For long technical "
                    "sets, use the supplied functional group headings instead of an unstructured "
                    "identifier dump. Explain individual fields only from their source descriptions "
                    "and never infer an absent meaning."
                )
            if plan.primary_entity == "Rapor Ayarları" and (
                AnswerComponent.FIELD_LISTING in plan.requested_components
            ):
                sections.append(
                    "REPORT SETTINGS COMPLETENESS RULE\n"
                    "The answer is incomplete unless both source-supported groups appear: "
                    "log signing/retention and server backup. Preserve the fields supplied "
                    "under both groups and do not stop after log retention."
                )
            if AnswerComponent.COMPARISON in plan.requested_components:
                sections.append(
                    "COMPARISON EVIDENCE RULE\n"
                    "State only operational differences supported by the context. Do not use "
                    "qualitative claims such as daha güvenli, daha güvenilir, daha iyi, ideal "
                    "or üstün unless the same claim is explicitly present in evidence."
                )
                if plan.primary_entity == "Rapor Ayarları":
                    sections.append(
                        "SOURCE IDENTITY CONFLICT RULE\n"
                        "The exact indexed source path is raporlar/rapor-ayarlari.md. "
                        "Use the path-derived menu identity `Raporlar > Rapor Ayarları`. "
                        "Do not repeat the conflicting embedded heading `Log Arşiv Yapılandırması`; "
                        "describe only supported settings from the exact source path."
                    )
                if plan.primary_entity == "SSL VPN":
                    sections.append(
                        "SOURCE IDENTITY CONFLICT RULE\n"
                        "The exact indexed source path is vpn/ssl-vpn-ayarlari.md. "
                        "Use the path-derived menu identity `VPN > SSL VPN Ayarları`. "
                        "Do not repeat the conflicting embedded Sertifika Yönetimi sentence."
                    )
        sections.append(f"USER MESSAGE\n{user_message}")
        return "\n\n".join(sections)

    def build_correction(
        self,
        user_message: str,
        retrieved_context: Sequence[RetrievedChunk],
        previous_answer: str,
        missing_components: Sequence[str],
    ) -> str:
        """Build one evidence-stable correction prompt for missing components."""
        base = self.build(user_message, retrieved_context)
        return "\n\n".join((
            base,
            "FOCUSED COMPLETENESS CORRECTION",
            f"PREVIOUS ANSWER:\n{previous_answer}",
            f"MISSING_COMPONENTS: {', '.join(missing_components)}",
            "Rewrite the complete answer once. Add only the missing components from "
            "the same supplied evidence. Do not retrieve, infer, or mention another "
            "document family. Preserve every correct supported part of the previous answer.",
        ))

    @staticmethod
    def _component_format_contract(components: Sequence[AnswerComponent]) -> str:
        rules: list[str] = []
        values = set(components)
        if AnswerComponent.DEFINITION in values:
            rules.append("Begin with a direct definition.")
        if values & {AnswerComponent.PURPOSE, AnswerComponent.PRODUCT_USAGE}:
            rules.append("Explain purpose and supported Antikor usage next.")
        if AnswerComponent.NAVIGATION in values:
            rules.append("State the exact menu path first.")
        if AnswerComponent.PROCEDURE in values:
            rules.append("Use a short introduction followed by ordered steps.")
        if AnswerComponent.FIELD_LISTING in values:
            rules.append("Use a compact field list.")
        if AnswerComponent.FIELD_PURPOSE in values:
            rules.append("Pair each relevant field with its supported purpose.")
        if AnswerComponent.COMPARISON in values:
            rules.append("Define both sides briefly and compare them directly.")
        return " ".join(rules)

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
