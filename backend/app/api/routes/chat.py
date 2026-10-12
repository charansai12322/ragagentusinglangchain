"""Chat and question answering endpoints."""

from fastapi import APIRouter, Depends

from backend.app.models.requests import ChatRequest
from backend.app.models.responses import ChatResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Chat"])


def get_rag_service() -> RAGService:
    from backend.app.main import app_state

    return app_state.rag_service


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def ask_question(
    session_id: str,
    payload: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    """
    Ask a grounded question against the document associated with session_id.
    Maintains bounded conversation history for follow-ups and returns page citations.
    """
    answer, citations, processing_time_ms = await rag_service.answer_question(
        session_id=session_id,
        question=payload.question,
    )

    return ChatResponse(
        answer=answer,
        citations=citations,
        session_id=session_id,
        processing_time_ms=processing_time_ms,
    )
