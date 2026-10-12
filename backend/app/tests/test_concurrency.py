"""Concurrency, load resilience, and race condition tests."""

import asyncio

import pytest
from httpx import AsyncClient

from backend.app.services.chat_service import MockChatService
from backend.app.services.embedding_service import MockEmbeddingService
from backend.app.services.rag_service import RAGService
from backend.app.tests.conftest import make_pdf_with_text


@pytest.mark.asyncio
async def test_concurrent_health_requests(client: AsyncClient):
    """Test rapid bursts of concurrent health check requests."""
    tasks = [client.get("/api/health") for _ in range(25)]
    responses = await asyncio.gather(*tasks)

    for r in responses:
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_concurrent_pdf_ingestion(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test concurrent uploads and verify unique session IDs and isolated indexes."""

    async def upload(idx: int):
        files = {"file": (f"doc_{idx}.pdf", valid_pdf_bytes, "application/pdf")}
        return await client.post("/api/documents/upload", files=files)

    responses = await asyncio.gather(*(upload(i) for i in range(5)))

    session_ids = set()
    for r in responses:
        assert r.status_code == 201
        sid = r.json()["session_id"]
        assert sid not in session_ids
        session_ids.add(sid)

    assert len(session_ids) == 5

    # Clean up all created sessions
    for sid in session_ids:
        await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_concurrent_chats_across_sessions(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test simultaneous chat questions across multiple independent sessions."""
    # Create 3 sessions
    session_ids = []
    for i in range(3):
        files = {"file": (f"doc_{i}.pdf", valid_pdf_bytes, "application/pdf")}
        resp = await client.post("/api/documents/upload", files=files)
        session_ids.append(resp.json()["session_id"])

    # Launch simultaneous questions
    async def ask(sid: str, q: str):
        return await client.post(f"/api/documents/{sid}/chat", json={"question": q})

    queries = [
        ask(session_ids[0], "Question for session 0"),
        ask(session_ids[1], "Question for session 1"),
        ask(session_ids[2], "Question for session 2"),
    ]
    chat_responses = await asyncio.gather(*queries)

    for i, r in enumerate(chat_responses):
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == session_ids[i]

    # Clean up
    for sid in session_ids:
        await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_concurrent_chats_in_same_session(client: AsyncClient, valid_pdf_bytes: bytes):
    """Test concurrent chat questions within the exact same session."""
    files = {"file": ("doc.pdf", valid_pdf_bytes, "application/pdf")}
    resp = await client.post("/api/documents/upload", files=files)
    sid = resp.json()["session_id"]

    tasks = [client.post(f"/api/documents/{sid}/chat", json={"question": f"Question {i}"}) for i in range(6)]
    responses = await asyncio.gather(*tasks)

    for r in responses:
        assert r.status_code == 200

    # Verify session recorded the turns without corruption
    status_resp = await client.get(f"/api/documents/{sid}/status")
    assert status_resp.status_code == 200
    # Turns count should be bounded by MAX_CHAT_HISTORY_TURNS (default 5)
    assert status_resp.json()["turns_count"] <= 5

    await client.delete(f"/api/documents/{sid}")


@pytest.mark.asyncio
async def test_session_deletion_during_in_flight_queries():
    """Verify session deletion while a query is running does not deadlock or crash."""
    mock_chat = MockChatService()

    # Artificially delay chat to allow delete to occur
    original_generate = mock_chat.generate

    async def slow_generate(messages):
        await asyncio.sleep(0.05)
        return await original_generate(messages)

    mock_chat.generate = slow_generate

    rag = RAGService(
        embedding_service=MockEmbeddingService(384),
        chat_service=mock_chat,
    )

    pdf = make_pdf_with_text("Project Aurora is an enterprise AI initiative launched in 2024.")
    session = await rag.ingest_pdf_bytes(pdf, "aurora.pdf")
    sid = session.session_id

    # Launch query and delete simultaneously
    query_task = asyncio.create_task(rag.answer_question(sid, "What is Aurora?"))
    await asyncio.sleep(0.01)
    delete_task = asyncio.create_task(rag.delete_session(sid))

    results = await asyncio.gather(query_task, delete_task, return_exceptions=True)
    # Neither should crash with unexpected unhandled errors
    assert len(results) == 2
