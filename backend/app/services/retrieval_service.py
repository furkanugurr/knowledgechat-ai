"""Application service for provider-independent semantic retrieval."""

import logging
from time import perf_counter

from app.retrieval.models import RetrievalResult
from app.retrieval.intent import IntentClassifier, QuestionIntent
from app.retrieval.reranker import DocumentAwareReranker
from app.retrieval.retriever import Retriever
from app.services.embedding_service import EmbeddingService
from app.vectorstore.provider import VectorStoreProvider

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

    async def retrieve(self, question: str) -> RetrievalResult:
        """Retrieve relevant chunks and return a serializable result."""
        started_at = perf_counter()
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
            thresholded = [
                chunk for chunk in candidates
                if chunk.similarity_score >= self._min_similarity
            ]
            intent = IntentClassifier.classify(question)
            ranked = self._reranker.rank(question, thresholded, intent)
            dominant_path = self._reranker.dominant_path(ranked)
            if intent == QuestionIntent.COMPARISON:
                chunks = []
                paths = self._reranker.top_document_paths(ranked, 2)
                for position, path in enumerate(paths):
                    document_candidates = [
                        item.chunk for item in ranked
                        if item.chunk.relative_path == path
                    ]
                    siblings = await self._retriever.retrieve_document(
                        embedding, path, max(self._candidate_k, 20)
                    )
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
