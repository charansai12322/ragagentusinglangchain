"""Sanitized logging configuration."""

import logging
import re
import sys

from backend.app.core.config import settings

# Patterns for sensitive tokens or keys
SECRET_PATTERNS = [
    re.compile(r"gsk_[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
]


class SanitizingFormatter(logging.Formatter):
    """Formatter that redacts sensitive API keys and tokens from log output."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
        return sanitized


def setup_logging() -> None:
    """Initialize root logging handler with sanitization."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid duplicate handlers on reloads
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve named logger."""
    return logging.getLogger(name)
