"""Validated vector store operation models."""

from pydantic import BaseModel, ConfigDict, Field


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


class VectorSearchRecord(BaseModel):
    """Provider-independent normalized similarity search record."""

    document: str = Field(min_length=1)
    similarity_score: float = Field(ge=-1.0, le=1.0)
    metadata: dict[str, str | int]

    model_config = ConfigDict(allow_inf_nan=False)
