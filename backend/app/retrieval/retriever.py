"""Semantic retrieval component independent from chat generation."""

import asyncio
import logging
from typing import Protocol

from pydantic import ValidationError

from app.embedding.models import EmbeddingVector
from app.embedding.provider import EmbeddingProviderError
from app.retrieval.models import RetrievedChunk
from app.vectorstore.models import VectorSearchRecord
from app.vectorstore.provider import (
    EmptyVectorStoreError,
    InvalidVectorSearchResultError,
    VectorSearchError,
    VectorStoreProvider,
)

logger = logging.getLogger(__name__)


class QuestionEmbeddingService(Protocol):
    """Minimal embedding capability required by retrieval."""

    async def embed_text(self, text: str) -> EmbeddingVector:
        """Generate one vector for a question."""


class RetrievalError(Exception):
    """Base exception for semantic retrieval failures."""


class EmptyCollectionError(RetrievalError):
    """Raised when semantic retrieval has no indexed vectors."""


class RetrievalEmbeddingError(RetrievalError):
    """Raised when a question embedding cannot be generated."""


class RetrievalSearchError(RetrievalError):
    """Raised when the vector store search fails."""


class InvalidRetrievalResultError(RetrievalError):
    """Raised when vector search results cannot be validated."""


class Retriever:
    """Generate a question embedding and retrieve similar chunks."""

    def __init__(
        self,
        embedding_service: QuestionEmbeddingService,
        vector_store_provider: VectorStoreProvider,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store_provider = vector_store_provider

    async def retrieve(
        self,
        question: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Return the highest-similarity knowledge chunks."""
        if not question.strip():
            raise ValueError("question cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        question_embedding = await self.embed_question(question)
        return await self.retrieve_with_embedding(question_embedding, top_k)

    async def embed_question(self, question: str) -> EmbeddingVector:
        """Generate and validate the embedding used by retrieval stages."""
        if not question.strip():
            raise ValueError("question cannot be empty")
        logger.info("Generating question embedding")
        try:
            return await self._embedding_service.embed_text(
                question
            )
        except EmbeddingProviderError as exc:
            raise RetrievalEmbeddingError(
                "Unable to generate the question embedding."
            ) from exc

    async def retrieve_with_embedding(
        self,
        question_embedding: EmbeddingVector,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Search using an existing embedding so expansion can reuse it."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        logger.info("Searching vector database top_k=%d", top_k)
        try:
            records = await asyncio.to_thread(
                self._vector_store_provider.search,
                question_embedding,
                top_k,
            )
        except EmptyVectorStoreError as exc:
            raise EmptyCollectionError(
                "The vector collection is empty."
            ) from exc
        except InvalidVectorSearchResultError as exc:
            raise InvalidRetrievalResultError(
                "The vector store returned invalid search results."
            ) from exc
        except VectorSearchError as exc:
            raise RetrievalSearchError(
                "Unable to search the vector store."
            ) from exc

        try:
            chunks = [
                self._to_retrieved_chunk(record)
                for record in records
            ]
        except (KeyError, TypeError, ValidationError) as exc:
            raise InvalidRetrievalResultError(
                "The vector store returned invalid chunk metadata."
            ) from exc

        chunks.sort(
            key=lambda chunk: chunk.similarity_score,
            reverse=True,
        )
        logger.info("Retrieved chunks count=%d", len(chunks))
        return chunks

    async def retrieve_document(
        self,
        question_embedding: EmbeddingVector,
        relative_path: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Retrieve similarity-ranked sibling chunks from one document."""
        try:
            records = await asyncio.to_thread(
                self._vector_store_provider.search_document,
                question_embedding,
                relative_path,
                top_k,
            )
        except VectorSearchError as exc:
            raise RetrievalSearchError(
                "Unable to expand the selected source document."
            ) from exc
        try:
            return [self._to_retrieved_chunk(record) for record in records]
        except (KeyError, TypeError, ValidationError) as exc:
            raise InvalidRetrievalResultError(
                "The vector store returned invalid document chunks."
            ) from exc

    @staticmethod
    def _to_retrieved_chunk(
        record: VectorSearchRecord,
    ) -> RetrievedChunk:
        """Convert a provider search record into a retrieval model."""
        metadata = record.metadata
        return RetrievedChunk(
            chunk_text=record.document,
            similarity_score=record.similarity_score,
            document_name=metadata["document_name"],
            relative_path=metadata["relative_path"],
            section_title=metadata["section_title"],
            chunk_index=metadata["chunk_index"],
            language=metadata["language"],
        )
