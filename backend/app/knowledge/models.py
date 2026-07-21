"""Validated models used by the knowledge preparation pipeline."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class KnowledgeSection(BaseModel):
    """One heading-aware section of a Markdown document."""

    title: str = Field(min_length=1)
    level: int | None = Field(default=None, ge=1, le=6)
    content: str


class KnowledgeDocument(BaseModel):
    """Parsed representation of one knowledge base Markdown file."""

    document_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    content: str
    sections: list[KnowledgeSection]
    language: str = Field(min_length=2)
    created_at: datetime
    updated_at: datetime


class KnowledgeMetadata(BaseModel):
    """Search-independent metadata attached to one knowledge chunk."""

    document_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    section_title: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    total_chunks: int = Field(ge=1)
    language: str = Field(min_length=2)
    source_type: str = Field(default="knowledge_document", min_length=1)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_chunk_index(self) -> "KnowledgeMetadata":
        """Ensure the zero-based chunk index fits the chunk collection."""
        if self.chunk_index >= self.total_chunks:
            raise ValueError("chunk_index must be less than total_chunks")
        return self


class KnowledgeChunk(BaseModel):
    """One chunk of knowledge text and its retrieval-ready metadata."""

    content: str = Field(min_length=1)
    metadata: KnowledgeMetadata


class IndexedFile(BaseModel):
    """Persistent incremental-index state for one knowledge document."""

    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    indexed_at: datetime
    chunk_count: int = Field(ge=0)


class IndexStatistics(BaseModel):
    """Serializable operational statistics for one indexing run."""

    files_scanned: int = Field(ge=0)
    files_indexed: int = Field(ge=0)
    files_skipped: int = Field(ge=0)
    files_removed: int = Field(ge=0)
    chunks_created: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)

    def to_report(self) -> str:
        """Return a human-readable knowledge indexing report."""
        return "\n".join(
            (
                "Knowledge Index Report",
                "",
                f"Files scanned: {self.files_scanned}",
                f"Files indexed: {self.files_indexed}",
                f"Files skipped: {self.files_skipped}",
                f"Files removed: {self.files_removed}",
                f"Chunks created: {self.chunks_created}",
                f"Duration: {self.duration_seconds:.2f} sec",
            )
        )


class IndexResult(BaseModel):
    """Serializable output containing incremental indexing changes."""

    manifest_version: int = Field(ge=1)
    indexed_files: list[IndexedFile]
    removed_files: list[str]
    chunks: list[KnowledgeChunk]
    statistics: IndexStatistics
