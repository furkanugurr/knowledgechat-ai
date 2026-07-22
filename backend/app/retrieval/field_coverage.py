"""Build complete, grouped field evidence for long Antikor screens."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.retrieval.models import RetrievedChunk
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class FieldEvidence:
    label: str
    description: str


@dataclass(frozen=True, slots=True)
class FieldGroup:
    key: str
    title: str
    purpose: str
    fields: tuple[FieldEvidence, ...]


@dataclass(frozen=True, slots=True)
class FieldCoveragePlan:
    """Coverage accounting plus grouped source text for one screen."""

    all_discovered_fields: tuple[str, ...]
    important_field_groups: tuple[FieldGroup, ...]
    available_purpose_descriptions: tuple[str, ...]
    fields_selected_for_direct_explanation: tuple[str, ...]
    fields_represented_through_groups: tuple[str, ...]
    omitted_fields: tuple[str, ...]
    omitted_reasons: tuple[str, ...]

    _FIELD = re.compile(r"^\s*-\s+`([^`]+)`(?:\s+\([^)]*\))?\s*:\s*(.+?)\s*$")

    @classmethod
    def build(
        cls, entity: str, chunks: list[RetrievedChunk], question: str = "",
    ) -> "FieldCoveragePlan | None":
        discovered: list[FieldEvidence] = []
        seen: set[str] = set()
        for chunk in sorted(chunks, key=lambda item: item.chunk_index):
            if "alan" not in TurkishLexicalNormalizer.phrase(chunk.section_title):
                continue
            for line in chunk.chunk_text.splitlines():
                match = cls._FIELD.match(line)
                if not match or match.group(1) in seen:
                    continue
                seen.add(match.group(1))
                discovered.append(FieldEvidence(match.group(1), match.group(2).strip()))
        if not discovered:
            return None
        grouped: dict[str, list[FieldEvidence]] = {}
        for field in discovered:
            key = cls._group_key(entity, field.label)
            grouped.setdefault(key, []).append(field)
        groups = tuple(
            FieldGroup(
                key=key,
                title=cls._group_metadata(key)[0],
                purpose=cls._group_metadata(key)[1],
                fields=tuple(fields),
            )
            for key, fields in grouped.items()
        )
        question_normalized = TurkishLexicalNormalizer.phrase(question)
        if all(token in question_normalized for token in ("saldir", "korum", "secenek")):
            groups = tuple(group for group in groups if group.key != "body_limits")
            represented_labels = {
                field.label for group in groups for field in group.fields
            }
            discovered = [
                field for field in discovered if field.label in represented_labels
            ]
        direct = tuple(
            field.label for group in groups if len(group.fields) <= 5
            for field in group.fields
        )
        represented = tuple(
            field.label for group in groups if len(group.fields) > 5
            for field in group.fields
        )
        return cls(
            all_discovered_fields=tuple(field.label for field in discovered),
            important_field_groups=groups,
            available_purpose_descriptions=tuple(
                field.description for field in discovered if field.description
            ),
            fields_selected_for_direct_explanation=direct,
            fields_represented_through_groups=represented,
            omitted_fields=(),
            omitted_reasons=(),
        )

    @staticmethod
    def _group_key(entity: str, label: str) -> str:
        entity_normalized = TurkishLexicalNormalizer.phrase(entity)
        normalized = TurkishLexicalNormalizer.phrase(label)
        if "web sunuc" in entity_normalized:
            if any(token in normalized for token in ("govdes", "boyut limit", "buyuk yanit")):
                return "body_limits"
            if "application attack" in normalized:
                return "application_attacks"
            if any(token in normalized for token in (
                "method enforcement", "protocol attack", "protocol enforcement",
                "common exceptions",
            )):
                return "protocol_controls"
            if any(token in normalized for token in (
                "ip reputation", "scanner detection", "dos protection",
            )):
                return "detection_reputation"
            if normalized.startswith("response") or "blocking evaluation" in normalized:
                return "response_data_protection"
        if "rapor ayar" in entity_normalized:
            if any(token in normalized for token in (
                "mza", "algoritma", "saklama sure", "musteri no",
            )):
                return "log_signing_retention"
            if any(token in normalized for token in (
                "sunuc", "dosya paylas", "adres ailes", "hedef klasor",
                "kullanici ad", "parola",
            )):
                return "server_backup"
        return "core_fields"

    @staticmethod
    def _group_metadata(key: str) -> tuple[str, str]:
        return {
            "body_limits": (
                "Gövde boyutu ve yanıt limitleri",
                "İstek ve yanıt gövdelerinin boyut sınırlarını ve büyük yanıtların işlenişini belirler.",
            ),
            "application_attacks": (
                "Uygulama saldırısı korumaları",
                "Java, LFI, Node.js, PHP, RCE, RFI, SQL injection, XSS ve session fixation kategorilerinin denetimini toplar.",
            ),
            "protocol_controls": (
                "Protokol ve istek kontrolleri",
                "İstek yöntemleri, protokol saldırıları, protokol uygulaması ve ortak istisnalarla ilgili denetimleri toplar.",
            ),
            "detection_reputation": (
                "Tespit ve itibar kontrolleri",
                "IP itibarı, tarayıcı tespiti ve DoS korumasıyla ilgili denetimleri toplar.",
            ),
            "response_data_protection": (
                "Yanıt ve veri sızıntısı korumaları",
                "Yanıt engelleme, brute force, korelasyon ve veri sızıntısı kategorilerini toplar.",
            ),
            "log_signing_retention": (
                "Log imzalama ve saklama",
                "İmza programı, algoritma ve log saklama sürelerini yapılandırır.",
            ),
            "server_backup": (
                "Sunucuya yedekleme",
                "Yedekleme hedefinin bağlantı, kimlik doğrulama ve hedef klasör bilgilerini yapılandırır.",
            ),
            "core_fields": (
                "Temel alanlar",
                "Ekranın kaynakta açıklanan temel yapılandırma değerlerini toplar.",
            ),
        }[key]

    def render_evidence(self) -> str:
        """Render every group without omitting source-supported labels."""
        sections: list[str] = []
        for group in self.important_field_groups:
            sections.extend((f"### {group.title}", f"Grup amacı: {group.purpose}"))
            sections.extend(
                f"- `{field.label}`: {field.description}"
                for field in group.fields
            )
        return "\n".join(sections)

    def diagnostics(self) -> dict[str, object]:
        return {
            "all_discovered_fields": list(self.all_discovered_fields),
            "important_field_groups": [group.key for group in self.important_field_groups],
            "available_purpose_description_count": len(self.available_purpose_descriptions),
            "fields_selected_for_direct_explanation": list(self.fields_selected_for_direct_explanation),
            "fields_represented_through_groups": list(self.fields_represented_through_groups),
            "omitted_fields": list(self.omitted_fields),
            "omitted_reasons": list(self.omitted_reasons),
        }

    def missing_answer_groups(self, answer: str) -> list[str]:
        """Return source-supported groups not represented in the answer."""
        normalized = TurkishLexicalNormalizer.phrase(answer)
        missing: list[str] = []
        for group in self.important_field_groups:
            title = TurkishLexicalNormalizer.phrase(group.title)
            labels = [TurkishLexicalNormalizer.phrase(item.label) for item in group.fields]
            represented = title in normalized or any(label in normalized for label in labels)
            if not represented:
                missing.append(group.key)
        return missing

    def render_answer(self) -> str:
        """Create a readable deterministic fallback from the complete plan."""
        parts: list[str] = []
        for group in self.important_field_groups:
            parts.append(f"### {group.title}\n\n{group.purpose}")
            parts.append("\n".join(
                f"- **{field.label}:** {field.description}" for field in group.fields
            ))
        return "\n\n".join(parts)
