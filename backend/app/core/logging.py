"""Centralized Python logging configuration."""

from logging.config import dictConfig


def configure_logging(log_level: str) -> None:
    """Configure application-wide console logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s | %(levelname)s | "
                        "%(name)s | %(filename)s:%(lineno)d | %(message)s"
                    ),
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": log_level,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": log_level,
            },
        }
    )
