"""PDF ingestion, parsing, page-limit validation, and text chunking."""

import io
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import EmptyFileError, PdfReadError

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingError
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class PDFService:
    """Service responsible for validating, parsing, and chunking PDF documents."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def parse_and_chunk(
        self,
        pdf_bytes: bytes,
        filename: str,
        session_id: str,
        max_pages: int | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        """
        Parse raw PDF bytes and chunk text while preserving page-level traceability.
        Returns (total_pages, list_of_chunks).
        """
        effective_max_pages = max_pages or settings.MAX_PDF_PAGES

        try:
            stream = io.BytesIO(pdf_bytes)
            reader = PdfReader(stream)
        except (PdfReadError, EmptyFileError) as e:
            logger.warning("Failed to parse PDF bytes: %s", e)
            raise DocumentProcessingError(f"Corrupt or malformed PDF: {e}") from e
        except Exception as e:
            logger.warning("Unexpected error opening PDF: %s", e)
            raise DocumentProcessingError(f"Cannot read PDF document: {e}") from e

        if reader.is_encrypted:
            try:
                # Attempt empty password decryption
                decrypted = reader.decrypt("")
                if not decrypted:
                    raise DocumentProcessingError("PDF is password-protected. Encrypted documents are not supported.")
            except Exception as e:
                raise DocumentProcessingError(
                    "PDF is password-protected. Encrypted documents are not supported."
                ) from e

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise DocumentProcessingError("PDF contains 0 pages.")

        if total_pages > effective_max_pages:
            raise DocumentProcessingError(
                f"Document has {total_pages} pages, which exceeds the maximum limit of {effective_max_pages} pages."
            )

        chunks: list[dict[str, Any]] = []
        total_extracted_chars = 0
        chunk_counter = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                logger.warning("Failed to extract text from page %d of %s: %s", page_idx, filename, e)
                page_text = ""

            clean_text = page_text.strip()
            total_extracted_chars += len(clean_text)

            if not clean_text:
                continue

            # Split page text into chunks
            sub_splits = self.splitter.split_text(clean_text)
            for split_text in sub_splits:
                if not split_text.strip():
                    continue
                chunks.append(
                    {
                        "chunk_id": chunk_counter,
                        "session_id": session_id,
                        "page": page_idx,
                        "total_pages": total_pages,
                        "source": filename,
                        "text": split_text.strip(),
                    }
                )
                chunk_counter += 1

        # Check for scanned or empty documents
        if total_extracted_chars < 50 or not chunks:
            raise DocumentProcessingError(
                "Document appears to be scanned or contains no extractable text. OCR is not supported in this version."
            )

        logger.info(
            "Parsed PDF '%s' for session %s: %d pages, %d chunks, %d chars",
            filename,
            session_id,
            total_pages,
            len(chunks),
            total_extracted_chars,
        )

        return total_pages, chunks
