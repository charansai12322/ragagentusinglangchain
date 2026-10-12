"""In-memory session-isolated vector indexing and cosine retrieval service."""

from typing import Any

import numpy as np

from backend.app.core.errors import DocumentProcessingError
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class SessionVectorIndex:
    """Isolated in-memory vector store for a single document session."""

    def __init__(self, session_id: str, chunks: list[dict[str, Any]], embeddings: list[list[float]]):
        self.session_id = session_id
        self.chunks = chunks
        if not embeddings:
            raise DocumentProcessingError("Cannot create vector index with empty embeddings.")

        matrix = np.array(embeddings, dtype=np.float32)
        # Normalize each embedding row to unit length for fast cosine similarity dot products
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        self.matrix = matrix / norms

    def search(self, query_vector: list[float], top_k: int = 4) -> list[dict[str, Any]]:
        """Retrieve top-k most similar chunks using cosine similarity."""
        if len(self.chunks) == 0:
            return []

        if len(query_vector) != self.matrix.shape[1]:
            logger.warning(
                "Query vector dimension (%d) does not match index dimension (%d)",
                len(query_vector),
                self.matrix.shape[1],
            )
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            q_norm = 1e-10
        q = q / q_norm

        # Matrix-vector dot product computes cosine similarities for all chunks in 1 operation
        scores = self.matrix @ q

        # Select top-k indices
        k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(scores[idx])
            results.append(chunk)

        return results


class VectorService:
    """Registry maintaining session-isolated in-memory vector indexes."""

    def __init__(self):
        self._indexes: dict[str, SessionVectorIndex] = {}

    def create_session_index(
        self,
        session_id: str,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Create and store an isolated vector index scoped strictly to session_id."""
        if session_id in self._indexes:
            logger.info("Replacing existing vector index for session %s", session_id)

        index = SessionVectorIndex(session_id=session_id, chunks=chunks, embeddings=embeddings)
        self._indexes[session_id] = index
        logger.info(
            "Created vector index for session %s with %d chunks (dim: %d)",
            session_id,
            len(chunks),
            index.matrix.shape[1],
        )

    def search(self, session_id: str, query_vector: list[float], top_k: int = 4) -> list[dict[str, Any]]:
        """Perform similarity search within the isolated index of session_id."""
        index = self._indexes.get(session_id)
        if not index:
            logger.warning("No vector index found for session %s", session_id)
            return []
        return index.search(query_vector=query_vector, top_k=top_k)

    def delete_session_index(self, session_id: str) -> bool:
        """Evict and free memory for a session index."""
        if session_id in self._indexes:
            del self._indexes[session_id]
            logger.info("Deleted vector index for session %s", session_id)
            return True
        return False

    def has_session(self, session_id: str) -> bool:
        """Check if an index exists for session_id."""
        return session_id in self._indexes

    def get_chunk_count(self, session_id: str) -> int:
        """Return total chunks indexed for session_id."""
        index = self._indexes.get(session_id)
        return len(index.chunks) if index else 0
