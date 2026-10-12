"""Application configuration management with Pydantic Settings."""

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central application settings loaded from environment and .env."""

    # Groq LLM Configuration
    GROQ_API_KEY: str = Field(
        default="PASTE_YOUR_GROQ_API_KEY_HERE",
        description="API key for Groq Cloud service",
    )
    GROQ_MODEL_NAME: str = Field(
        default="openai/gpt-oss-120b",
        description="Groq model identifier",
    )

    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="FastEmbed model name for lightweight CPU embeddings",
    )

    # Application Environment & Logging
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "https://ragagentusinglangchain.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed origins for CORS",
    )

    # Document Ingestion Security & Limits
    MAX_UPLOAD_SIZE_MB: int = Field(default=15, description="Maximum upload file size in megabytes")
    MAX_PDF_PAGES: int = Field(default=100, description="Maximum allowed pages per PDF document")
    PDF_DOWNLOAD_TIMEOUT_SECONDS: float = Field(default=15.0, description="Timeout for downloading PDF from URL")

    # Session & Concurrency Bounds
    SESSION_TTL_MINUTES: int = Field(default=60, description="Session idle time before expiration in minutes")
    MAX_SESSIONS: int = Field(default=20, description="Maximum concurrent active in-memory document sessions")
    MAX_CONCURRENT_INGESTIONS: int = Field(default=2, description="Maximum concurrent document ingestion operations")
    MAX_CONCURRENT_LLM_REQUESTS: int = Field(default=3, description="Maximum concurrent LLM chat generation calls")

    # RAG & Retrieval Tuning
    RAG_TOP_K: int = Field(default=4, description="Number of top chunks retrieved for answering")
    MAX_CONTEXT_TOKENS: int = Field(default=6000, description="Budget for context window tokens")
    MAX_CHAT_HISTORY_TURNS: int = Field(default=5, description="Maximum conversation history turns per session")
    LLM_TIMEOUT_SECONDS: float = Field(default=30.0, description="Timeout for LLM inference in seconds")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Support both JSON strings and Python lists for CORS_ORIGINS."""
        parsed: list[str] = []
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    loaded = json.loads(value)
                    if isinstance(loaded, list):
                        parsed = [str(origin).strip().rstrip("/") for origin in loaded if str(origin).strip()]
                except Exception:
                    pass
            if not parsed:
                parsed = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        elif isinstance(value, list):
            parsed = [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]

        origins = (
            parsed
            if parsed
            else [
                "https://ragagentusinglangchain.vercel.app",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        )

        # Always guarantee the production Vercel frontend origin is allowed
        if "https://ragagentusinglangchain.vercel.app" not in origins:
            origins.append("https://ragagentusinglangchain.vercel.app")

        return origins

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_groq_configured(self) -> bool:
        """Check if a real Groq API key is configured."""
        key = self.GROQ_API_KEY.strip()
        return bool(key and key != "PASTE_YOUR_GROQ_API_KEY_HERE" and not key.startswith("PASTE_"))


# Cached settings instance
settings = Settings()
