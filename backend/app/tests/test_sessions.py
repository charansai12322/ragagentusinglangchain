"""Session service lifecycle, TTL expiration, and capacity tests."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from backend.app.core.config import settings
from backend.app.core.errors import SessionNotFoundError
from backend.app.services.session_service import SessionService


@pytest.mark.asyncio
async def test_session_lifecycle():
    """Verify session creation, updating, and manual deletion."""
    svc = SessionService()
    session = await svc.create_session("report.pdf")
    assert session.status == "processing"

    await svc.update_session_ready(session.session_id, total_pages=5, chunk_count=12)
    ready = await svc.get_session(session.session_id)
    assert ready.status == "ready"
    assert ready.total_pages == 5

    deleted = await svc.delete_session(session.session_id)
    assert deleted is True

    with pytest.raises(SessionNotFoundError):
        await svc.get_session(session.session_id)


@pytest.mark.asyncio
async def test_session_ttl_expiration():
    """Verify session expires and is pruned when past TTL."""
    svc = SessionService()
    session = await svc.create_session("report.pdf")

    # Manually backdate expiration to simulate expired TTL
    session.expires_at = datetime.now(UTC) - timedelta(minutes=10)

    # Accessing expired session raises SessionNotFoundError and removes it
    with pytest.raises(SessionNotFoundError):
        await svc.get_session(session.session_id)

    assert await svc.get_active_session_count() == 0


@pytest.mark.asyncio
async def test_session_capacity_eviction(monkeypatch):
    """Verify that exceeding MAX_SESSIONS evicts the oldest inactive session."""
    monkeypatch.setattr(settings, "MAX_SESSIONS", 3)
    svc = SessionService()

    s1 = await svc.create_session("doc1.pdf")
    await asyncio.sleep(0.02)
    s2 = await svc.create_session("doc2.pdf")
    await asyncio.sleep(0.02)
    s3 = await svc.create_session("doc3.pdf")
    await asyncio.sleep(0.02)

    # Access s1 so s1 is refreshed and s2 becomes the oldest
    await svc.get_session(s1.session_id)
    await asyncio.sleep(0.02)

    # Creating s4 should evict s2 (oldest last_accessed)
    s4 = await svc.create_session("doc4.pdf")

    with pytest.raises(SessionNotFoundError):
        await svc.get_session(s2.session_id)

    # s1, s3, s4 should remain
    assert (await svc.get_session(s1.session_id)).session_id == s1.session_id
    assert (await svc.get_session(s3.session_id)).session_id == s3.session_id
    assert (await svc.get_session(s4.session_id)).session_id == s4.session_id


@pytest.mark.asyncio
async def test_bounded_conversation_history():
    """Verify conversation history is bounded to configured max turns."""
    svc = SessionService()
    session = await svc.create_session("chat_test.pdf")

    for i in range(10):
        await svc.record_chat_turn(session.session_id, f"Q{i}", f"A{i}")

    s = await svc.get_session(session.session_id)
    # MAX_CHAT_HISTORY_TURNS is 5, each turn is 2 messages (user + assistant) -> 10 messages max
    assert len(s.history) <= settings.MAX_CHAT_HISTORY_TURNS * 2
    assert s.history[-2]["content"] == "Q9"
    assert s.history[-1]["content"] == "A9"


@pytest.mark.asyncio
async def test_eviction_callback_invoked_on_capacity(monkeypatch):
    """Verify eviction callback is triggered with the evicted session ID."""
    monkeypatch.setattr(settings, "MAX_SESSIONS", 2)
    evicted_ids = []

    svc = SessionService(on_evict=lambda sid: evicted_ids.append(sid))

    s1 = await svc.create_session("doc1.pdf")
    await asyncio.sleep(0.01)
    await svc.create_session("doc2.pdf")
    await asyncio.sleep(0.01)

    # Creating s3 should evict s1 and invoke callback
    await svc.create_session("doc3.pdf")

    assert len(evicted_ids) == 1
    assert evicted_ids[0] == s1.session_id


@pytest.mark.asyncio
async def test_repeated_deletion():
    """Verify repeated deletion returns False gracefully without error."""
    svc = SessionService()
    s = await svc.create_session("doc.pdf")
    first_del = await svc.delete_session(s.session_id)
    assert first_del is True

    second_del = await svc.delete_session(s.session_id)
    assert second_del is False
