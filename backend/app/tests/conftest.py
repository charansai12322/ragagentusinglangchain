"""Pytest fixtures and test environment configuration."""

import io
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pypdf import PdfWriter

from backend.app.main import app_state, create_app
from backend.app.services.chat_service import MockChatService
from backend.app.services.embedding_service import MockEmbeddingService
from backend.app.services.rag_service import RAGService


def make_pdf_with_text(text: str) -> bytes:
    """Create a valid single-page PDF containing the provided text string."""
    escaped = text.replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT\n/F1 12 Tf\n50 700 Td\n({escaped}) Tj\nET"
    stream_len = len(stream_content.encode("latin-1"))

    pdf_template = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{stream_content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
{"0000000000 65535 f "}
{"0000000009 00000 n "}
{"0000000058 00000 n "}
{"0000000115 00000 n "}
{"0000000244 00000 n "}
{"0000000350 00000 n "}
trailer
<< /Size 6 /Root 1 0 R >>
startxref
450
%%EOF"""
    return pdf_template.encode("latin-1")


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    """Valid text-rich document fixture."""
    text = (
        "The Transformer is a deep learning architecture introduced in 2017. "
        "It relies entirely on an attention mechanism to model dependencies regardless of distance. "
        "Multi-head attention projects queries, keys, and values into multiple representation subspaces. "
        "The model achieves state-of-the-art results on machine translation tasks."
    )
    return make_pdf_with_text(text)


@pytest.fixture
def multi_page_pdf_bytes() -> bytes:
    """Valid two-page PDF fixture."""
    page1 = make_pdf_with_text("Page 1 discusses the encoder stack and self-attention layers in Transformers.")
    page2 = make_pdf_with_text("Page 2 discusses the decoder stack and masked multi-head attention mechanisms.")

    writer = PdfWriter()
    writer.append(io.BytesIO(page1))
    writer.append(io.BytesIO(page2))
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def empty_pdf_bytes() -> bytes:
    """PDF with no extractable text."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def corrupt_pdf_bytes() -> bytes:
    """Corrupt bytes with fake PDF header."""
    return b"%PDF-1.4\nCorrupted binary garbage that cannot be parsed by pypdf!"


@pytest.fixture
def encrypted_pdf_bytes(valid_pdf_bytes: bytes) -> bytes:
    """Password-encrypted PDF fixture."""
    writer = PdfWriter()
    writer.append(io.BytesIO(valid_pdf_bytes))
    writer.encrypt("super_secret_password")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def mock_rag_service() -> RAGService:
    """RAG service configured with deterministic mock embedding and chat services."""
    return RAGService(
        embedding_service=MockEmbeddingService(dimension=384),
        chat_service=MockChatService(answer_prefix="Grounded response"),
    )


@pytest_asyncio.fixture
async def client(mock_rag_service: RAGService) -> AsyncGenerator[AsyncClient, None]:
    """Test AsyncClient configured with mock RAG service."""
    app_state.rag_service = mock_rag_service
    app = create_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
