"""Health check endpoint and configuration tests."""

import pytest
from httpx import AsyncClient

from backend.app.core.config import Settings


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verify health check responds with 200 and accurate system metadata."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "groq_configured" in data
    assert "groq_model" in data
    assert "embedding_model" in data
    assert "active_sessions" in data
    assert "X-Request-ID" in response.headers


def test_settings_validation():
    """Verify Settings object handles defaults and CORS parsing correctly."""
    s = Settings(
        GROQ_API_KEY="PASTE_YOUR_GROQ_API_KEY_HERE",
        CORS_ORIGINS='["http://localhost:5173", "http://example.com"]',
    )
    assert not s.is_groq_configured
    assert "http://example.com" in s.CORS_ORIGINS
    assert s.max_upload_size_bytes == 15 * 1024 * 1024
