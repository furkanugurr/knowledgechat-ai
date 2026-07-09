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


class ChatResponse(BaseModel):
    """Generated single-turn chat response."""

    response: str
