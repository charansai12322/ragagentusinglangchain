"""Document upload and ingestion endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_valid_pdf(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test successful upload of a text-rich PDF document."""
    files = {"file": ("attention.pdf", valid_pdf_bytes, "application/pdf")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == "attention.pdf"
    assert data["total_pages"] == 1
    assert data["chunk_count"] > 0
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_upload_empty_scanned_pdf(client: AsyncClient, empty_pdf_bytes: bytes):
    """Test graceful rejection of scanned/empty PDF without extractable text."""
    files = {"file": ("empty.pdf", empty_pdf_bytes, "application/pdf")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "DOCUMENT_PROCESSING_ERROR"
    assert "scanned" in data["detail"].lower() or "no extractable text" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_corrupt_pdf(client: AsyncClient, corrupt_pdf_bytes: bytes):
    """Test rejection of malformed/corrupt PDF."""
    files = {"file": ("corrupt.pdf", corrupt_pdf_bytes, "application/pdf")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "DOCUMENT_PROCESSING_ERROR"


@pytest.mark.asyncio
async def test_upload_encrypted_pdf(client: AsyncClient, encrypted_pdf_bytes: bytes):
    """Test rejection of password-protected PDF."""
    files = {"file": ("encrypted.pdf", encrypted_pdf_bytes, "application/pdf")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 422
    data = response.json()
    assert "password" in data["detail"].lower() or "encrypted" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_non_pdf(client: AsyncClient):
    """Test rejection of arbitrary text/image file lacking PDF signature."""
    files = {"file": ("malicious.exe", b"MZThis is not a PDF", "application/octet-stream")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 422
    data = response.json()
    assert "valid pdf" in data["detail"].lower()


@pytest.mark.asyncio
async def test_session_status_and_deletion(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test querying status and deleting an active session."""
    files = {"file": ("test.pdf", valid_pdf_bytes, "application/pdf")}
    create_resp = await client.post("/api/documents/upload", files=files)
    session_id = create_resp.json()["session_id"]

    # Check status
    status_resp = await client.get(f"/api/documents/{session_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "ready"

    # Delete session
    del_resp = await client.delete(f"/api/documents/{session_id}")
    assert del_resp.status_code == 200

    # Querying deleted session returns 404
    status_after = await client.get(f"/api/documents/{session_id}/status")
    assert status_after.status_code == 404


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    """Test rejection of empty 0-byte file."""
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 422
    assert "empty" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_oversized_file(client: AsyncClient):
    """Test rejection of files exceeding MAX_UPLOAD_SIZE_MB."""
    oversized_bytes = b"%PDF-1.4\n" + b"0" * (16 * 1024 * 1024)
    files = {"file": ("huge.pdf", oversized_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 400
    assert "exceeds" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_page_limit_exceeded(client: AsyncClient):
    """Test rejection of PDFs exceeding the page limit."""
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(102):
        writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)

    files = {"file": ("toolong.pdf", buf.getvalue(), "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 422
    assert "exceeds the maximum limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_missing_multipart_field(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test rejection when required multipart form field is missing or incorrectly named."""
    files = {"wrong_field_name": ("test.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upload_filename_traversal_sanitization(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test that uploaded filenames with directory traversal are safely sanitized."""
    files = {"file": ("../../../../etc/passwd.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert "/" not in data["filename"]
    assert ".." not in data["filename"]
    assert data["filename"] == "passwd.pdf"
    # Clean up
    await client.delete(f"/api/documents/{data['session_id']}")


@pytest.mark.asyncio
async def test_upload_failure_leaves_no_orphaned_session(client: AsyncClient, corrupt_pdf_bytes: bytes):
    """Test that a failed ingestion does NOT leave any phantom session in SessionService."""
    from backend.app.main import app_state

    # Get baseline count
    baseline_count = await app_state.rag_service.session_service.get_active_session_count()

    files = {"file": ("corrupt.pdf", corrupt_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    assert resp.status_code == 422

    # Verify session count did not increase
    current_count = await app_state.rag_service.session_service.get_active_session_count()
    assert current_count == baseline_count
