"""Environment-based application configuration."""

import logging
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables."""

    app_name: str = Field(validation_alias="APP_NAME")
    app_version: str = Field(validation_alias="APP_VERSION")
    app_env: str = Field(validation_alias="APP_ENV")
    host: str = Field(validation_alias="HOST")
    port: int = Field(validation_alias="PORT", ge=1, le=65535)
    log_level: str = Field(validation_alias="LOG_LEVEL")
    ollama_host: str = Field(validation_alias="OLLAMA_HOST")
    chat_model: str = Field(validation_alias="CHAT_MODEL")
    request_timeout: float = Field(
        validation_alias="REQUEST_TIMEOUT",
        gt=0,
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


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
