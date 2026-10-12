"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from backend.app.core.config import settings
from backend.app.models.responses import HealthResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(tags=["Health"])


def get_rag_service() -> RAGService:
    """Dependency provider for RAGService."""
    from backend.app.main import app_state

    return app_state.rag_service


@router.get("/health", response_model=HealthResponse)
async def health_check(rag_service: RAGService = Depends(get_rag_service)) -> HealthResponse:
    """
    Check application health, configuration status, and active session count.
    Does not invoke the upstream LLM to avoid rate-limit consumption.
    """
    active_count = await rag_service.session_service.get_active_session_count()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(UTC),
        groq_configured=settings.is_groq_configured,
        groq_model=settings.GROQ_MODEL_NAME,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        active_sessions=active_count,
    )
