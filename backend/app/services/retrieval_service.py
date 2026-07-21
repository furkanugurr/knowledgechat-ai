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
            intent = IntentClassifier.classify(question)
            concept = (
                self._concept_catalog.resolve(question)
                if intent in {
                    QuestionIntent.CONCEPT_DEFINITION,
                    QuestionIntent.PRODUCT_OVERVIEW,
                }
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
                for path in family_paths[:2]:
                    siblings = await self._retriever.retrieve_document(
                        embedding, path, max(self._candidate_k, 20)
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
            }
            if intent in {
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
        return RetrievalResult(
            chunks=chunks,
            total_results=len(chunks),
            top_k=self._context_max_chunks,
            duration_seconds=duration,
        )

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
