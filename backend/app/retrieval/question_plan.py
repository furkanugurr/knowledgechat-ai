"""Deterministic decomposition of compound Antikor questions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


class AnswerComponent(StrEnum):
    """Evidence shapes that may be requested in one user question."""

    DEFINITION = "definition"
    PURPOSE = "purpose"
    PRODUCT_USAGE = "product_usage"
    NAVIGATION = "navigation"
    PROCEDURE = "procedure"
    FIELD_LISTING = "field_listing"
    FIELD_PURPOSE = "field_purpose"
    COMPARISON = "comparison"


@dataclass(frozen=True, slots=True)
class QuestionPlan:
    """One entity-constrained plan shared by retrieval and generation."""

    primary_entity: str
    primary_intent: QuestionIntent
    requested_components: tuple[AnswerComponent, ...]
    preferred_source_families: tuple[str, ...]
    comparison_entities: tuple[str, ...] = ()

    @property
    def is_multi_part(self) -> bool:
        return len(self.requested_components) > 1


class QuestionPlanner:
    """Build conservative plans from Turkish question wording."""

    _ENTITY_PATTERNS = (
        ("yönetim paneli kullanıcısı", ("yonetim panel kullan",)),
        ("Web Sunucu Güvenliği", ("web sunuc guvenlig",)),
        ("Rapor Ayarları", ("rapor ayar",)),
        ("SSL VPN", ("ssl vpn",)),
        ("Dinamik NAT", ("dinamik nat",)),
        ("Statik NAT", ("statik nat",)),
        ("Kaynak Adres ve Hedef Adres", ("kaynak adres", "hedef adres")),
        ("SD-WAN", ("sd wan",)),
        ("VLAN", ("vlan",)),
        ("OSPF", ("ospf",)),
        ("IPS", ("ips",)),
        ("Antikor", ("antikor",)),
    )

    _FAMILY_HINTS = {
        "Antikor": ("product_document",),
        "IPS": ("product_document", "ips"),
        "VLAN": ("vlan",),
        "Dinamik NAT": ("dinamik-nat",),
        "Statik NAT": ("statik-nat",),
        "SSL VPN": ("ssl-vpn-ayarlari",),
        "yönetim paneli kullanıcısı": ("yonetim-paneli-kullanicilari",),
        "Web Sunucu Güvenliği": ("web-sunucu-guvenligi",),
        "Rapor Ayarları": ("rapor-ayarlari",),
        "OSPF": ("ospf",),
        "Kaynak Adres ve Hedef Adres": ("guvenlik-kurallari",),
        "SD-WAN": ("sdwan",),
    }

    @classmethod
    def plan(cls, question: str) -> QuestionPlan:
        phrase = TurkishLexicalNormalizer.phrase(question)
        entity = cls._entity(phrase, question)
        components: list[AnswerComponent] = []

        normalized_entity = TurkishLexicalNormalizer.phrase(entity)
        if (
            f"{normalized_entity} nedir" in phrase
            or cls._has(phrase, "ne demek", "acilimi")
        ):
            components.append(AnswerComponent.DEFINITION)
        if cls._has(phrase, "ne ise yarar", "hangi amac", "amacla kullan", "amaclari"):
            components.append(AnswerComponent.PURPOSE)
        if entity == "Antikor" and cls._has(
            phrase, "temel guvenlik ozellik", "ozellikleri nelerdir", "ana yetenek"
        ):
            components.append(AnswerComponent.PURPOSE)
        if cls._has(phrase, "antikor da nasil kullan") and (
            AnswerComponent.DEFINITION in components
            or AnswerComponent.PURPOSE in components
        ):
            components.append(AnswerComponent.PRODUCT_USAGE)
        if cls._has(phrase, "hangi menu", "menu alt", "nasil gid", "nereden ulas"):
            components.append(AnswerComponent.NAVIGATION)
        if cls._has(
            phrase, "nasil olustur", "nasil yapilandir", "nasil yapilir",
            "adimlari sirayla", "adim adim",
        ):
            components.append(AnswerComponent.PROCEDURE)
        if cls._has(
            phrase, "hangi alan", "alanlar bulun", "alanlari", "hangi ayarlar",
            "koruma secenekleri", "saldiri koruma secenekleri",
        ):
            components.append(AnswerComponent.FIELD_LISTING)
            if cls._has(phrase, "ne ise yarar", "amac"):
                components.append(AnswerComponent.FIELD_PURPOSE)
        if cls._has(phrase, "arasindaki fark", "farki nedir", "farki ne"):
            components.append(AnswerComponent.COMPARISON)

        components = list(dict.fromkeys(components))
        inferred_intent: QuestionIntent | None = None
        if not components:
            inferred_intent = IntentClassifier.classify(question)
            components = [cls._component_for_intent(inferred_intent)]
        intent = inferred_intent or cls._primary_intent(entity, components, question)
        comparison_entities = (
            ("Dinamik NAT", "Statik NAT")
            if entity == "Dinamik NAT" and AnswerComponent.COMPARISON in components
            else ()
        )
        families = list(cls._FAMILY_HINTS.get(entity, ()))
        if comparison_entities:
            families = ["dinamik-nat", "statik-nat"]
        return QuestionPlan(
            primary_entity=entity,
            primary_intent=intent,
            requested_components=tuple(components),
            preferred_source_families=tuple(families),
            comparison_entities=comparison_entities,
        )

    @classmethod
    def _entity(cls, phrase: str, question: str) -> str:
        for display, patterns in cls._ENTITY_PATTERNS:
            if all(pattern in phrase for pattern in patterns):
                return display
        term = IntentClassifier.definition_term(question)
        return term.upper() if term and len(term) <= 6 else (term or question.strip())

    @staticmethod
    def _primary_intent(
        entity: str, components: list[AnswerComponent], question: str,
    ) -> QuestionIntent:
        values = set(components)
        if AnswerComponent.COMPARISON in values:
            return QuestionIntent.COMPARISON
        if AnswerComponent.PROCEDURE in values:
            return QuestionIntent.PROCEDURE
        if AnswerComponent.NAVIGATION in values:
            return QuestionIntent.NAVIGATION
        if AnswerComponent.FIELD_LISTING in values:
            return QuestionIntent.FIELD_LISTING
        if AnswerComponent.DEFINITION in values:
            return (
                QuestionIntent.PRODUCT_OVERVIEW
                if entity == "Antikor" else QuestionIntent.CONCEPT_DEFINITION
            )
        if entity == "Antikor" and AnswerComponent.PURPOSE in values:
            return QuestionIntent.PRODUCT_OVERVIEW
        return IntentClassifier.classify(question)

    @staticmethod
    def _component_for_intent(intent: QuestionIntent) -> AnswerComponent:
        return {
            QuestionIntent.NAVIGATION: AnswerComponent.NAVIGATION,
            QuestionIntent.PROCEDURE: AnswerComponent.PROCEDURE,
            QuestionIntent.FIRST_ACTION: AnswerComponent.PROCEDURE,
            QuestionIntent.FIELD_LISTING: AnswerComponent.FIELD_LISTING,
            QuestionIntent.FIELD_PURPOSE: AnswerComponent.FIELD_PURPOSE,
            QuestionIntent.CONTROL_PURPOSE: AnswerComponent.PURPOSE,
            QuestionIntent.COMPARISON: AnswerComponent.COMPARISON,
            QuestionIntent.CONCEPT_DEFINITION: AnswerComponent.DEFINITION,
            QuestionIntent.PRODUCT_OVERVIEW: AnswerComponent.DEFINITION,
        }.get(intent, AnswerComponent.PURPOSE)

    @staticmethod
    def _has(value: str, *patterns: str) -> bool:
        return any(TurkishLexicalNormalizer.phrase(item) in value for item in patterns)


class AnswerCompletenessValidator:
    """Conservatively detect which planned components an answer contains."""

    @classmethod
    def answered_components(
        cls, plan: QuestionPlan, answer: str,
    ) -> tuple[AnswerComponent, ...]:
        text = TurkishLexicalNormalizer.phrase(answer)
        lines = [line.strip() for line in answer.splitlines() if line.strip()]
        answered: list[AnswerComponent] = []
        for component in plan.requested_components:
            present = False
            if component == AnswerComponent.DEFINITION:
                present = TurkishLexicalNormalizer.phrase(plan.primary_entity) in text and len(text) >= 40
            elif component in {AnswerComponent.PURPOSE, AnswerComponent.PRODUCT_USAGE}:
                present = len(text) >= 80 and any(
                    token in text for token in ("amac", "kullan", "saglar", "korur", "yonet")
                )
            elif component == AnswerComponent.NAVIGATION:
                expected_path = {
                    "SSL VPN": "VPN > SSL VPN Ayarları",
                    "Rapor Ayarları": "Raporlar > Rapor Ayarları",
                }.get(plan.primary_entity)
                present = (
                    TurkishLexicalNormalizer.phrase(expected_path) in text
                    if expected_path else
                    ">" in answer or any(
                        "menu" in TurkishLexicalNormalizer.phrase(line)
                        for line in lines
                    )
                )
            elif component == AnswerComponent.PROCEDURE:
                present = sum(bool(re.match(r"^\s*\d+[.)]\s+", line)) for line in lines) >= 2
                if present and plan.primary_entity == "yönetim paneli kullanıcısı":
                    present = all(
                        token in text
                        for token in ("kullanici ad", "parola", "kaydet")
                    )
                if present and plan.primary_entity == "OSPF":
                    present = all(
                        token in text for token in ("router id", "network id", "area", "kaydet")
                    ) and not any(
                        token in text for token in ("neighbour detail", "ospf route", "komsu durum")
                    )
            elif component == AnswerComponent.FIELD_LISTING:
                present = sum(line.startswith(("- ", "* ")) for line in lines) >= 2
                if present and "rapor ayar" in TurkishLexicalNormalizer.phrase(
                    plan.primary_entity
                ):
                    present = any(token in text for token in ("mza", "algoritma")) and any(
                        token in text for token in ("yedek", "sunuc")
                    )
                if present and "web sunuc" in TurkishLexicalNormalizer.phrase(
                    plan.primary_entity
                ) and AnswerComponent.FIELD_PURPOSE in plan.requested_components:
                    present = all(token in text for token in (
                        "govde", "uygulama saldiri", "protokol", "itibar", "veri sizinti",
                    ))
            elif component == AnswerComponent.FIELD_PURPOSE:
                present = sum(
                    line.startswith(("- ", "* ")) and (":" in line or " - " in line)
                    for line in lines
                ) >= 2
            elif component == AnswerComponent.COMPARISON:
                entities = plan.comparison_entities or (plan.primary_entity,)
                present = all(
                    TurkishLexicalNormalizer.phrase(entity) in text
                    for entity in entities
                ) and any(token in text for token in ("fark", "oysa", "iken"))
            if present:
                answered.append(component)
        return tuple(answered)
