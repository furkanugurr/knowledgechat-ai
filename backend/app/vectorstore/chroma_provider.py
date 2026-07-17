"""Persistent ChromaDB implementation of vector storage."""

import hashlib
import logging
import math
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import chromadb

from app.embedding.models import EmbeddedChunk, EmbeddingVector
from app.vectorstore.models import (
    VectorCollectionInfo,
    VectorSearchRecord,
)
from app.vectorstore.provider import (
    CollectionCreationError,
    EmptyVectorStoreError,
    InvalidVectorSearchResultError,
    VectorDeleteError,
    VectorSearchError,
    VectorStoreProvider,
    VectorStoreUnavailableError,
    VectorUpsertError,
)

logger = logging.getLogger(__name__)

ClientFactory = Callable[..., Any]


class ChromaVectorStoreProvider(VectorStoreProvider):
    """Persist externally generated embeddings in local ChromaDB."""

    def __init__(
        self,
        persistence_path: Path,
        collection_name: str,
        client_factory: ClientFactory = chromadb.PersistentClient,
    ) -> None:
        self._persistence_path = persistence_path.resolve()
        self._collection_name = collection_name
        self._client_factory = client_factory
        self._client: Any | None = None
        self._collection: Any | None = None

    def create_collection(self) -> VectorCollectionInfo:
        """Create or load the configured persistent collection."""
        client = self._connect()
        if self._collection is None:
            logger.info(
                "Creating or loading vector collection name=%s",
                self._collection_name,
            )
            try:
                self._collection = client.get_or_create_collection(
                    name=self._collection_name,
                    embedding_function=None,
                    configuration={"hnsw": {"space": "cosine"}},
                )
                self._validate_cosine_configuration(self._collection)
            except Exception as exc:
                self._collection = None
                raise CollectionCreationError(
                    f"Unable to create vector collection: "
                    f"{self._collection_name}"
                ) from exc
            logger.info(
                "Vector collection ready name=%s",
                self._collection_name,
            )
        return self.collection_info()

    def upsert_embeddings(
        self,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        """Upsert embedded chunks and remove stale IDs for changed files."""
        if not embedded_chunks:
            return 0

        collection = self._require_collection()
        ids = [self._record_id(item) for item in embedded_chunks]
        try:
            self._delete_stale_records(
                collection,
                embedded_chunks,
                set(ids),
            )
            logger.info(
                "Upserting vectors collection=%s count=%d",
                self._collection_name,
                len(embedded_chunks),
            )
            collection.upsert(
                ids=ids,
                embeddings=[
                    item.embedding.values
                    for item in embedded_chunks
                ],
                metadatas=[
                    self._metadata(item)
                    for item in embedded_chunks
                ],
                documents=[
                    item.chunk.content
                    for item in embedded_chunks
                ],
            )
        except Exception as exc:
            raise VectorUpsertError(
                f"Unable to upsert vectors into collection: "
                f"{self._collection_name}"
            ) from exc
        return len(embedded_chunks)

    def delete_embeddings(
        self,
        relative_paths: Sequence[str],
    ) -> int:
        """Delete all vectors belonging to removed knowledge documents."""
        if not relative_paths:
            return 0

        collection = self._require_collection()
        try:
            count_before = collection.count()
            for relative_path in sorted(set(relative_paths)):
                logger.info(
                    "Deleting vectors collection=%s relative_path=%s",
                    self._collection_name,
                    relative_path,
                )
                collection.delete(where={"relative_path": relative_path})
            return max(count_before - collection.count(), 0)
        except Exception as exc:
            raise VectorDeleteError(
                f"Unable to delete vectors from collection: "
                f"{self._collection_name}"
            ) from exc

    def collection_info(self) -> VectorCollectionInfo:
        """Return collection name and persisted record count."""
        collection = self._require_collection()
        try:
            record_count = collection.count()
        except Exception as exc:
            raise VectorStoreUnavailableError(
                f"Unable to read vector collection: "
                f"{self._collection_name}"
            ) from exc
        return VectorCollectionInfo(
            collection_name=self._collection_name,
            record_count=record_count,
        )

    def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        """Run unfiltered cosine similarity search in ChromaDB."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        collection = self._require_collection()
        try:
            record_count = collection.count()
            if record_count == 0:
                raise EmptyVectorStoreError(
                    "The vector collection is empty."
                )

            result = collection.query(
                query_embeddings=[query_embedding.values],
                n_results=min(top_k, record_count),
                include=["documents", "metadatas", "distances"],
            )
            return self._parse_search_result(result)
        except EmptyVectorStoreError:
            raise
        except InvalidVectorSearchResultError:
            raise
        except Exception as exc:
            raise VectorSearchError(
                f"Unable to search vector collection: "
                f"{self._collection_name}"
            ) from exc

    def search_document(
        self,
        query_embedding: EmbeddingVector,
        relative_path: str,
        top_k: int,
    ) -> list[VectorSearchRecord]:
        """Search within one document without changing persisted data."""
        if not relative_path.strip():
            raise ValueError("relative_path cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        collection = self._require_collection()
        try:
            matching = collection.get(
                where={"relative_path": relative_path},
                include=[],
            )
            count = len(matching.get("ids", []))
            if count == 0:
                return []
            result = collection.query(
                query_embeddings=[query_embedding.values],
                n_results=min(top_k, count),
                where={"relative_path": relative_path},
                include=["documents", "metadatas", "distances"],
            )
            return self._parse_search_result(result)
        except InvalidVectorSearchResultError:
            raise
        except Exception as exc:
            raise VectorSearchError(
                f"Unable to search document in collection: {relative_path}"
            ) from exc

    def document_catalog(self) -> list[dict[str, str]]:
        """Build document identities from persisted chunk metadata."""
        collection = self._require_collection()
        try:
            result = collection.get(include=["metadatas"])
            catalog: dict[str, dict[str, str]] = {}
            for metadata in result.get("metadatas") or []:
                if not isinstance(metadata, dict):
                    continue
                path = str(metadata.get("relative_path", ""))
                if not path or not path.startswith("guides/antikor_v2/"):
                    continue
                entry = catalog.setdefault(
                    path,
                    {
                        "relative_path": path,
                        "title": "",
                        "category": path.split("/")[-2],
                    },
                )
                if metadata.get("chunk_index") == 0:
                    entry["title"] = str(metadata.get("section_title", ""))
            for entry in catalog.values():
                if not entry["title"]:
                    entry["title"] = Path(entry["relative_path"]).stem
            return sorted(catalog.values(), key=lambda item: item["relative_path"])
        except Exception as exc:
            raise VectorSearchError("Unable to build indexed document catalog.") from exc

    def health_check(self) -> bool:
        """Return whether the persistent Chroma client is operational."""
        try:
            self._connect().heartbeat()
        except VectorStoreUnavailableError:
            return False
        return True

    def _connect(self) -> Any:
        """Create the persistent Chroma client on first use."""
        if self._client is None:
            logger.info(
                "Connecting to ChromaDB path=%s",
                self._persistence_path,
            )
            try:
                self._persistence_path.mkdir(parents=True, exist_ok=True)
                self._client = self._client_factory(
                    path=str(self._persistence_path)
                )
            except Exception as exc:
                raise VectorStoreUnavailableError(
                    f"Unable to connect to ChromaDB at: "
                    f"{self._persistence_path}"
                ) from exc
        return self._client

    def _require_collection(self) -> Any:
        """Return the collection, creating it automatically when needed."""
        if self._collection is None:
            self.create_collection()
        return self._collection

    @staticmethod
    def _validate_cosine_configuration(collection: Any) -> None:
        """Reject an existing collection configured with another metric."""
        configuration = getattr(collection, "configuration", None)
        if configuration is None:
            return

        hnsw_configuration = configuration.get("hnsw") or {}
        if hnsw_configuration.get("space") != "cosine":
            raise CollectionCreationError(
                "The vector collection must use cosine distance."
            )

    def _delete_stale_records(
        self,
        collection: Any,
        embedded_chunks: Sequence[EmbeddedChunk],
        current_ids: set[str],
    ) -> None:
        """Delete old chunk IDs no longer present in changed documents."""
        relative_paths = {
            item.chunk.metadata.relative_path
            for item in embedded_chunks
        }
        for relative_path in relative_paths:
            existing = collection.get(
                where={"relative_path": relative_path},
                include=[],
            )
            stale_ids = set(existing["ids"]) - current_ids
            if stale_ids:
                collection.delete(ids=sorted(stale_ids))

    @staticmethod
    def _parse_search_result(
        result: Any,
    ) -> list[VectorSearchRecord]:
        """Validate Chroma's columnar result and normalize cosine scores."""
        if not isinstance(result, dict):
            raise InvalidVectorSearchResultError

        try:
            documents = result["documents"][0]
            metadatas = result["metadatas"][0]
            distances = result["distances"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise InvalidVectorSearchResultError from exc

        if not (
            isinstance(documents, list)
            and isinstance(metadatas, list)
            and isinstance(distances, list)
            and len(documents) == len(metadatas) == len(distances)
        ):
            raise InvalidVectorSearchResultError

        records: list[VectorSearchRecord] = []
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
            strict=True,
        ):
            if (
                not isinstance(document, str)
                or not document
                or not isinstance(metadata, dict)
                or isinstance(distance, bool)
                or not isinstance(distance, (int, float))
                or not math.isfinite(distance)
            ):
                raise InvalidVectorSearchResultError

            similarity = max(-1.0, min(1.0, 1.0 - float(distance)))
            records.append(
                VectorSearchRecord(
                    document=document,
                    similarity_score=similarity,
                    metadata=metadata,
                )
            )

        records.sort(
            key=lambda record: record.similarity_score,
            reverse=True,
        )
        return records

    @staticmethod
    def _record_id(embedded_chunk: EmbeddedChunk) -> str:
        """Build a stable record ID from source path and chunk index."""
        metadata = embedded_chunk.chunk.metadata
        identity = (
            f"{metadata.relative_path}\0{metadata.chunk_index}"
        ).encode("utf-8")
        return hashlib.sha256(identity).hexdigest()

    @staticmethod
    def _metadata(embedded_chunk: EmbeddedChunk) -> dict[str, str | int]:
        """Return the approved scalar metadata stored with one vector."""
        metadata = embedded_chunk.chunk.metadata
        return {
            "document_name": metadata.document_name,
            "relative_path": metadata.relative_path,
            "section_title": metadata.section_title,
            "chunk_index": metadata.chunk_index,
            "language": metadata.language,
        }
