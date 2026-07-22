"""Balance broad Antikor product evidence across capability categories."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.models import RetrievedChunk
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer


@dataclass(frozen=True, slots=True)
class ClassifiedProductEvidence:
    chunk: RetrievedChunk
    evidence_role: str
    category: str


@dataclass(frozen=True, slots=True)
class ProductEvidenceSelection:
    chunks: tuple[RetrievedChunk, ...]
    selected_categories: tuple[str, ...]
    dominant_category: str | None
    sub_product_ratio: float
    core_overview_present: bool
    missing_capability_categories: tuple[str, ...]
    marketing_chunk_ratio: float


class ProductEvidenceBalancer:
    """Prefer core product breadth over repeated sub-product evidence."""

    @classmethod
    def select(
        cls, chunks: list[RetrievedChunk], limit: int,
    ) -> ProductEvidenceSelection:
        classified = [cls.classify(item) for item in chunks if item.source_type == "product_document"]
        selected: list[ClassifiedProductEvidence] = []
        seen: set[tuple[str, int]] = set()

        def add(candidate: ClassifiedProductEvidence | None) -> None:
            if candidate is None or len(selected) >= limit:
                return
            key = (candidate.chunk.relative_path, candidate.chunk.chunk_index)
            if key not in seen:
                selected.append(candidate)
                seen.add(key)

        core = [item for item in classified if item.evidence_role == "core_product_overview"]
        core.sort(key=cls._rank, reverse=True)
        add(core[0] if core else None)

        capabilities = [item for item in classified if item.evidence_role == "core_capabilities"]
        priority = {
            "firewall_network_security": 0, "ids_ips": 1,
            "vpn_remote_access": 2, "web_security": 3,
            "reporting_logging": 4, "centralized_management": 5,
        }
        capabilities.sort(key=lambda item: (
            priority.get(item.category, 99),
            -item.chunk.similarity_score,
            item.chunk.chunk_index,
        ))
        used_categories: set[str] = set()
        for item in capabilities:
            if item.category in used_categories:
                continue
            add(item)
            used_categories.add(item.category)
            if len(used_categories) >= 4 or len(selected) >= limit:
                break

        deployments = [item for item in classified if item.evidence_role == "deployment_use_cases"]
        deployments.sort(key=cls._rank, reverse=True)
        add(deployments[0] if deployments else None)

        if len(selected) < min(limit, 4):
            supporting = [
                item for item in classified
                if item.evidence_role in {"sub_product", "marketing_supporting"}
            ]
            supporting.sort(key=cls._rank, reverse=True)
            add(supporting[0] if supporting else None)

        if not selected:
            for item in sorted(classified, key=cls._rank, reverse=True)[:limit]:
                add(item)
        categories = tuple(item.category for item in selected)
        available_categories = {
            item.category for item in capabilities if item.category != "general_product"
        }
        selected_capabilities = {
            item.category for item in selected if item.evidence_role == "core_capabilities"
        }
        dominant = max(set(categories), key=categories.count) if categories else None
        sub_count = sum(item.evidence_role == "sub_product" for item in selected)
        return ProductEvidenceSelection(
            chunks=tuple(item.chunk for item in selected),
            selected_categories=categories,
            dominant_category=dominant,
            sub_product_ratio=round(sub_count / max(len(selected), 1), 3),
            core_overview_present=any(
                item.evidence_role == "core_product_overview" for item in selected
            ),
            missing_capability_categories=tuple(sorted(
                available_categories - selected_capabilities
            )),
            marketing_chunk_ratio=round(
                sum(item.evidence_role == "marketing_supporting" for item in selected)
                / max(len(selected), 1), 3,
            ),
        )

    @classmethod
    def classify(cls, chunk: RetrievedChunk) -> ClassifiedProductEvidence:
        document = TurkishLexicalNormalizer.phrase(chunk.document_name)
        searchable = TurkishLexicalNormalizer.phrase(
            f"{chunk.section_title} {chunk.chunk_text}"
        )
        core_document = document.startswith("1 antikor ngfw")
        category = cls._category(searchable)
        if category == "general_product" and not core_document:
            category = cls._category(document)
        if core_document and any(token in searchable for token in (
            "yerl", "mill", "teknolojik bagimsiz", "sertifika",
            "karsilastirmali avantaj", "sonuc ve degerlendirme",
        )):
            role = "marketing_supporting"
        elif core_document and chunk.definition_evidence:
            role = "core_product_overview"
        elif core_document and category != "general_product":
            role = "core_capabilities"
        elif core_document and any(
            token in searchable for token in ("kurum", "kullanim", "senaryo", "mimari", "dagitim")
        ):
            role = "deployment_use_cases"
        elif core_document:
            role = "core_product_overview"
        elif category in {
            "sd_wan", "vpn_remote_access", "ids_ips", "web_security",
            "reporting_logging", "centralized_management",
        }:
            role = "sub_product"
        else:
            role = "marketing_supporting"
        return ClassifiedProductEvidence(chunk, role, category)

    @staticmethod
    def _category(value: str) -> str:
        checks = (
            ("ids_ips", ("ids", "ips", "saldiri tespit")),
            ("vpn_remote_access", ("vpn", "uzak erisim", "ztsa")),
            ("web_security", ("web guvenlik", "icerik filtre", "web filtre", "uygulama kontrol", "ssl tls incele", "ssl incele")),
            ("reporting_logging", ("rapor", "log", "clm")),
            ("sd_wan", ("sdwan", "sd wan")),
            ("centralized_management", ("merkezi yonetim", "cfwm", "ctnm")),
            ("firewall_network_security", ("firewall", "guvenlik duvar", "ag guvenlig")),
        )
        for category, terms in checks:
            if any(term in value for term in terms):
                return category
        return "general_product"

    @staticmethod
    def _rank(item: ClassifiedProductEvidence) -> tuple[int, float, int]:
        return (
            1 if item.chunk.definition_evidence else 0,
            item.chunk.similarity_score,
            -item.chunk.chunk_index,
        )

    @staticmethod
    def missing_answer_requirements(
        answer: str, selection: ProductEvidenceSelection,
    ) -> list[str]:
        """Return broad overview requirements missing from a generated answer."""
        normalized = TurkishLexicalNormalizer.phrase(answer)
        missing: list[str] = []
        if not normalized.startswith("antikor"):
            missing.append("direct_product_definition")
        category_terms = {
            "firewall_network_security": ("firewall", "guvenlik duvar", "ag guvenlig"),
            "ids_ips": ("ids", "ips", "saldiri"),
            "vpn_remote_access": ("vpn", "uzak erisim"),
            "web_security": ("web", "icerik filtre"),
            "reporting_logging": ("rapor", "log"),
            "sd_wan": ("sd wan", "sdwan"),
            "centralized_management": ("merkezi yonetim",),
        }
        available = set(selection.selected_categories) - {"general_product"}
        represented = {
            category for category in available
            if any(term in normalized for term in category_terms.get(category, ()))
        }
        if len(available) >= 2 and len(represented) < 2:
            missing.append("multiple_capability_categories")
        sdwan_mentions = normalized.count("sd wan") + normalized.count("sdwan")
        antikor_mentions = max(normalized.count("antikor"), 1)
        if sdwan_mentions > 2 and sdwan_mentions > antikor_mentions:
            missing.append("sub_product_dominance")
        return missing
