"""Response schemas for API endpoints."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status response."""

    status: str = Field(default="healthy", description="Application operational health")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="UTC timestamp of the check")
    groq_configured: bool = Field(..., description="Whether a valid Groq API key is present")
    groq_model: str = Field(..., description="Configured Groq model identifier")
    embedding_model: str = Field(..., description="Configured embedding model identifier")
    active_sessions: int = Field(..., description="Current count of active in-memory document sessions")


class Citation(BaseModel):
    """Structured citation referencing supporting text from document."""

    page: int = Field(..., description="1-indexed page number containing the referenced text")
    snippet: str = Field(..., description="Supporting chunk snippet from the page")
    relevance_score: float = Field(..., description="Cosine similarity score of the retrieved chunk (0.0 to 1.0)")


class DocumentIngestResponse(BaseModel):
    """Response returned after successful document ingestion."""

    session_id: str = Field(..., description="Unique UUID assigned to this document session")
    filename: str = Field(..., description="Sanitized document filename")
    total_pages: int = Field(..., description="Total pages parsed from the PDF")
    chunk_count: int = Field(..., description="Number of text chunks embedded into the session index")
    status: str = Field(default="ready", description="Current status of the document session")
    created_at: datetime = Field(..., description="Timestamp of session creation")
    expires_at: datetime = Field(..., description="Timestamp when this temporary session will be evicted")


class ChatResponse(BaseModel):
    """Response returned from asking a question."""

    answer: str = Field(..., description="Grounded answer synthesized by the LLM")
    citations: list[Citation] = Field(default_factory=list, description="Page citations supporting the answer")
    session_id: str = Field(..., description="Active session UUID")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


class SessionStatusResponse(BaseModel):
    """Details and status of an active document session."""

    session_id: str = Field(..., description="Unique UUID assigned to this document session")
    filename: str = Field(..., description="Sanitized document filename")
    status: str = Field(..., description="Current session state: processing, ready, failed, expired")
    total_pages: int = Field(..., description="Total pages parsed")
    chunk_count: int = Field(..., description="Total chunks indexed")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    turns_count: int = Field(..., description="Number of conversation turns recorded in this session")


class ErrorResponse(BaseModel):
    """Unified API error format."""

    error: str = Field(..., description="Short error classification")
    detail: str = Field(..., description="Human-readable explanation of the issue")
    code: str = Field(..., description="Machine-readable error code")
    request_id: str | None = Field(default=None, description="Correlation ID for request tracing")
