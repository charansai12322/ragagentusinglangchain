"""Session isolation, retrieval quality, and metadata tests."""

import pytest

from backend.app.services.embedding_service import MockEmbeddingService
from backend.app.services.pdf_service import PDFService
from backend.app.services.rag_service import RAGService
from backend.app.tests.conftest import make_pdf_with_text


@pytest.mark.asyncio
async def test_session_isolation():
    """
    CRITICAL TEST: Ensure two concurrent document sessions cannot contaminate each other's vectors.
    Session A: Document about Transformers.
    Session B: Document about Photosynthesis.
    """
    pdf_a = make_pdf_with_text("The Transformer attention mechanism allows global dependencies.")
    pdf_b = make_pdf_with_text("Photosynthesis in plants converts solar light into chemical energy.")

    rag = RAGService(embedding_service=MockEmbeddingService(384))

    # Ingest both
    session_a = await rag.ingest_pdf_bytes(pdf_a, "transformers.pdf")
    session_b = await rag.ingest_pdf_bytes(pdf_b, "plants.pdf")

    # Search in session A
    q_vec = rag.embedding_service.embed_query("attention")
    results_a = rag.vector_service.search(session_a.session_id, q_vec, top_k=2)
    assert len(results_a) > 0
    for chunk in results_a:
        assert "Transformer" in chunk["text"]
        assert "Photosynthesis" not in chunk["text"]

    # Search in session B
    results_b = rag.vector_service.search(session_b.session_id, q_vec, top_k=2)
    assert len(results_b) > 0
    for chunk in results_b:
        assert "Photosynthesis" in chunk["text"]
        assert "Transformer" not in chunk["text"]

    # Search with invalid session returns empty list
    results_none = rag.vector_service.search("invalid-session-uuid", q_vec, top_k=2)
    assert results_none == []


@pytest.mark.asyncio
async def test_page_number_traceability(multi_page_pdf_bytes: bytes):
    """Ensure page numbers are accurately retained in chunks."""
    pdf_service = PDFService()
    pages, chunks = pdf_service.parse_and_chunk(multi_page_pdf_bytes, "multipage.pdf", "test-session")
    assert pages == 2
    assert any(c["page"] == 1 for c in chunks)
    assert any(c["page"] == 2 for c in chunks)


def test_vector_service_top_k_bounding():
    """Verify search strictly respects top_k limit."""
    from backend.app.services.vector_service import VectorService

    vs = VectorService()
    chunks = [{"chunk_id": i, "text": f"Chunk text {i}", "page": 1} for i in range(10)]
    # 10 orthogonal or standard vectors of dim 4
    embeddings = [[1.0 if j == i % 4 else 0.0 for j in range(4)] for i in range(10)]
    vs.create_session_index("session-topk", chunks, embeddings)

    results = vs.search("session-topk", query_vector=[1.0, 0.0, 0.0, 0.0], top_k=3)
    assert len(results) == 3


def test_vector_service_dimension_mismatch_safety():
    """Verify query vector with dimension mismatch is safely handled without unhandled exceptions."""
    from backend.app.services.vector_service import VectorService

    vs = VectorService()
    chunks = [{"chunk_id": 0, "text": "Some text", "page": 1}]
    embeddings = [[0.1, 0.2, 0.3, 0.4]]  # dim 4
    vs.create_session_index("session-dim", chunks, embeddings)

    # Search with dim 8 (mismatch)
    results = vs.search("session-dim", query_vector=[0.1] * 8, top_k=2)
    assert results == []


def test_vector_service_deletion_cleanup():
    """Verify deleting session releases index."""
    from backend.app.services.vector_service import VectorService

    vs = VectorService()
    chunks = [{"chunk_id": 0, "text": "Sample text", "page": 1}]
    embeddings = [[0.1, 0.2, 0.3]]
    vs.create_session_index("session-del", chunks, embeddings)
    assert vs.has_session("session-del")

    deleted = vs.delete_session_index("session-del")
    assert deleted is True
    assert not vs.has_session("session-del")
    assert vs.search("session-del", [0.1, 0.2, 0.3]) == []


@pytest.mark.asyncio
async def test_relevance_discrimination_multi_topic():
    """
    Verify that cosine retrieval properly discriminates and ranks the most relevant topic first.
    We test using real FastEmbed embeddings.
    """
    from backend.app.services.embedding_service import EmbeddingService
    from backend.app.services.vector_service import VectorService

    embed_svc = EmbeddingService()
    vector_svc = VectorService()

    topic1 = "Project Aurora is an enterprise AI software platform headquartered in Hyderabad, India."
    topic2 = "Marine biology studies the diverse ecosystem of coral reefs in the Pacific Ocean."
    topic3 = "Quantum computing relies on superposition and quantum entanglement to execute parallel calculations."

    chunks = [
        {"chunk_id": 0, "text": topic1, "page": 1},
        {"chunk_id": 1, "text": topic2, "page": 2},
        {"chunk_id": 2, "text": topic3, "page": 3},
    ]

    embeddings = embed_svc.embed_documents([topic1, topic2, topic3])
    vector_svc.create_session_index("session-topics", chunks, embeddings)

    # Query about Hyderabad AI
    q_vec = embed_svc.embed_query("Where is the headquarters of Project Aurora?")
    results = vector_svc.search("session-topics", q_vec, top_k=2)

    assert len(results) == 2
    # Topic 1 must be ranked #1 with highest score
    assert results[0]["chunk_id"] == 0
    assert "Hyderabad" in results[0]["text"]
    assert results[0]["score"] > results[1]["score"]
