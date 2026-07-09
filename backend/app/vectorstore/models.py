"""Validated vector store operation models."""

from pydantic import BaseModel, Field


class VectorCollectionInfo(BaseModel):
    """Provider-independent collection statistics."""

    collection_name: str = Field(min_length=1)
    record_count: int = Field(ge=0)


class VectorStoreResult(BaseModel):
    """Serializable result of one vector persistence operation."""

    collection_name: str = Field(min_length=1)
    vectors_upserted: int = Field(ge=0)
    vectors_deleted: int = Field(ge=0)
    total_vectors: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
