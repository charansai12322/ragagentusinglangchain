"""Lightweight CPU-based FastEmbed embedding service."""

import time
from typing import Protocol

import numpy as np
from fastembed import TextEmbedding

from backend.app.core.config import settings
from backend.app.core.errors import UpstreamProviderError
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingServiceInterface(Protocol):
    """Interface for embedding services to support swapping or mocking."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...

    @property
    def dimension(self) -> int: ...


class EmbeddingService:
    """Singleton service wrapping FastEmbed ONNX embeddings."""

    _instance: "EmbeddingService | None" = None
    _model: TextEmbedding | None = None
    _dimension: int = 384

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self) -> None:
        """Initialize the FastEmbed ONNX model once."""
        t0 = time.perf_counter()
        model_name = settings.EMBEDDING_MODEL_NAME
        logger.info("Initializing FastEmbed embedding model: %s", model_name)
        try:
            self._model = TextEmbedding(model_name=model_name)
            init_duration = time.perf_counter() - t0
            # Test dimension with a single probe token
            probe = list(self._model.embed(["probe"]))
            self._dimension = len(probe[0])
            logger.info(
                "FastEmbed model '%s' initialized in %.3fs (dimension: %d)",
                model_name,
                init_duration,
                self._dimension,
            )
        except Exception as e:
            logger.error("Failed to initialize FastEmbed model '%s': %s", model_name, e)
            raise UpstreamProviderError(f"Could not initialize embedding engine: {e}") from e

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized dense embeddings for document chunks."""
        if not texts:
            return []

        if not self._model:
            raise UpstreamProviderError("Embedding model is not initialized.")

        try:
            t0 = time.perf_counter()
            generator = self._model.embed(texts)
            results = [arr.tolist() if isinstance(arr, np.ndarray) else list(arr) for arr in generator]
            duration = time.perf_counter() - t0
            logger.debug("Embedded %d chunks in %.3fs", len(texts), duration)
            return results
        except Exception as e:
            logger.error("Error during document embedding: %s", e)
            raise UpstreamProviderError(f"Failed to generate document embeddings: {e}") from e

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding vector for a single search query."""
        if not text.strip():
            return [0.0] * self._dimension

        if not self._model:
            raise UpstreamProviderError("Embedding model is not initialized.")

        try:
            t0 = time.perf_counter()
            generator = self._model.embed([text])
            vector = next(generator)
            duration = time.perf_counter() - t0
            logger.debug("Embedded query in %.3fs", duration)
            return vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        except Exception as e:
            logger.error("Error during query embedding: %s", e)
            raise UpstreamProviderError(f"Failed to generate query embedding: {e}") from e


class MockEmbeddingService:
    """Deterministic mock embedding service for unit and integration testing."""

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            # Deterministic hash-based mock embedding
            seed = sum(ord(c) for c in text) % 1000
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(self._dim)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
