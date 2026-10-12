"""Groq LLM chat integration with error mapping and concurrency control."""

import asyncio
import time
from typing import Protocol

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.app.core.config import settings
from backend.app.core.errors import (
    ConfigurationError,
    RateLimitExceededError,
    UpstreamProviderError,
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ChatServiceInterface(Protocol):
    """Interface for LLM generation backends."""

    async def generate(self, messages: list[dict[str, str]]) -> str: ...


class ChatService:
    """Service wrapping LangChain ChatGroq with bounds and mapped error handling."""

    def __init__(self):
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_LLM_REQUESTS)
        self._llm: ChatGroq | None = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize reusable ChatGroq client if key is present."""
        if settings.is_groq_configured:
            try:
                self._llm = ChatGroq(
                    model_name=settings.GROQ_MODEL_NAME,
                    api_key=settings.GROQ_API_KEY,
                    request_timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=1,  # Prevent retry storms; handle transient failures explicitly
                )
                logger.info("Initialized ChatGroq with model '%s'", settings.GROQ_MODEL_NAME)
            except Exception as e:
                logger.error("Failed to initialize ChatGroq: %s", e)
                self._llm = None
        else:
            logger.warning("Groq API key not configured. Live LLM calls will return ConfigurationError.")
            self._llm = None

    async def generate(self, messages: list[dict[str, str]]) -> str:
        """
        Invoke the Groq model with mapped error handling, timeout, and concurrency limits.
        """
        if not settings.is_groq_configured or self._llm is None:
            raise ConfigurationError(
                "GROQ_API_KEY is not configured. Please supply a valid Groq API key in backend/.env."
            )

        # Convert dict format to LangChain messages
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))

        t0 = time.perf_counter()
        try:
            async with self._semaphore:
                # Use asyncio.wait_for to guarantee adherence to LLM_TIMEOUT_SECONDS
                response = await asyncio.wait_for(
                    self._llm.ainvoke(langchain_messages),
                    timeout=settings.LLM_TIMEOUT_SECONDS + 2.0,
                )
                duration = time.perf_counter() - t0
                logger.info(
                    "Groq model '%s' responded in %.3fs (%d input messages)",
                    settings.GROQ_MODEL_NAME,
                    duration,
                    len(messages),
                )
                content = response.content
                if isinstance(content, list):
                    # Handle list-based content structures
                    return "".join(part if isinstance(part, str) else str(part) for part in content)
                return str(content)

        except TimeoutError as e:
            logger.error("Groq request timed out after %.1fs", settings.LLM_TIMEOUT_SECONDS)
            raise UpstreamProviderError(
                f"Groq generation timed out after {settings.LLM_TIMEOUT_SECONDS}s.",
                code="LLM_TIMEOUT",
                status_code=504,
            ) from e

        except Exception as e:
            err_str = str(e).lower()
            logger.error("Groq generation error: %s", e)

            if "401" in err_str or "invalid_api_key" in err_str or "unauthorized" in err_str:
                raise UpstreamProviderError(
                    "Invalid Groq API key. Please check your credentials.",
                    code="GROQ_AUTH_ERROR",
                    status_code=502,
                ) from e
            elif "429" in err_str or "rate_limit" in err_str or "resource_exhausted" in err_str:
                raise RateLimitExceededError("Groq rate limit reached. Please retry in a moment.") from e
            elif "model_not_found" in err_str or "decommissioned" in err_str or "not available" in err_str:
                raise UpstreamProviderError(
                    f"Model '{settings.GROQ_MODEL_NAME}' is not available on Groq.",
                    code="GROQ_MODEL_UNAVAILABLE",
                    status_code=502,
                ) from e
            else:
                raise UpstreamProviderError(
                    f"Upstream Groq error: {type(e).__name__}",
                    code="GROQ_UPSTREAM_ERROR",
                    status_code=502,
                ) from e


class MockChatService:
    """Deterministic mock LLM service for testing without live Groq API credentials."""

    def __init__(self, answer_prefix: str = "Mock answer based on context"):
        self.answer_prefix = answer_prefix
        self.call_count = 0

    async def generate(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        # Extract last user query
        user_queries = [m["content"] for m in messages if m.get("role") == "user"]
        query = user_queries[-1] if user_queries else "No question"
        return f"{self.answer_prefix} for '{query}' [Page 1]."
