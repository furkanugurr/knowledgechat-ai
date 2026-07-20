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
                QuestionIntent.GENERAL_INFORMATION: (),
            }[intent]
            evidence_available = any(
                any(
                    expected.casefold() in chunk.section_title.casefold()
                    for expected in expected_sections
                )
                for chunk in retrieved_context
            ) if expected_sections else bool(retrieved_context)
            answer_shapes = {
                QuestionIntent.NAVIGATION: "Return one clear supported menu path. Do not combine unrelated headings or descriptive prose.",
                QuestionIntent.PROCEDURE: "Return ordered supported steps in source order.",
                QuestionIntent.FIRST_ACTION: "Answer the first supported button or action directly; add at most one short following step.",
                QuestionIntent.FIELD_LISTING: "Return a clean list of supported fields without a limitation preface.",
                QuestionIntent.FIELD_PURPOSE: "Explain only the requested field's supported purpose.",
                QuestionIntent.CONTROL_PURPOSE: "Explain only the requested control's supported purpose.",
                QuestionIntent.COMPARISON: "Explain both supported concepts separately, then state their difference.",
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
                "For navigation, when NAVIGATION_PATH_HINT is not unavailable, return that exact path and nothing else. "
                "For procedure or first_action, when CREATION_CONTROL_HINT is not unavailable, begin with that exact control and continue only with supported steps. "
                "For navigation, reject descriptive menu text that does not form a path for the exact guide entity; "
                "the exact guide title and matching source URL path segments may be used as navigation evidence."
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
            "Use only context that directly answers its entity and action. "
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
                    f" Output exactly this single path and nothing else: {navigation_hint}"
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
        """Derive a conservative path hint from the selected guide identity."""
        if not retrieved_context:
            return "unavailable"
        first = retrieved_context[0]
        path = first.relative_path.casefold()
        title = next(
            (
                chunk.section_title
                for chunk in retrieved_context
                if chunk.chunk_index == 0
            ),
            Path(first.document_name).stem.replace("-", " ").title(),
        )
        if "/vpn/" in path:
            return f"VPN Yönetimi > {title}"
        if "/kullanici_yonetimi/" in path:
            return f"Kullanıcı Yönetimi > {title}"
        if "/guvenlik_kurallari/" in path:
            return title
        if "/nat/" in path:
            return f"NAT Yapılandırması > {title}"
        return title

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
