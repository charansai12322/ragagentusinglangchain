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


@pytest.mark.asyncio
async def test_cors_production_vercel_origin(client: AsyncClient):
    """Verify production Vercel frontend origin receives Access-Control-Allow-Origin header."""
    headers = {"Origin": "https://ragagentusinglangchain.vercel.app"}
    response = await client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://ragagentusinglangchain.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "X-Request-ID" in response.headers.get("access-control-expose-headers", "")


@pytest.mark.asyncio
async def test_cors_preflight_options_request(client: AsyncClient):
    """Verify OPTIONS preflight request succeeds with CORS headers for production Vercel frontend."""
    headers = {
        "Origin": "https://ragagentusinglangchain.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = await client.options("/api/documents/upload", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://ragagentusinglangchain.vercel.app"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_cors_unapproved_origin_denied(client: AsyncClient):
    """Verify an unapproved origin is NOT granted Access-Control-Allow-Origin."""
    headers = {"Origin": "https://malicious-unapproved-site.com"}
    response = await client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_cors_on_error_response(client: AsyncClient):
    """Verify that error responses (e.g. 404) also retain CORS headers for approved origins."""
    headers = {"Origin": "https://ragagentusinglangchain.vercel.app"}
    response = await client.get("/api/documents/non-existent-session-uuid/status", headers=headers)
    assert response.status_code == 404
    assert response.headers.get("access-control-allow-origin") == "https://ragagentusinglangchain.vercel.app"


def test_settings_validation():
    """Verify Settings object handles defaults and CORS parsing correctly."""
    s = Settings(
        GROQ_API_KEY="PASTE_YOUR_GROQ_API_KEY_HERE",
        CORS_ORIGINS='["http://localhost:5173", "http://example.com"]',
    )
    assert not s.is_groq_configured
    assert "http://example.com" in s.CORS_ORIGINS
    assert "https://ragagentusinglangchain.vercel.app" in s.CORS_ORIGINS
    assert s.max_upload_size_bytes == 15 * 1024 * 1024
