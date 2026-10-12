"""Thread-safe session lifecycle and conversational memory management."""

import asyncio
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from backend.app.core.config import settings
from backend.app.core.errors import SessionNotFoundError
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


def utc_now() -> datetime:
    """Helper returning current UTC datetime."""
    return datetime.now(UTC)


class DocumentSession:
    """State model for an active document session."""

    def __init__(self, session_id: str, filename: str):
        now = utc_now()
        self.session_id = session_id
        self.filename = filename
        self.status = "processing"
        self.total_pages = 0
        self.chunk_count = 0
        self.created_at = now
        self.last_accessed = now
        self.expires_at = now + timedelta(minutes=settings.SESSION_TTL_MINUTES)
        self.history: list[dict[str, str]] = []

    def touch(self) -> None:
        """Update last accessed time and extend expiration window."""
        now = utc_now()
        self.last_accessed = now
        self.expires_at = now + timedelta(minutes=settings.SESSION_TTL_MINUTES)

    def is_expired(self) -> bool:
        """Check if the session has exceeded idle TTL."""
        return utc_now() > self.expires_at

    def add_turn(self, user_question: str, assistant_answer: str) -> None:
        """Record a conversation turn, keeping history bounded."""
        self.touch()
        self.history.append({"role": "user", "content": user_question})
        self.history.append({"role": "assistant", "content": assistant_answer})

        # Keep history bounded to MAX_CHAT_HISTORY_TURNS (each turn is 2 messages)
        max_messages = settings.MAX_CHAT_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]


class SessionService:
    """Manages active document sessions with concurrency locking and TTL eviction."""

    def __init__(self, on_evict: Callable[[str], None] | None = None):
        self._sessions: dict[str, DocumentSession] = {}
        self._lock = asyncio.Lock()
        self._on_evict = on_evict

    def set_eviction_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback invoked when a session is pruned or capacity-evicted."""
        self._on_evict = callback

    def _notify_evicted(self, session_id: str) -> None:
        """Notify listener of session eviction."""
        if self._on_evict:
            try:
                self._on_evict(session_id)
            except Exception as e:
                logger.warning("Error notifying eviction for session %s: %s", session_id, e)

    async def create_session(self, filename: str) -> DocumentSession:
        """Create a new document session, enforcing session capacity."""
        async with self._lock:
            # Purge expired sessions first
            self._purge_expired_sessions()

            # Evict oldest session if at max capacity
            if len(self._sessions) >= settings.MAX_SESSIONS:
                oldest_id = min(self._sessions.keys(), key=lambda sid: self._sessions[sid].last_accessed)
                logger.info("Evicting oldest session %s due to capacity limit", oldest_id)
                del self._sessions[oldest_id]
                self._notify_evicted(oldest_id)

            session_id = str(uuid.uuid4())
            session = DocumentSession(session_id=session_id, filename=filename)
            self._sessions[session_id] = session
            logger.info("Created session %s for file '%s'", session_id, filename)
            return session

    async def get_session(self, session_id: str) -> DocumentSession:
        """Retrieve active session, verifying expiration."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionNotFoundError(f"Session '{session_id}' not found.")

            if session.is_expired():
                del self._sessions[session_id]
                self._notify_evicted(session_id)
                logger.info("Session %s expired and was evicted on access", session_id)
                raise SessionNotFoundError(f"Session '{session_id}' has expired.")

            session.touch()
            return session

    async def update_session_ready(self, session_id: str, total_pages: int, chunk_count: int) -> None:
        """Mark session as ready with processed stats."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = "ready"
                session.total_pages = total_pages
                session.chunk_count = chunk_count
                session.touch()

    async def update_session_failed(self, session_id: str) -> None:
        """Mark session as failed."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = "failed"

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info("Manually deleted session %s", session_id)
                return True
            return False

    async def record_chat_turn(self, session_id: str, user_question: str, assistant_answer: str) -> None:
        """Record turn under lock."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.add_turn(user_question, assistant_answer)

    async def get_active_session_count(self) -> int:
        """Return count of unexpired active sessions."""
        async with self._lock:
            self._purge_expired_sessions()
            return len(self._sessions)

    def _purge_expired_sessions(self) -> list[str]:
        """Internal helper to prune all expired sessions."""
        expired_ids = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired_ids:
            del self._sessions[sid]
            self._notify_evicted(sid)
            logger.info("Purged expired session %s", sid)
        return expired_ids

    async def purge_expired(self) -> list[str]:
        """Async public method for background janitor."""
        async with self._lock:
            return self._purge_expired_sessions()
