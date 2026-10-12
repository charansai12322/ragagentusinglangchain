"""Chat and grounded RAG question answering tests."""

import pytest
from httpx import AsyncClient

from backend.app.core.errors import (
    ConfigurationError,
)
from backend.app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_ask_question_success(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test successful question answering against uploaded document."""
    # 1. Upload document
    files = {"file": ("attention.pdf", valid_pdf_bytes, "application/pdf")}
    upload_resp = await client.post("/api/documents/upload", files=files)
    assert upload_resp.status_code == 201
    session_id = upload_resp.json()["session_id"]

    # 2. Ask question
    chat_payload = {"question": "What is the key mechanism of the Transformer?"}
    chat_resp = await client.post(f"/api/documents/{session_id}/chat", json=chat_payload)
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert data["citations"][0]["page"] == 1
    assert data["session_id"] == session_id
    assert data["processing_time_ms"] > 0


@pytest.mark.asyncio
async def test_follow_up_question(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test follow-up question continuity within the same session."""
    files = {"file": ("attention.pdf", valid_pdf_bytes, "application/pdf")}
    upload_resp = await client.post("/api/documents/upload", files=files)
    session_id = upload_resp.json()["session_id"]

    # Turn 1
    await client.post(f"/api/documents/{session_id}/chat", json={"question": "What is attention?"})

    # Turn 2 (Follow-up)
    resp2 = await client.post(
        f"/api/documents/{session_id}/chat",
        json={"question": "Can you summarize that in one sentence?"},
    )
    assert resp2.status_code == 200

    # Verify session has 2 turns
    status_resp = await client.get(f"/api/documents/{session_id}/status")
    assert status_resp.json()["turns_count"] == 2


@pytest.mark.asyncio
async def test_ask_question_invalid_session(client: AsyncClient):
    """Test asking question against non-existent session returns 404."""
    chat_payload = {"question": "What is attention?"}
    chat_resp = await client.post("/api/documents/non-existent-uuid/chat", json=chat_payload)
    assert chat_resp.status_code == 404
    assert chat_resp.json()["code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_chat_service_unconfigured_error():
    """Verify ChatService raises ConfigurationError when Groq API key is unconfigured."""
    chat_svc = ChatService()
    chat_svc._llm = None  # Ensure unconfigured

    with pytest.raises(ConfigurationError):
        await chat_svc.generate([{"role": "user", "content": "Hello"}])


@pytest.mark.asyncio
async def test_chat_question_validation_empty(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test rejection of empty question."""
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": ""})
    assert chat_resp.status_code == 422
    assert chat_resp.json()["code"] == "VALIDATION_ERROR"
    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_chat_question_validation_whitespace(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test rejection of whitespace-only question."""
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "   \n\t  "})
    assert chat_resp.status_code == 422
    assert chat_resp.json()["code"] == "VALIDATION_ERROR"
    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_chat_question_validation_oversized(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test rejection of questions exceeding 2000 characters."""
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "x" * 2001})
    assert chat_resp.status_code == 422
    assert chat_resp.json()["code"] == "VALIDATION_ERROR"
    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_request_id_middleware_propagation(client: AsyncClient):
    """Test that custom X-Request-ID header is propagated into response headers and body."""
    custom_id = "trace-test-uuid-999"
    resp = await client.get("/api/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == custom_id

    # Also on validation error
    err_resp = await client.post("/api/documents/some-sid/chat", json={}, headers={"X-Request-ID": custom_id})
    assert err_resp.status_code == 422
    assert err_resp.headers.get("x-request-id") == custom_id
    assert err_resp.json().get("request_id") == custom_id
