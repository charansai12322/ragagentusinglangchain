"""Offline tests for Groq provider failure modes and error mapping."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.core.errors import (
    ConfigurationError,
    RateLimitExceededError,
    UpstreamProviderError,
)
from backend.app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_groq_401_auth_error_mapping():
    """Verify 401/invalid API key exception maps to GROQ_AUTH_ERROR."""
    service = ChatService()
    mock_llm = MagicMock()
    auth_err_msg = "Error code: 401 - {'error': {'message': 'Invalid API Key'}}"
    mock_llm.ainvoke = AsyncMock(side_effect=Exception(auth_err_msg))
    service._llm = mock_llm

    with pytest.raises(UpstreamProviderError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert err.code == "GROQ_AUTH_ERROR"
    assert err.status_code == 502
    assert "Invalid Groq API key" in err.message


@pytest.mark.asyncio
async def test_groq_429_rate_limit_mapping():
    """Verify 429 rate limit exception maps to RATE_LIMIT_EXCEEDED."""
    service = ChatService()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("Error code: 429 - rate_limit_exceeded: TPM limit reached"))
    service._llm = mock_llm

    with pytest.raises(RateLimitExceededError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert err.code == "RATE_LIMIT_EXCEEDED"
    assert err.status_code == 429


@pytest.mark.asyncio
async def test_groq_timeout_mapping():
    """Verify timeout exception maps to LLM_TIMEOUT with 504 Gateway Timeout."""
    service = ChatService()
    mock_llm = MagicMock()

    async def slow_invoke(*args, **kwargs):
        raise TimeoutError("Call timed out")

    mock_llm.ainvoke = slow_invoke
    service._llm = mock_llm

    with pytest.raises(UpstreamProviderError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert err.code == "LLM_TIMEOUT"
    assert err.status_code == 504


@pytest.mark.asyncio
async def test_groq_model_unavailable_mapping():
    """Verify decommissioned/unavailable model exception maps to GROQ_MODEL_UNAVAILABLE."""
    service = ChatService()
    mock_llm = MagicMock()
    not_found_msg = "model_not_found: The model does not exist or has been decommissioned"
    mock_llm.ainvoke = AsyncMock(side_effect=Exception(not_found_msg))
    service._llm = mock_llm

    with pytest.raises(UpstreamProviderError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert err.code == "GROQ_MODEL_UNAVAILABLE"
    assert err.status_code == 502


@pytest.mark.asyncio
async def test_groq_generic_upstream_error_mapping():
    """Verify generic provider error maps to GROQ_UPSTREAM_ERROR without leaking details."""
    service = ChatService()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("Internal server connection dropped unexpectedly"))
    service._llm = mock_llm

    with pytest.raises(UpstreamProviderError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert err.code == "GROQ_UPSTREAM_ERROR"
    assert err.status_code == 502
    assert "RuntimeError" in err.message


@pytest.mark.asyncio
async def test_groq_unconfigured_key_mapping():
    """Verify missing/placeholder key raises ConfigurationError."""
    service = ChatService()
    service._llm = None
    with pytest.raises(ConfigurationError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])
    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "CONFIGURATION_ERROR"


@pytest.mark.asyncio
async def test_groq_secret_not_leaked_in_exception():
    """Verify simulated API keys in raw error strings are never leaked in client-facing messages."""
    service = ChatService()
    mock_llm = MagicMock()
    secret_key = "gsk_supersecretkey123456789"
    mock_llm.ainvoke = AsyncMock(side_effect=Exception(f"Failed connection using key {secret_key}"))
    service._llm = mock_llm

    with pytest.raises(UpstreamProviderError) as exc_info:
        await service.generate([{"role": "user", "content": "test"}])

    err = exc_info.value
    assert secret_key not in err.message
