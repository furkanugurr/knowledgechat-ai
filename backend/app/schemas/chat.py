"""Chat endpoint schemas."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Validated single-turn chat request."""

    message: str = Field(min_length=1)

    @field_validator("message", mode="before")
    @classmethod
    def trim_message(cls, value: Any) -> Any:
        """Trim surrounding whitespace before length validation."""
        return value.strip() if isinstance(value, str) else value


class CitationSource(BaseModel):
    """Public source metadata for one retrieved knowledge chunk."""

    document_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    section_title: str | None = Field(default=None, min_length=1)
    chunk_index: int = Field(ge=0)
    similarity_score: float = Field(ge=-1.0, le=1.0)
    language: str | None = Field(default=None, min_length=2)


class ChatResponse(BaseModel):
    """Generated single-turn chat response."""

    response: str
    sources: list[CitationSource]
