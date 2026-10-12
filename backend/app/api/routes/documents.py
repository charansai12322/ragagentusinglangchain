"""Document ingestion and session lifecycle endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.app.core.config import settings
from backend.app.models.requests import UrlIngestRequest
from backend.app.models.responses import DocumentIngestResponse, SessionStatusResponse
from backend.app.security.upload_validation import sanitize_filename, validate_pdf_bytes
from backend.app.security.url_validation import safe_download_pdf
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_rag_service() -> RAGService:
    from backend.app.main import app_state

    return app_state.rag_service


@router.post("/upload", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    rag_service: RAGService = Depends(get_rag_service),
) -> DocumentIngestResponse:
    """
    Upload a PDF document directly as multipart form data.
    Parses, chunks, and creates a session-isolated in-memory retrieval index.
    """
    raw_content = await file.read()
    validate_pdf_bytes(raw_content, max_size_bytes=settings.max_upload_size_bytes)
    filename = sanitize_filename(file.filename)

    session = await rag_service.ingest_pdf_bytes(pdf_bytes=raw_content, filename=filename)

    return DocumentIngestResponse(
        session_id=session.session_id,
        filename=session.filename,
        total_pages=session.total_pages,
        chunk_count=session.chunk_count,
        status=session.status,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.post("/url", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document_from_url(
    payload: UrlIngestRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> DocumentIngestResponse:
    """
    Ingest a PDF from a remote HTTP/HTTPS URL with SSRF protection.
    Streams download with strict byte limits and DNS verification.
    """
    pdf_bytes, filename = await safe_download_pdf(
        url=payload.url,
        max_size_bytes=settings.max_upload_size_bytes,
        timeout_seconds=settings.PDF_DOWNLOAD_TIMEOUT_SECONDS,
    )
    validate_pdf_bytes(pdf_bytes, max_size_bytes=settings.max_upload_size_bytes)
    sanitized_name = sanitize_filename(filename)

    session = await rag_service.ingest_pdf_bytes(pdf_bytes=pdf_bytes, filename=sanitized_name)

    return DocumentIngestResponse(
        session_id=session.session_id,
        filename=session.filename,
        total_pages=session.total_pages,
        chunk_count=session.chunk_count,
        status=session.status,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service),
) -> SessionStatusResponse:
    """Retrieve document processing status, page count, and conversation length."""
    session = await rag_service.session_service.get_session(session_id)
    return SessionStatusResponse(
        session_id=session.session_id,
        filename=session.filename,
        status=session.status,
        total_pages=session.total_pages,
        chunk_count=session.chunk_count,
        created_at=session.created_at,
        expires_at=session.expires_at,
        turns_count=len(session.history) // 2,
    )


@router.delete("/{session_id}")
async def delete_document_session(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service),
) -> dict[str, str]:
    """Delete a document session and release all associated in-memory vectors."""
    deleted = await rag_service.delete_session(session_id)
    if not deleted:
        return {"message": f"Session '{session_id}' did not exist or was already expired."}
    return {"message": f"Session '{session_id}' deleted successfully."}
