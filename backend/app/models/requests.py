"""Request schemas for API endpoints."""

from pydantic import BaseModel, Field, field_validator


class UrlIngestRequest(BaseModel):
    """Payload for ingesting a PDF from a remote URL."""

    url: str = Field(
        ...,
        description="Public HTTP/HTTPS URL pointing directly to a PDF document",
        examples=["https://arxiv.org/pdf/1706.03762"],
    )

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, value: str) -> str:
        clean = value.strip()
        if not clean.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return clean


class ChatRequest(BaseModel):
    """Payload for asking a question against a document session."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question grounded in the active document",
        examples=["What is the main advantage of multi-head attention?"],
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Question cannot be empty or whitespace only")
        return clean
