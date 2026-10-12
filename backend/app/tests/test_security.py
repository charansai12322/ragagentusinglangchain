"""Security tests for SSRF prevention, upload limits, and filename sanitization."""

import pytest

from backend.app.core.errors import DocumentProcessingError, SecurityValidationError
from backend.app.security.upload_validation import sanitize_filename, validate_pdf_bytes
from backend.app.security.url_validation import validate_pdf_url


def test_sanitize_filename():
    """Verify filename sanitization eliminates traversal and illegal characters."""
    assert sanitize_filename("../../etc/passwd") == "passwd.pdf"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe") == "calc.exe.pdf"
    assert sanitize_filename("my_document.pdf") == "my_document.pdf"
    assert sanitize_filename("test\x00file.pdf") == "testfile.pdf"
    assert sanitize_filename("") == "uploaded_document.pdf"


def test_validate_pdf_bytes_limits():
    """Verify byte length and signature checks."""
    # Empty
    with pytest.raises(DocumentProcessingError):
        validate_pdf_bytes(b"", max_size_bytes=1000)

    # Oversized
    with pytest.raises(SecurityValidationError):
        validate_pdf_bytes(b"%PDF-1.4" + b"A" * 2000, max_size_bytes=1000)

    # Missing PDF magic header
    with pytest.raises(DocumentProcessingError):
        validate_pdf_bytes(b"HELLO WORLD THIS IS NOT PDF", max_size_bytes=1000)

    # Valid
    validate_pdf_bytes(b"%PDF-1.4\nvalid content", max_size_bytes=1000)


def test_ssrf_forbidden_schemes():
    """Verify non-HTTP schemes are rejected."""
    with pytest.raises(SecurityValidationError):
        validate_pdf_url("file:///etc/passwd")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("ftp://example.com/doc.pdf")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("gopher://127.0.0.1/")


def test_ssrf_forbidden_hostnames():
    """Verify loopback, private IPs, and cloud metadata endpoints are rejected."""
    # Loopback
    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://127.0.0.1/test.pdf")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://localhost/test.pdf")

    # Private RFC1918
    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://192.168.1.1/doc.pdf")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://10.0.0.1/doc.pdf")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://172.16.0.1/doc.pdf")

    # Cloud metadata
    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://169.254.169.254/computeMetadata/v1/")

    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://metadata.google.internal/v1/")


def test_ssrf_forbidden_credentials():
    """Verify URLs containing user credentials are rejected."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_pdf_url("http://admin:secret123@example.com/doc.pdf")
    assert "credentials" in str(exc.value).lower()


def test_ssrf_forbidden_ipv6_loopback():
    """Verify IPv6 loopback [::1] is rejected."""
    with pytest.raises(SecurityValidationError):
        validate_pdf_url("http://[::1]/doc.pdf")


@pytest.mark.asyncio
async def test_safe_download_redirect_to_private_ip():
    """Verify that a redirect chain redirecting to a forbidden internal address is blocked."""
    import socket
    from unittest.mock import patch

    import httpx
    import respx

    from backend.app.security.url_validation import safe_download_pdf

    def mock_dns(host, port, *args, **kwargs):
        if host in ("127.0.0.1", "localhost"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    with patch("socket.getaddrinfo", side_effect=mock_dns):
        async with respx.mock(base_url="https://legit-site.org") as respx_mock:
            # Mock initial URL redirecting to loopback
            respx_mock.get("/initial.pdf").mock(
                return_value=httpx.Response(
                    302,
                    headers={"Location": "http://127.0.0.1/internal.pdf"},
                )
            )

            with pytest.raises(SecurityValidationError) as exc:
                await safe_download_pdf("https://legit-site.org/initial.pdf", max_size_bytes=10000)
            err_text = str(exc.value).lower()
            assert "prohibited" in err_text or "loopback" in err_text or "127.0.0.1" in err_text


@pytest.mark.asyncio
async def test_safe_download_too_many_redirects():
    """Verify that redirect loops exceeding max_redirects are aborted."""
    import socket
    from unittest.mock import patch

    import httpx
    import respx

    from backend.app.security.url_validation import safe_download_pdf

    def mock_dns(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    with patch("socket.getaddrinfo", side_effect=mock_dns):
        async with respx.mock(base_url="https://legit-site.org") as respx_mock:
            respx_mock.get("/loop1").mock(
                return_value=httpx.Response(302, headers={"Location": "https://legit-site.org/loop2"})
            )
            respx_mock.get("/loop2").mock(
                return_value=httpx.Response(302, headers={"Location": "https://legit-site.org/loop3"})
            )
            respx_mock.get("/loop3").mock(
                return_value=httpx.Response(302, headers={"Location": "https://legit-site.org/loop4"})
            )
            respx_mock.get("/loop4").mock(
                return_value=httpx.Response(302, headers={"Location": "https://legit-site.org/loop5"})
            )

            with pytest.raises(SecurityValidationError) as exc:
                await safe_download_pdf("https://legit-site.org/loop1", max_size_bytes=10000, max_redirects=3)
            assert "too many redirects" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_safe_download_content_length_limit():
    """Verify that downloads declaring oversized content-length are rejected before reading body."""
    import socket
    from unittest.mock import patch

    import httpx
    import respx

    from backend.app.security.url_validation import safe_download_pdf

    def mock_dns(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    with patch("socket.getaddrinfo", side_effect=mock_dns):
        async with respx.mock(base_url="https://legit-site.org") as respx_mock:
            respx_mock.get("/huge.pdf").mock(
                return_value=httpx.Response(
                    200,
                    headers={"Content-Length": "50000000"},
                    content=b"dummy",
                )
            )

            with pytest.raises(SecurityValidationError) as exc:
                await safe_download_pdf("https://legit-site.org/huge.pdf", max_size_bytes=10000)
            assert "exceeds" in str(exc.value).lower()
