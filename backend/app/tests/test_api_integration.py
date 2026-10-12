"""Dedicated API-Level End-to-End Scenarios (Scenarios 1 through 7)."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from httpx import AsyncClient

from backend.app.core.errors import RateLimitExceededError
from backend.app.main import app_state
from backend.app.services.chat_service import MockChatService
from backend.app.tests.conftest import make_pdf_with_text


@pytest.mark.asyncio
async def test_scenario_1_complete_document_lifecycle(client: AsyncClient, valid_pdf_bytes: bytes):
    """
    Scenario 1: Complete successful document lifecycle.
    Health -> Ingest -> Status -> Grounded Chat -> Follow-up -> Delete -> Verification.
    """
    # 1. Call health endpoint
    health_resp = await client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    # 2. Upload valid PDF
    files = {"file": ("attention_lifecycle.pdf", valid_pdf_bytes, "application/pdf")}
    upload_resp = await client.post("/api/documents/upload", files=files)
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    session_id = upload_data["session_id"]
    assert upload_data["status"] == "ready"
    assert upload_data["total_pages"] == 1
    assert upload_data["chunk_count"] > 0

    # 3. Retrieve session status
    status_resp = await client.get(f"/api/documents/{session_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["session_id"] == session_id
    assert status_data["turns_count"] == 0

    # 4. Ask grounded question
    chat_resp = await client.post(
        f"/api/documents/{session_id}/chat",
        json={"question": "What architecture is introduced in 2017?"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert len(chat_data["answer"]) > 0
    assert len(chat_data["citations"]) > 0
    assert chat_data["citations"][0]["page"] == 1

    # 5. Ask follow-up question
    followup_resp = await client.post(
        f"/api/documents/{session_id}/chat",
        json={"question": "How does multi-head attention work?"},
    )
    assert followup_resp.status_code == 200
    assert followup_resp.json()["session_id"] == session_id

    # Verify turn count updated to 2
    status2_resp = await client.get(f"/api/documents/{session_id}/status")
    assert status2_resp.json()["turns_count"] == 2

    # 6. Delete session
    del_resp = await client.delete(f"/api/documents/{session_id}")
    assert del_resp.status_code == 200
    assert "deleted successfully" in del_resp.json()["message"]

    # 7. Verify subsequent chat and status return 404
    after_chat = await client.post(
        f"/api/documents/{session_id}/chat",
        json={"question": "Where is the attention?"},
    )
    assert after_chat.status_code == 404
    assert after_chat.json()["code"] == "SESSION_NOT_FOUND"

    after_status = await client.get(f"/api/documents/{session_id}/status")
    assert after_status.status_code == 404
    assert after_status.json()["code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_scenario_2_invalid_document_recovery(
    client: AsyncClient, corrupt_pdf_bytes: bytes, valid_pdf_bytes: bytes
):
    """
    Scenario 2: Invalid document recovery.
    Invalid file -> 422 -> Verify zero orphaned sessions -> Upload valid -> Chat succeeds.
    """
    baseline_sessions = await app_state.rag_service.session_service.get_active_session_count()

    # 1. Upload invalid corrupt file
    corrupt_files = {"file": ("bad.pdf", corrupt_pdf_bytes, "application/pdf")}
    err_resp = await client.post("/api/documents/upload", files=corrupt_files)
    assert err_resp.status_code == 422
    assert err_resp.json()["code"] == "DOCUMENT_PROCESSING_ERROR"

    # 2. Verify no unusable session remains registered
    active_after_error = await app_state.rag_service.session_service.get_active_session_count()
    assert active_after_error == baseline_sessions

    # 3. Upload valid PDF
    valid_files = {"file": ("good.pdf", valid_pdf_bytes, "application/pdf")}
    ok_resp = await client.post("/api/documents/upload", files=valid_files)
    assert ok_resp.status_code == 201
    sid = ok_resp.json()["session_id"]

    # 4. Ask question
    chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "What is Transformer?"})
    assert chat_resp.status_code == 200
    assert len(chat_resp.json()["citations"]) > 0

    # Cleanup
    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_scenario_3_remote_pdf_lifecycle(client: AsyncClient, valid_pdf_bytes: bytes):
    """
    Scenario 3: Remote PDF lifecycle.
    Remote download with mock HTTP transport -> Ingest -> Chat -> Delete.
    """
    import socket
    from unittest.mock import patch

    def mock_dns(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    with patch("socket.getaddrinfo", side_effect=mock_dns):
        async with respx.mock(base_url="https://remote-library.org") as respx_mock:
            respx_mock.get("/papers/transformer.pdf").mock(
                return_value=httpx.Response(
                    200,
                    headers={"Content-Type": "application/pdf"},
                    content=valid_pdf_bytes,
                )
            )

            # Ingest URL
            url_payload = {"url": "https://remote-library.org/papers/transformer.pdf"}
            resp = await client.post("/api/documents/url", json=url_payload)
            assert resp.status_code == 201
            data = resp.json()
            sid = data["session_id"]
            assert data["filename"] == "transformer.pdf"
            assert data["total_pages"] == 1

            # Chat against session
            chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "What is the paper about?"})
            assert chat_resp.status_code == 200
            assert len(chat_resp.json()["citations"]) > 0

            # Delete session
            del_resp = await client.delete(f"/api/documents/{sid}")
            assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_scenario_4_cross_session_isolation(client: AsyncClient):
    """
    Scenario 4: Cross-session isolation.
    Ingest A (Aurora) & B (Borealis) -> Verify isolation -> Delete A -> Verify B works.
    """
    pdf_aurora = make_pdf_with_text("Project Aurora is an enterprise AI solution in Hyderabad.")
    pdf_borealis = make_pdf_with_text("Project Borealis conducts atmospheric research in Tromso.")

    # Ingest A
    resp_a = await client.post("/api/documents/upload", files={"file": ("aurora.pdf", pdf_aurora, "application/pdf")})
    assert resp_a.status_code == 201
    sid_a = resp_a.json()["session_id"]

    # Ingest B
    files_b = {"file": ("borealis.pdf", pdf_borealis, "application/pdf")}
    resp_b = await client.post("/api/documents/upload", files=files_b)
    assert resp_b.status_code == 201
    sid_b = resp_b.json()["session_id"]

    # Query A
    chat_a = await client.post(f"/api/documents/{sid_a}/chat", json={"question": "Where is Aurora based?"})
    assert chat_a.status_code == 200
    for citation in chat_a.json()["citations"]:
        assert "Aurora" in citation["snippet"]
        assert "Borealis" not in citation["snippet"]

    # Query B
    chat_b = await client.post(f"/api/documents/{sid_b}/chat", json={"question": "Where is Borealis based?"})
    assert chat_b.status_code == 200
    for citation in chat_b.json()["citations"]:
        assert "Borealis" in citation["snippet"]
        assert "Aurora" not in citation["snippet"]

    # Delete session A
    await client.delete(f"/api/documents/{sid_a}")

    # Confirm session B remains functional
    chat_b_after = await client.post(f"/api/documents/{sid_b}/chat", json={"question": "Summarize Borealis"})
    assert chat_b_after.status_code == 200

    # Cleanup B
    await client.delete(f"/api/documents/{sid_b}")


@pytest.mark.asyncio
async def test_scenario_5_provider_outage_and_recovery(client: AsyncClient, valid_pdf_bytes: bytes):
    """
    Scenario 5: Provider outage.
    Ingest PDF -> Simulate provider 429 -> Verify error -> Restore provider -> Verify success.
    """
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    original_chat_svc = app_state.rag_service.chat_service

    # 1. Simulate provider failure (429 Rate Limit)
    class FailingChatService:
        async def generate(self, messages):
            raise RateLimitExceededError("Simulated Groq 429 rate limit exceeded")

    app_state.rag_service.chat_service = FailingChatService()

    err_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "What is the key mechanism?"})
    assert err_resp.status_code == 429
    assert err_resp.json()["code"] == "RATE_LIMIT_EXCEEDED"

    # 2. Restore working provider
    app_state.rag_service.chat_service = MockChatService(answer_prefix="Recovered answer")

    ok_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "What is the key mechanism?"})
    assert ok_resp.status_code == 200
    assert "Recovered answer" in ok_resp.json()["answer"]

    # Restore original service and cleanup
    app_state.rag_service.chat_service = original_chat_svc
    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_scenario_6_expired_session(client: AsyncClient, valid_pdf_bytes: bytes):
    """
    Scenario 6: Expired session.
    Create session -> Artificially expire timestamp -> Status 404 -> Chat 404 -> Vectors purged.
    """
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    # Artificially expire the session
    session = await app_state.rag_service.session_service.get_session(sid)
    session.expires_at = datetime.now(UTC) - timedelta(hours=2)

    # Next access to status should detect expiration and return 404
    status_resp = await client.get(f"/api/documents/{sid}/status")
    assert status_resp.status_code == 404
    assert status_resp.json()["code"] == "SESSION_NOT_FOUND"

    # Chat should also return 404
    chat_resp = await client.post(f"/api/documents/{sid}/chat", json={"question": "Hello?"})
    assert chat_resp.status_code == 404

    # Verify vector index was cleaned up by eviction callback
    assert not app_state.rag_service.vector_service.has_session(sid)


@pytest.mark.asyncio
async def test_scenario_7_security_rejection_and_error_sanitization(client: AsyncClient):
    """
    Scenario 7: Security rejection and error sanitization.
    SSRF URL -> 400; Malformed PDF -> 422; Non-existent session -> 404.
    Ensure internal tracebacks and keys are not leaked.
    """
    # 1. Prohibited loopback URL
    ssrf_resp = await client.post("/api/documents/url", json={"url": "http://127.0.0.1:8000/api/health"})
    assert ssrf_resp.status_code == 400
    assert ssrf_resp.json()["code"] == "SECURITY_VIOLATION"
    assert "Traceback" not in ssrf_resp.text

    # 2. Malformed PDF upload
    files = {"file": ("corrupt.pdf", b"NOT_A_PDF_STREAM", "application/pdf")}
    bad_upload = await client.post("/api/documents/upload", files=files)
    assert bad_upload.status_code == 422
    assert bad_upload.json()["code"] == "DOCUMENT_PROCESSING_ERROR"
    assert "Traceback" not in bad_upload.text

    # 3. Access unknown session
    bad_chat = await client.post("/api/documents/00000000-0000-0000-0000-000000000000/chat", json={"question": "Test"})
    assert bad_chat.status_code == 404
    assert bad_chat.json()["code"] == "SESSION_NOT_FOUND"
    assert "Traceback" not in bad_chat.text
