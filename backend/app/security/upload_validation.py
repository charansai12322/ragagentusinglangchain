"""Upload validation and filename sanitization logic."""

import re
from pathlib import Path

from backend.app.core.errors import DocumentProcessingError, SecurityValidationError


def sanitize_filename(filename: str | None) -> str:
    """Sanitize user-provided filename to prevent directory traversal and null bytes."""
    if not filename:
        return "uploaded_document.pdf"

    # Strip null bytes and whitespace
    clean = filename.replace("\x00", "").strip()

    # Extract base name across both POSIX and Windows path separators
    clean_posix = clean.replace("\\", "/")
    base = Path(clean_posix).name

    # Remove unsafe characters
    base = re.sub(r"[^a-zA-Z0-9_\-\. ]", "_", base)
    # Strip dangerous leading/trailing dots and spaces
    base = base.strip(". ")

    if not base:
        base = "document"

    if not base.lower().endswith(".pdf"):
        base += ".pdf"

    return base


def validate_pdf_bytes(content: bytes, max_size_bytes: int) -> None:
    """
    Validate raw bytes:
    1. Not empty.
    2. Does not exceed byte limit.
    3. Has valid PDF magic header (%PDF-).
    """
    if not content:
        raise DocumentProcessingError("Uploaded file is empty (0 bytes).")

    if len(content) > max_size_bytes:
        raise SecurityValidationError(
            f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {max_size_bytes} bytes."
        )

    # PDF header must appear near the beginning
    # (typically at index 0, but spec permits comments within first 1024 bytes)
    header_sample = content[:1024]
    if b"%PDF-" not in header_sample:
        raise DocumentProcessingError("Invalid file signature: Content does not appear to be a valid PDF document.")
