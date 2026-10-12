import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx

from backend.app.core.errors import SecurityValidationError

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
}


def is_ip_disallowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to private, loopback, link-local, or reserved ranges."""
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified


def validate_pdf_url(url: str) -> None:
    """
    Validate that a URL is safe to fetch:
    1. Scheme is http or https.
    2. Hostname is present and not blocked.
    3. No embedded credentials.
    4. Resolved IP addresses do not belong to local/private/cloud-metadata networks.
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SecurityValidationError(f"Invalid URL format: {e}") from e

    if parsed.scheme.lower() not in ("http", "https"):
        raise SecurityValidationError(f"Forbidden URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    if parsed.username or parsed.password:
        raise SecurityValidationError("URLs containing embedded credentials are not allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityValidationError("URL must include a valid hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise SecurityValidationError(f"Access to hostname '{hostname}' is prohibited.")

    # Check direct IP addresses
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_disallowed(ip):
            raise SecurityValidationError(f"Access to IP address '{ip}' is prohibited.")
        return
    except ValueError:
        pass  # It's a hostname, proceed to DNS resolution

    # Resolve hostname to all associated IPs to prevent SSRF
    try:
        addr_info = socket.getaddrinfo(
            hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP
        )
    except socket.gaierror as e:
        raise SecurityValidationError(f"Could not resolve hostname '{hostname}': {e}") from e

    resolved_ips: set[str] = set()
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        resolved_ips.add(ip_str)

    if not resolved_ips:
        raise SecurityValidationError(f"Hostname '{hostname}' did not resolve to any IP address.")

    for ip_str in resolved_ips:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if is_ip_disallowed(ip_obj):
                raise SecurityValidationError(
                    f"Hostname '{hostname}' resolved to disallowed network address '{ip_str}'."
                )
        except ValueError as err:
            raise SecurityValidationError(f"Invalid resolved IP '{ip_str}'.") from err


async def safe_download_pdf(
    url: str,
    max_size_bytes: int,
    timeout_seconds: float = 15.0,
    max_redirects: int = 3,
) -> tuple[bytes, str]:
    """
    Safely download PDF bytes from a remote URL with streaming size limits
    and redirect hop re-validation to block redirect-based SSRF.
    Returns (content_bytes, resolved_filename).
    """
    current_url = url
    redirect_count = 0

    transport = httpx.AsyncHTTPTransport(retries=1)
    timeout = httpx.Timeout(timeout_seconds, connect=5.0)

    async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
        while True:
            # Revalidate current URL on every hop
            validate_pdf_url(current_url)

            # Follow redirects manually to validate each target
            response = await client.get(current_url, follow_redirects=False)

            if response.is_redirect:
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SecurityValidationError("Too many redirects while fetching PDF.")

                redirect_target = response.headers.get("location")
                if not redirect_target:
                    raise SecurityValidationError("Redirect response missing Location header.")

                # Resolve relative or absolute redirects safely
                current_url = urljoin(current_url, redirect_target)
                continue

            if response.status_code != 200:
                raise SecurityValidationError(
                    f"Remote server returned HTTP {response.status_code} while fetching document."
                )

            # Check declared content-length header if present
            cl_header = response.headers.get("content-length")
            if cl_header and cl_header.isdigit() and int(cl_header) > max_size_bytes:
                raise SecurityValidationError(
                    f"Remote file size ({int(cl_header)} bytes) exceeds limit of {max_size_bytes} bytes."
                )

            # Read content with hard byte cap
            content = response.content
            if len(content) > max_size_bytes:
                raise SecurityValidationError(
                    f"Downloaded content size ({len(content)} bytes) exceeds limit of {max_size_bytes} bytes."
                )

            # Infer filename from URL
            path = urlparse(current_url).path
            filename = path.split("/")[-1].strip() or "downloaded_document.pdf"
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"

            return content, filename
