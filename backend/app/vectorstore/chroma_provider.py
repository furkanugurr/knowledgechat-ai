"""Persistent ChromaDB implementation of vector storage."""

import hashlib
import logging
import math
import re
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
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer

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
                include=["documents", "metadatas", "embeddings"],
            )
            count = len(matching.get("ids", []))
            if count == 0:
                return []
            documents = matching.get("documents") or []
            metadatas = matching.get("metadatas") or []
            embeddings = matching.get("embeddings")
            if embeddings is None or not (
                len(documents) == len(metadatas) == len(embeddings)
            ):
                raise InvalidVectorSearchResultError
            query = query_embedding.values
            query_norm = math.sqrt(sum(value * value for value in query))
            records: list[VectorSearchRecord] = []
            for document, metadata, embedding in zip(
                documents, metadatas, embeddings, strict=True
            ):
                values = [float(value) for value in embedding]
                norm = math.sqrt(sum(value * value for value in values))
                similarity = (
                    sum(left * right for left, right in zip(query, values, strict=True))
                    / (query_norm * norm)
                    if query_norm and norm else 0.0
                )
                records.append(VectorSearchRecord(
                    document=document, metadata=metadata,
                    similarity_score=max(-1.0, min(1.0, similarity)),
                ))
            return sorted(
                records, key=lambda item: item.similarity_score, reverse=True
            )[:top_k]
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
            result = collection.get(include=["metadatas", "documents"])
            catalog: dict[str, dict[str, str]] = {}
            documents = result.get("documents") or []
            for index, metadata in enumerate(result.get("metadatas") or []):
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
                        "available_sections": "",
                        "source_url": "",
                    },
                )
                if metadata.get("chunk_index") == 0:
                    entry["title"] = str(metadata.get("section_title", ""))
                section = str(metadata.get("section_title", ""))
                sections = set(filter(None, entry["available_sections"].split("|")))
                sections.add(section)
                entry["available_sections"] = "|".join(sorted(sections))
                document = str(documents[index]) if index < len(documents) else ""
                source_match = re.search(
                    r"^-\s+Sayfa:\s+(\S+)", document, re.MULTILINE
                )
                if source_match:
                    entry["source_url"] = source_match.group(1)
            for entry in catalog.values():
                if not entry["title"]:
                    entry["title"] = Path(entry["relative_path"]).stem
            return sorted(catalog.values(), key=lambda item: item["relative_path"])
        except Exception as exc:
            raise VectorSearchError("Unable to build indexed document catalog.") from exc

    def concept_catalog(self) -> list[dict[str, str]]:
        """Derive technical aliases from indexed metadata and content."""
        collection = self._require_collection()
        try:
            result = collection.get(include=["metadatas", "documents"])
            aliases: dict[str, dict[str, object]] = {}
            documents = result.get("documents") or []
            for index, metadata in enumerate(result.get("metadatas") or []):
                if not isinstance(metadata, dict):
                    continue
                document = str(documents[index]) if index < len(documents) else ""
                path = str(metadata.get("relative_path", ""))
                section = str(metadata.get("section_title", ""))
                document_name = str(metadata.get("document_name", ""))
                values = [section, Path(document_name).stem]
                normalized_path = path.replace("\\", "/")
                if "/" in normalized_path:
                    values.append(normalized_path.rsplit("/", 2)[-2].replace("-", " "))
                values.extend(re.findall(r"`([^`]{2,80})`", document))
                acronym_values = re.findall(
                    r"(?<![A-Za-z0-9ÇĞİÖŞÜ])"
                    r"[A-ZÇĞİÖŞÜ]{2,}(?:-[A-ZÇĞİÖŞÜ]{2,})*"
                    r"(?![A-Za-z0-9ÇĞİÖŞÜ])",
                    " ".join((section, document_name, document)),
                )
                for acronym in acronym_values:
                    values.append(acronym)
                    values.extend(part for part in acronym.split("-") if len(part) >= 3)
                for value in values:
                    self._add_concept_alias(aliases, value, path)
                    tokens = TurkishLexicalNormalizer.tokens(value)
                    if len(tokens) > 1:
                        for token in tokens:
                            if (
                                len(token) >= 3
                                and token not in self._CONCEPT_GENERIC_TOKENS
                            ):
                                self._add_concept_alias(aliases, token, path)
            return [
                {
                    "alias": alias,
                    "display_term": str(entry["display_term"]),
                    "relative_paths": "|".join(sorted(entry["paths"])),
                    "acronym": "true" if entry["acronym"] else "false",
                }
                for alias, entry in sorted(aliases.items())
                if entry["paths"]
            ]
        except Exception as exc:
            raise VectorSearchError("Unable to build indexed concept catalog.") from exc

    def search_concept(
        self, normalized_term: str, top_k: int,
    ) -> list[VectorSearchRecord]:
        """Return exact concept occurrences ranked for definition quality."""
        if not normalized_term.strip() or top_k <= 0:
            return []
        collection = self._require_collection()
        try:
            result = collection.get(include=["metadatas", "documents"])
            documents = result.get("documents") or []
            term_tokens = set(TurkishLexicalNormalizer.tokens(normalized_term))
            ranked: list[tuple[int, int, VectorSearchRecord]] = []
            for index, metadata in enumerate(result.get("metadatas") or []):
                if not isinstance(metadata, dict):
                    continue
                document = str(documents[index]) if index < len(documents) else ""
                section = str(metadata.get("section_title", ""))
                searchable_tokens = set(TurkishLexicalNormalizer.tokens(
                    f"{section} {document}"
                ))
                if not term_tokens.issubset(searchable_tokens):
                    continue
                path = str(metadata.get("relative_path", ""))
                source_type = str(metadata.get(
                    "source_type",
                    "product_document" if path.casefold().endswith(".docx") else "guide",
                ))
                definition = self._is_definition_evidence(
                    normalized_term, section, document
                )
                section_normalized = TurkishLexicalNormalizer.phrase(section)
                preferred_section = any(
                    marker in section_normalized
                    for marker in ("tanim", "aciklama", "genel bak", "giris", "kapsam")
                )
                score = (
                    (100 if definition else 0)
                    + (30 if definition and source_type == "product_document" else 0)
                    + (15 if preferred_section else 0)
                    + (5 if normalized_term in section_normalized else 0)
                )
                enriched = dict(metadata)
                enriched["source_type"] = source_type
                enriched["definition_evidence"] = 1 if definition else 0
                record = VectorSearchRecord(
                    document=document,
                    similarity_score=0.99 if definition else 0.80,
                    metadata=enriched,
                )
                ranked.append((score, -int(metadata.get("chunk_index", 0)), record))
            ranked.sort(key=lambda item: (-item[0], item[1], str(item[2].metadata.get("relative_path", ""))))
            return [item[2] for item in ranked[:top_k]]
        except Exception as exc:
            raise VectorSearchError("Unable to search indexed concept evidence.") from exc

    _CONCEPT_GENERIC_TOKENS = frozenset({
        "ayar", "ayarlari", "alan", "bilgi", "bolum", "durum", "ekran",
        "genel", "giris", "gorunur", "islem", "kapsam", "kayit", "kontrol",
        "kullanim", "menu", "profil", "tanim", "yonetim", "yeni",
    })

    @staticmethod
    def _add_concept_alias(
        aliases: dict[str, dict[str, object]], value: str, path: str,
    ) -> None:
        normalized = TurkishLexicalNormalizer.phrase(value)
        if (
            not normalized or not path or len(normalized.split()) > 4
            or normalized in ChromaVectorStoreProvider._CONCEPT_GENERIC_TOKENS
            or all(token.isdigit() for token in normalized.split())
        ):
            return
        entry = aliases.setdefault(normalized, {
            "display_term": value.strip(), "paths": set(),
            "acronym": value.strip().isupper(),
        })
        paths = entry["paths"]
        if isinstance(paths, set):
            paths.add(path)
        entry["acronym"] = bool(entry["acronym"] or value.strip().isupper())

    @staticmethod
    def _is_definition_evidence(term: str, section: str, document: str) -> bool:
        normalized_term = TurkishLexicalNormalizer.phrase(term)
        normalized_section = TurkishLexicalNormalizer.phrase(section)
        body = re.sub(r"^#{1,6}\s+.*$", "", document, count=1, flags=re.MULTILINE).strip()
        normalized_body = TurkishLexicalNormalizer.phrase(body)
        first_sentence = re.split(r"(?<=[.!?])\s+", body, maxsplit=1)[0]
        normalized_first_sentence = TurkishLexicalNormalizer.phrase(first_sentence)
        starts_with_definition = (
            bool(re.match(
                rf"^\s*{re.escape(term)}\s*(?:,|\(|\bbir\b)",
                first_sentence,
                re.IGNORECASE,
            ))
            and "maktadir" not in normalized_first_sentence.split()[-1]
            and "mektedir" not in normalized_first_sentence.split()[-1]
            and bool(re.search(
                r"(?:dır|dir|dur|dür|tır|tir|tur|tür)\.?$",
                normalized_first_sentence,
            ))
        )
        # Only a standalone parenthetical acronym is definition evidence.
        # Lists such as ``(DMZ, WAN, LAN)`` merely mention the term.
        parenthesized = any(
            normalized_term in {
                TurkishLexicalNormalizer.phrase(part)
                for part in re.split(r"[/|-]", match.group(1))
            }
            for match in re.finditer(r"\(\s*([A-Za-z0-9/-]+)\s*\)", document)
        )
        return bool(starts_with_definition or parenthesized)

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
            "source_type": metadata.source_type,
        }
