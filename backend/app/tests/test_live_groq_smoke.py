"""Single minimal live Groq smoke test. Strictly opt-in via marker."""

import time

import pytest

from backend.app.core.config import settings
from backend.app.services.chat_service import ChatService


@pytest.mark.live_provider
@pytest.mark.asyncio
async def test_live_groq_single_call_smoke():
    """
    Opt-in live provider verification: makes exactly 1 minimal call to the real configured Groq model.
    Does not run during standard offline test runs.
    """
    if not settings.is_groq_configured:
        pytest.skip("GROQ_API_KEY is not configured in backend/.env; skipping live provider smoke test.")

    service = ChatService()
    t0 = time.perf_counter()
    prompt = [{"role": "user", "content": "Respond with only the single word: PONG"}]
    response = await service.generate(prompt)
    duration = time.perf_counter() - t0

    assert len(response.strip()) > 0
    assert "PONG" in response.upper()
    log_msg = f"[LIVE GROQ SUCCESS] Model '{settings.GROQ_MODEL_NAME}' in {duration:.2f}s: '{response.strip()}'"
    print(f"\n{log_msg}")
