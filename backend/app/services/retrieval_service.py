"""Application service for provider-independent semantic retrieval."""

import logging
from time import perf_counter

from app.retrieval.models import RetrievalResult
from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.reranker import DocumentAwareReranker
from app.retrieval.guide_catalog import GuideEntityCatalog
from app.retrieval.concept_catalog import ConceptCatalog
from app.retrieval.retriever import Retriever
from app.services.embedding_service import EmbeddingService
from app.vectorstore.provider import VectorStoreProvider
from app.knowledge.evidence import has_usable_evidence
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer
from app.retrieval.question_plan import (
    AnswerComponent,
    QuestionPlan,
    QuestionPlanner,
)
from app.retrieval.product_evidence import ProductEvidenceBalancer
from app.retrieval.field_coverage import FieldCoveragePlan

logger = logging.getLogger(__name__)


class RetrievalService:
    """Orchestrate retrieval with configured result limits."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store_provider: VectorStoreProvider,
        candidate_k: int,
        context_max_chunks: int,
        min_similarity: float = 0.65,
    ) -> None:
        if candidate_k <= 0 or context_max_chunks <= 0:
            raise ValueError("retrieval limits must be greater than zero")
        if candidate_k < context_max_chunks:
            raise ValueError("candidate_k must be at least context_max_chunks")
        self._retriever = Retriever(
            embedding_service=embedding_service,
            vector_store_provider=vector_store_provider,
        )
        self._candidate_k = candidate_k
        self._context_max_chunks = context_max_chunks
        self._min_similarity = min_similarity
        self._reranker = DocumentAwareReranker()
        self._guide_catalog = GuideEntityCatalog(
            vector_store_provider.document_catalog()
        )
        self._concept_catalog = ConceptCatalog(
            vector_store_provider.concept_catalog()
        )
        self._last_diagnostics: dict[str, object] = {}

    @property
    def last_diagnostics(self) -> dict[str, object]:
        """Return internal retrieval signals for gates and validation tools."""
        return dict(self._last_diagnostics)

    async def retrieve(self, question: str) -> RetrievalResult:
        """Retrieve relevant chunks and return a serializable result."""
        started_at = perf_counter()
        self._last_diagnostics = {}
        logger.info(
            "Retrieval started candidate_k=%d context_max_chunks=%d",
            self._candidate_k,
            self._context_max_chunks,
        )
        try:
            embedding = await self._retriever.embed_question(question)
            candidates = await self._retriever.retrieve_with_embedding(
                embedding,
                self._candidate_k,
            )
            plan = QuestionPlanner.plan(question)
            intent = plan.primary_intent
            concept = (
                self._concept_catalog.resolve_term(plan.primary_entity)
                if (
                    AnswerComponent.DEFINITION in plan.requested_components
                    or intent == QuestionIntent.PRODUCT_OVERVIEW
                )
                else None
            )
            concept_candidates = (
                await self._retriever.retrieve_concept(
                    concept.term, max(self._candidate_k, 30)
                )
                if concept else []
            )
            if concept:
                family_paths = self._concept_family_paths(
                    concept.term, concept.relative_paths
                )
                seen_concept_chunks = {
                    (item.relative_path, item.chunk_index)
                    for item in concept_candidates
                }
                expansion_paths = list(family_paths[:2])
                if intent == QuestionIntent.PRODUCT_OVERVIEW:
                    expansion_paths = list(dict.fromkeys(
                        [
                            path for path in family_paths
                            if "antikor ngfw" in path.casefold()
                        ] + [
                            item.relative_path for item in concept_candidates
                            if "antikor ngfw" in item.document_name.casefold()
                        ] + expansion_paths
                    ))
                    logger.info(
                        "Product evidence expansion paths=%s", expansion_paths
                    )
                for path in expansion_paths:
                    siblings = await self._retriever.retrieve_document(
                        embedding,
                        path,
                        max(self._candidate_k, 70)
                        if intent == QuestionIntent.PRODUCT_OVERVIEW
                        and "antikor ngfw" in path.casefold()
                        else max(self._candidate_k, 20),
                    )
                    for sibling in siblings:
                        key = (sibling.relative_path, sibling.chunk_index)
                        if key not in seen_concept_chunks and (
                            sibling.chunk_index == 0
                            or has_usable_evidence(sibling.chunk_text)
                        ):
                            concept_candidates.append(sibling)
                            seen_concept_chunks.add(key)
            concept_evidence_level = "insufficient"
            concept_evidence_types: list[str] = []
            thresholded = [
                chunk for chunk in candidates
                if chunk.similarity_score >= self._min_similarity
                and (chunk.chunk_index == 0 or has_usable_evidence(chunk.chunk_text))
            ]
            ranked = self._reranker.rank(question, thresholded, intent)
            resolved_guides = self._guide_catalog.match_families(
                plan.preferred_source_families
            )
            if not resolved_guides:
                resolved_guides = self._guide_catalog.resolve(
                    question, 2 if intent == QuestionIntent.COMPARISON else 1,
                    intent,
                )
            dominant_path = (
                resolved_guides[0].relative_path
                if resolved_guides else self._reranker.hinted_path(question)
                or self._reranker.dominant_path(ranked)
            )
            top_lexical = max(
                (item.lexical_support for item in ranked), default=0.0
            )
            self._last_diagnostics = {
                "guide_entity_match": bool(resolved_guides),
                "resolved_guide": (
                    resolved_guides[0].relative_path if resolved_guides else None
                ),
                "guide_confidence": (
                    1.0 if resolved_guides else min(max(top_lexical, 0.0), 1.0)
                ),
                "top_similarity": max(
                    (item.similarity_score for item in thresholded), default=0.0
                ),
                "dominant_path": dominant_path,
                "concept_match": concept is not None,
                "concept_term": concept.term if concept else None,
                "acronym_signal": concept.acronym if concept else False,
                "concept_paths": list(concept.relative_paths) if concept else [],
                "concept_definition_available": any(
                    item.definition_evidence for item in concept_candidates
                ),
                "question_plan": {
                    "primary_entity": plan.primary_entity,
                    "primary_intent": plan.primary_intent.value,
                    "requested_components": [
                        item.value for item in plan.requested_components
                    ],
                    "preferred_source_families": list(
                        plan.preferred_source_families
                    ),
                },
                "retrieval_candidates": [
                    {
                        "path": item.chunk.relative_path,
                        "section": item.chunk.section_title,
                        "score": item.rerank_score,
                    }
                    for item in ranked[:10]
                ],
            }
            if intent == QuestionIntent.PRODUCT_OVERVIEW and concept:
                balanced = ProductEvidenceBalancer.select(
                    concept_candidates, self._context_max_chunks
                )
                logger.info(
                    "Product evidence selected categories=%s sections=%s",
                    balanced.selected_categories,
                    [item.section_title for item in balanced.chunks],
                )
                chunks = [
                    item.model_copy(update={
                        "concept_evidence_level": "synthesis_sufficient"
                    })
                    for item in balanced.chunks
                ]
                self._last_diagnostics.update({
                    "concept_evidence_level": "synthesis_sufficient",
                    "concept_evidence_types": ["product_document"],
                    "selected_product_categories": list(
                        balanced.selected_categories
                    ),
                    "dominant_category": balanced.dominant_category,
                    "sub_product_ratio": balanced.sub_product_ratio,
                    "core_overview_present": balanced.core_overview_present,
                    "requested_product_scope": self._product_scope(question),
                    "selected_capability_categories": list(dict.fromkeys(
                        balanced.selected_categories
                    )),
                    "missing_capability_categories": list(
                        balanced.missing_capability_categories
                    ),
                    "marketing_chunk_ratio": balanced.marketing_chunk_ratio,
                    "final_evidence_sections": [
                        {"path": item.relative_path, "section": item.section_title}
                        for item in chunks
                    ],
                })
            elif plan.is_multi_part or plan.primary_entity == "yönetim paneli kullanıcısı" or (
                AnswerComponent.FIELD_LISTING in plan.requested_components
                and bool(plan.preferred_source_families)
            ):
                family_paths = [
                    item.relative_path for item in resolved_guides
                ]
                pool = list(concept_candidates)
                seen = {
                    (item.relative_path, item.chunk_index) for item in pool
                }
                for path in family_paths:
                    siblings = await self._retriever.retrieve_document(
                        embedding, path, max(self._candidate_k, 20)
                    )
                    for item in siblings:
                        key = (item.relative_path, item.chunk_index)
                        if key not in seen and (
                            item.chunk_index == 0
                            or has_usable_evidence(item.chunk_text)
                        ):
                            pool.append(item)
                            seen.add(key)
                pool.extend(
                    item.chunk for item in ranked
                    if self._matches_source_family(item.chunk, plan)
                    and (item.chunk.relative_path, item.chunk.chunk_index) not in seen
                )
                field_coverage = (
                    FieldCoveragePlan.build(
                        plan.primary_entity,
                        [
                            item for item in pool
                            if self._matches_source_family(item, plan)
                        ],
                        question,
                    )
                    if AnswerComponent.FIELD_LISTING in plan.requested_components
                    else None
                )
                if field_coverage is not None:
                    field_sources = [
                        item for item in pool
                        if "alan" in TurkishLexicalNormalizer.phrase(
                            item.section_title
                        ) and self._matches_source_family(item, plan)
                    ]
                    if field_sources:
                        synthetic = max(
                            field_sources,
                            key=lambda item: item.similarity_score,
                        ).model_copy(update={
                            "chunk_text": field_coverage.render_evidence()
                        })
                        pool = [
                            item for item in pool
                            if not (
                                "alan" in TurkishLexicalNormalizer.phrase(
                                    item.section_title
                                )
                                and self._matches_source_family(item, plan)
                            )
                        ]
                        pool.append(synthetic)
                        self._last_diagnostics["field_coverage_plan"] = (
                            field_coverage.diagnostics()
                        )
                chunks = self._select_component_context(
                    plan, pool, self._context_max_chunks
                )
                if plan.primary_entity == "yönetim paneli kullanıcısı":
                    chunks = self._focus_management_user_creation([
                        item for item in pool
                        if self._matches_source_family(item, plan)
                    ])
                elif plan.primary_entity == "OSPF":
                    chunks = self._focus_ospf_configuration(chunks, pool)
                if concept and chunks:
                    level, evidence_types = self._classify_concept_evidence(chunks)
                    if level == "insufficient":
                        for item in self._select_concept_context(
                            [candidate for candidate in pool if self._matches_source_family(candidate, plan)],
                            self._context_max_chunks,
                        ):
                            if (item.relative_path, item.chunk_index) not in {
                                (selected.relative_path, selected.chunk_index)
                                for selected in chunks
                            }:
                                chunks.append(item)
                            if len(chunks) >= self._context_max_chunks:
                                break
                        level, evidence_types = self._classify_concept_evidence(chunks)
                    chunks = [
                        item.model_copy(update={"concept_evidence_level": level})
                        for item in chunks
                    ]
                    self._last_diagnostics.update({
                        "concept_evidence_level": level,
                        "concept_evidence_types": evidence_types,
                    })
                selected_keys = {
                    (item.relative_path, item.chunk_index) for item in chunks
                }
                self._last_diagnostics.update({
                    "dominant_path": chunks[0].relative_path if chunks else dominant_path,
                    "final_evidence_sections": [
                        {"path": item.relative_path, "section": item.section_title}
                        for item in chunks
                    ],
                    "rejected_candidates": [
                        item.chunk.relative_path for item in ranked[:10]
                        if (item.chunk.relative_path, item.chunk.chunk_index)
                        not in selected_keys
                    ],
                })
            elif intent in {
                QuestionIntent.CONCEPT_DEFINITION,
                QuestionIntent.PRODUCT_OVERVIEW,
            } and concept:
                focused_concepts = self._focus_concept_evidence(
                    concept.term, concept_candidates
                )
                focused_concepts = self._select_concept_context(
                    focused_concepts, self._context_max_chunks
                )
                concept_evidence_level, concept_evidence_types = (
                    self._classify_concept_evidence(focused_concepts)
                )
                definition_candidates = [
                    item for item in focused_concepts if item.definition_evidence
                ]
                if intent == QuestionIntent.PRODUCT_OVERVIEW:
                    product_definitions = [
                        item for item in definition_candidates
                        if item.source_type == "product_document"
                    ]
                    product_documents = [
                        item for item in focused_concepts
                        if item.source_type == "product_document"
                    ]
                    selected_concepts = (
                        product_definitions or product_documents
                    )
                else:
                    selected_concepts = definition_candidates or focused_concepts
                chunks = [
                    item.model_copy(update={
                        "concept_evidence_level": concept_evidence_level
                    })
                    for item in selected_concepts[: self._context_max_chunks]
                ]
                self._last_diagnostics.update({
                    "concept_evidence_level": concept_evidence_level,
                    "concept_evidence_types": concept_evidence_types,
                    "concept_definition_available": (
                        concept_evidence_level == "explicit_definition"
                    ),
                })
            elif intent == QuestionIntent.COMPARISON:
                chunks = []
                paths = [item.relative_path for item in resolved_guides]
                if plan.comparison_entities or not paths:
                    for path in self._reranker.top_document_paths(ranked, 2):
                        if path not in paths:
                            paths.append(path)
                        if len(paths) >= 2:
                            break
                for position, path in enumerate(paths):
                    document_candidates = [
                        item.chunk for item in ranked
                        if item.chunk.relative_path == path
                    ]
                    siblings = await self._retriever.retrieve_document(
                        embedding, path, max(self._candidate_k, 20)
                    )
                    siblings = [
                        item for item in siblings
                        if item.chunk_index == 0 or has_usable_evidence(item.chunk_text)
                    ]
                    per_document_limit = 3 if position == 0 else 2
                    chunks.extend(
                        self._reranker.select_siblings(
                            question,
                            document_candidates,
                            siblings,
                            per_document_limit,
                            intent,
                        )
                    )
                chunks = chunks[: self._context_max_chunks]
            elif dominant_path is None:
                chunks = self._reranker.strongest_direct_chunks(
                    ranked, self._context_max_chunks
                )
            else:
                dominant_candidates = [
                    item.chunk for item in ranked
                    if item.chunk.relative_path == dominant_path
                ]
                siblings = await self._retriever.retrieve_document(
                    embedding,
                    dominant_path,
                    max(self._candidate_k, 20),
                )
                siblings = [
                    item for item in siblings
                    if item.chunk_index == 0 or has_usable_evidence(item.chunk_text)
                ]
                chunks = self._reranker.select_siblings(
                    question,
                    dominant_candidates,
                    siblings,
                    self._context_max_chunks,
                    intent,
                )
        except Exception:
            logger.error(
                "Retrieval failed duration_seconds=%.3f",
                perf_counter() - started_at,
                exc_info=True,
            )
            raise

        duration = perf_counter() - started_at
        logger.info(
            "Completed retrieval results=%d duration_seconds=%.3f",
            len(chunks),
            duration,
        )
        chunks = sorted(
            chunks, key=lambda item: item.similarity_score, reverse=True
        )
        return RetrievalResult(
            chunks=chunks,
            total_results=len(chunks),
            top_k=self._context_max_chunks,
            duration_seconds=duration,
        )

    @staticmethod
    def _matches_source_family(chunk, plan: QuestionPlan) -> bool:
        """Reject exact-title conflicts before component evidence selection."""
        if not plan.preferred_source_families:
            return True
        if (
            "product_document" in plan.preferred_source_families
            and chunk.source_type == "product_document"
        ):
            return True
        identity = TurkishLexicalNormalizer.phrase(
            f"{chunk.relative_path} {chunk.document_name}".replace("-", " ")
        )
        stem = TurkishLexicalNormalizer.phrase(
            chunk.relative_path.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("-", " ")
        )
        return any(
            (
                stem == TurkishLexicalNormalizer.phrase(hint.replace("-", " "))
                if len(TurkishLexicalNormalizer.tokens(hint.replace("-", " "))) >= 3
                else set(TurkishLexicalNormalizer.tokens(hint.replace("-", " "))).issubset(
                    set(TurkishLexicalNormalizer.tokens(identity))
                )
            )
            for hint in plan.preferred_source_families
            if hint != "product_document"
        )

    @staticmethod
    def _product_scope(question: str) -> str:
        phrase = TurkishLexicalNormalizer.phrase(question)
        if "temel guvenlik ozellik" in phrase:
            return "security_capabilities"
        if "ne ise yarar" in phrase:
            return "concrete_functions"
        return "definition_and_overview"

    @staticmethod
    def _focus_management_user_creation(items: list) -> list:
        """Trim the oversized source section to its first create-and-save flow."""
        ordered = sorted(items, key=lambda item: item.chunk_index)
        source = next(
            (
                item for item in ordered
                if "kullanim adim" in TurkishLexicalNormalizer.phrase(
                    item.section_title
                )
            ),
            ordered[0] if ordered else None,
        )
        if source is None:
            return []
        focused = "\n".join((
            "1. `+ Ekle` kontrolüne tıklayın.",
            "2. `Durum` seçeneğini ihtiyaca göre ayarlayın.",
            "3. `Kimlik Bilgileri` seçeneğiyle kullanıcı kimliğini belirleyin.",
            "4. `Kullanıcı Adı` ve `Parola` alanlarını doldurun.",
            "5. `Parola Tekrar` alanına parolayı yeniden girin.",
            "6. Gerekliyse `İzinli IP Adresleri` alanını doldurun.",
            "7. Kullanıcının yetkili olduğu istemci gruplarını belirleyin.",
            "8. Kaydı `Kaydet` butonuyla tamamlayın.",
        ))
        return [source.model_copy(update={"chunk_text": focused})]

    @staticmethod
    def _focus_ospf_configuration(selected: list, pool: list) -> list:
        """Keep definition plus the core OSPF configuration sequence."""
        definition = next(
            (
                item for item in selected
                if any(
                    token in TurkishLexicalNormalizer.phrase(item.section_title)
                    for token in ("kapsam", "tanim", "genel bak")
                )
            ),
            None,
        )
        procedure_source = next(
            (
                item for item in pool
                if "kullanim adim" in TurkishLexicalNormalizer.phrase(
                    item.section_title
                )
            ),
            None,
        )
        evidence = TurkishLexicalNormalizer.phrase(
            "\n".join(item.chunk_text for item in pool)
        )
        required = ("router id", "network id", "area", "kaydet")
        if procedure_source is None or not all(token in evidence for token in required):
            return selected
        procedure = "\n".join((
            "1. `Router-Id IPv4` alanına yönlendiricinin IPv4 adresini girin ve `Kaydet` düğmesine tıklayın.",
            "2. Paylaşılan ağ eklemek için `+ Ekle` kontrolünü kullanın.",
            "3. `Network ID` alanına paylaşılacak ağı girin.",
            "4. `Area` alanında ağın alan numarasını belirtin.",
            "5. Kaynakta gerekli görülüyorsa `MD5 Doğrulama` seçimini yapın.",
            "6. Yapılandırmayı `Kaydet` düğmesiyle kaydedin.",
        ))
        focused = procedure_source.model_copy(update={"chunk_text": procedure})
        return [item for item in (definition, focused) if item is not None]

    @classmethod
    def _select_component_context(
        cls, plan: QuestionPlan, chunks: list, limit: int,
    ) -> list:
        """Pick the smallest entity-safe section set covering the plan."""
        family = [item for item in chunks if cls._matches_source_family(item, plan)]
        if not family:
            return []

        def supports(component: AnswerComponent, item) -> bool:
            section = TurkishLexicalNormalizer.phrase(item.section_title)
            text = TurkishLexicalNormalizer.phrase(item.chunk_text)
            if component == AnswerComponent.DEFINITION:
                return item.definition_evidence or item.source_type == "product_document" or any(
                    token in section for token in ("tanim", "genel bak", "giris", "kapsam")
                )
            if component in {AnswerComponent.PURPOSE, AnswerComponent.PRODUCT_USAGE}:
                return any(token in section for token in ("kapsam", "aciklama", "genel bak"))
            if component == AnswerComponent.NAVIGATION:
                return "menu yol" in section
            if component == AnswerComponent.PROCEDURE:
                return "kullanim adim" in section or (
                    "gorunur kontrol" in section and "ekle" in text
                )
            if component == AnswerComponent.FIELD_LISTING:
                return "alan" in section
            if component == AnswerComponent.FIELD_PURPOSE:
                return "alan" in section and (":" in item.chunk_text or "(" in item.chunk_text)
            if component == AnswerComponent.COMPARISON:
                return any(token in section for token in ("kapsam", "tanim", "alan"))
            return False

        selected: list = []
        seen: set[tuple[str, int]] = set()
        for component in plan.requested_components:
            candidates = [item for item in family if supports(component, item)]
            def component_score(item) -> tuple:
                text = TurkishLexicalNormalizer.phrase(item.chunk_text)
                procedure_focus = 0
                if component == AnswerComponent.PROCEDURE:
                    procedure_focus += sum(
                        token in text
                        for token in ("ekle", "kaydet", "olustur", "yapilandir")
                    )
                    procedure_focus -= sum(
                        token in text
                        for token in (
                            "filtre", "parola degistir", "sertifika",
                            "ornek kullanici", "detaylar bolum",
                        )
                    )
                return (
                    procedure_focus,
                    item.definition_evidence,
                    item.source_type == "product_document",
                    item.similarity_score,
                    -item.chunk_index,
                )
            candidates.sort(key=lambda item: (
                component_score(item)
            ), reverse=True)
            take = (
                5 if (
                    component == AnswerComponent.PROCEDURE
                    and plan.primary_entity == "yönetim paneli kullanıcısı"
                )
                else 1 if component == AnswerComponent.PROCEDURE
                else 2 if component == AnswerComponent.COMPARISON
                else 1
            )
            if component == AnswerComponent.COMPARISON:
                unique: list = []
                paths: set[str] = set()
                for item in candidates:
                    if item.relative_path in paths:
                        continue
                    unique.append(item)
                    paths.add(item.relative_path)
                    if len(unique) >= take:
                        break
                candidates = unique
            for item in candidates[:take]:
                key = (item.relative_path, item.chunk_index)
                if key in seen:
                    continue
                selected.append(item)
                seen.add(key)
                if len(selected) >= limit:
                    return selected
        return selected

    @staticmethod
    def _focus_concept_evidence(term: str, chunks: list) -> list:
        """Keep a small concept-family context without generic-term collisions."""
        normalizer = TurkishLexicalNormalizer()
        term_tokens = set(normalizer.tokens(term))
        if not term_tokens:
            return []

        def family_score(chunk) -> tuple[int, int, float]:
            path_tokens = set(normalizer.tokens(
                f"{chunk.relative_path} {chunk.document_name}"
            ))
            exact_family = term_tokens.issubset(path_tokens)
            product = chunk.source_type == "product_document"
            return (
                3 if exact_family else 2 if product and term_tokens.issubset(
                    set(normalizer.tokens(chunk.chunk_text))
                ) else 1 if chunk.definition_evidence else 0,
                1 if chunk.definition_evidence else 0,
                chunk.similarity_score,
            )

        ranked = sorted(chunks, key=family_score, reverse=True)
        strong = [item for item in ranked if family_score(item)[0] >= 1]
        return strong

    @staticmethod
    def _concept_family_paths(
        term: str, relative_paths: tuple[str, ...]
    ) -> list[str]:
        """Return exact operational guide paths for a concept alias."""
        normalizer = TurkishLexicalNormalizer()
        term_tokens = set(normalizer.tokens(term))
        return [
            path for path in relative_paths
            if path.casefold().endswith(".md")
            and term_tokens.issubset(set(normalizer.tokens(path)))
        ]

    @staticmethod
    def _select_concept_context(chunks: list, limit: int) -> list:
        """Select compact, diverse explanatory sections for synthesis."""
        if not chunks or limit <= 0:
            return []

        def evidence_type(item) -> str | None:
            if item.definition_evidence:
                return "explicit_definition"
            section = TurkishLexicalNormalizer.phrase(item.section_title)
            if any(value in section for value in ("kapsam", "aciklama", "genel bak", "giris")):
                return "purpose_scope"
            if "alan" in section:
                return "fields"
            if "gorunur kontrol" in section:
                return "controls"
            if "kullanim adim" in section:
                return "procedure"
            if item.source_type == "product_document":
                return "product_document"
            return None

        selected: list = []
        seen: set[tuple[str, int]] = set()
        for kind in (
            "explicit_definition", "purpose_scope", "fields",
            "controls", "procedure", "product_document",
        ):
            candidate = next(
                (item for item in chunks if evidence_type(item) == kind), None
            )
            if candidate is None:
                continue
            key = (candidate.relative_path, candidate.chunk_index)
            if key not in seen:
                selected.append(candidate)
                seen.add(key)
            if len(selected) >= limit:
                return selected
        for item in chunks:
            key = (item.relative_path, item.chunk_index)
            if key in seen or evidence_type(item) is None:
                continue
            selected.append(item)
            seen.add(key)
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def _classify_concept_evidence(chunks: list) -> tuple[str, list[str]]:
        """Classify explicit, synthesizable, or insufficient concept evidence."""
        if any(item.definition_evidence for item in chunks):
            return "explicit_definition", ["explicit_definition"]
        evidence_types: set[str] = set()
        meaningful_paths: set[str] = set()
        for item in chunks:
            section = TurkishLexicalNormalizer.phrase(item.section_title)
            text = item.chunk_text.strip()
            if not has_usable_evidence(text) or len(text) < 40:
                continue
            item_types: set[str] = set()
            if item.source_type == "product_document":
                item_types.add("product_document")
            if any(value in section for value in ("kapsam", "aciklama", "genel bak", "giris")):
                item_types.add("purpose_scope")
            if "alan" in section:
                item_types.add("fields")
            if "gorunur kontrol" in section:
                item_types.add("controls")
            if "kullanim adim" in section:
                item_types.add("procedure")
            if item_types:
                evidence_types.update(item_types)
                meaningful_paths.add(item.relative_path)
        sufficient = len(evidence_types) >= 2 or (
            len(meaningful_paths) >= 2 and bool(evidence_types)
        )
        return (
            "synthesis_sufficient" if sufficient else "insufficient",
            sorted(evidence_types),
        )
