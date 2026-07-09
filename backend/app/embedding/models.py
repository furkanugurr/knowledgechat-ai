"""Validated embedding result models."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.knowledge.models import KnowledgeChunk


class EmbeddingVector(BaseModel):
    """One finite, non-empty numeric embedding vector."""

    values: list[float] = Field(min_length=1)

    model_config = ConfigDict(allow_inf_nan=False)


class EmbeddedChunk(BaseModel):
    """A knowledge chunk paired with its generated embedding."""

    chunk: KnowledgeChunk
    embedding: EmbeddingVector


class EmbeddingResult(BaseModel):
    """Serializable result of one embedding batch."""

    embedded_chunks: list[EmbeddedChunk]
    total_chunks: int = Field(ge=0)
    dimensions: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_batch_shape(self) -> "EmbeddingResult":
        """Ensure counts and vector dimensions are internally consistent."""
        if self.total_chunks != len(self.embedded_chunks):
            raise ValueError(
                "total_chunks must match the embedded chunk count"
            )

        expected_dimensions = (
            len(self.embedded_chunks[0].embedding.values)
            if self.embedded_chunks
            else 0
        )
        if self.dimensions != expected_dimensions:
            raise ValueError(
                "dimensions must match the generated vector size"
            )
        if any(
            len(item.embedding.values) != expected_dimensions
            for item in self.embedded_chunks
        ):
            raise ValueError("all embedding vectors must have equal dimensions")
        return self
