"""Validated semantic retrieval result models."""

from pydantic import BaseModel, Field, model_validator


class RetrievedChunk(BaseModel):
    """One knowledge chunk returned by similarity search."""

    chunk_text: str = Field(min_length=1)
    similarity_score: float = Field(ge=-1.0, le=1.0)
    document_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    section_title: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    language: str = Field(min_length=2)
    source_type: str = Field(default="knowledge_document", min_length=1)
    definition_evidence: bool = False
    concept_evidence_level: str = "insufficient"


class RetrievalResult(BaseModel):
    """Serializable result of one semantic retrieval operation."""

    chunks: list[RetrievedChunk]
    total_results: int = Field(ge=0)
    top_k: int = Field(ge=1)
    duration_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_result_order(self) -> "RetrievalResult":
        """Ensure counts and descending similarity order are consistent."""
        if self.total_results != len(self.chunks):
            raise ValueError(
                "total_results must match the retrieved chunk count"
            )
        if self.total_results > self.top_k:
            raise ValueError("total_results cannot exceed top_k")
        return self
