"""Environment-based application configuration."""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables."""

    app_name: str = Field(validation_alias="APP_NAME")
    app_version: str = Field(validation_alias="APP_VERSION")
    environment: str = Field(
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV")
    )
    host: str = Field(validation_alias="HOST")
    port: int = Field(validation_alias="PORT", ge=1, le=65535)
    api_v1_prefix: str = Field(
        default="/api/v1",
        validation_alias="API_V1_PREFIX",
    )
    log_level: str = Field(validation_alias="LOG_LEVEL")
    ollama_host: str = Field(validation_alias="OLLAMA_HOST")
    chat_model: str = Field(validation_alias="CHAT_MODEL")
    chat_max_tokens: int = Field(
        default=768,
        validation_alias="CHAT_MAX_TOKENS",
        ge=128,
    )
    embedding_model: str = Field(validation_alias="EMBEDDING_MODEL")
    vector_db_path: Path = Field(validation_alias="VECTOR_DB_PATH")
    vector_collection_name: str = Field(
        validation_alias="VECTOR_COLLECTION_NAME"
    )
    retrieval_candidate_k: int = Field(
        default=30,
        validation_alias="RETRIEVAL_CANDIDATE_K",
        ge=1,
    )
    chat_context_max_chunks: int = Field(
        default=5,
        validation_alias="CHAT_CONTEXT_MAX_CHUNKS",
        ge=1,
    )
    retrieval_min_similarity: float = Field(
        default=0.65,
        validation_alias="RETRIEVAL_MIN_SIMILARITY",
        ge=0,
        le=1,
    )
    request_timeout: float = Field(
        validation_alias="REQUEST_TIMEOUT",
        gt=0,
    )
    cors_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize and validate the configured Python log level."""
        normalized_value = value.upper()
        if normalized_value not in logging.getLevelNamesMapping():
            raise ValueError(f"Unsupported log level: {value}")
        return normalized_value

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_v1_prefix(cls, value: str) -> str:
        """Normalize and validate the API prefix."""
        normalized_value = value.rstrip("/")
        if not normalized_value.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        return normalized_value

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
