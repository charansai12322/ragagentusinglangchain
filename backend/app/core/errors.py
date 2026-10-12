"""Custom domain exceptions and error handling."""

from fastapi import status


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self, message: str, code: str = "INTERNAL_ERROR", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ConfigurationError(AppException):
    """Configuration missing or invalid."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFIGURATION_ERROR", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class SecurityValidationError(AppException):
    """Security check failed (SSRF, malicious file, path traversal)."""

    def __init__(self, message: str, code: str = "SECURITY_VIOLATION"):
        super().__init__(message, code=code, status_code=status.HTTP_400_BAD_REQUEST)


class DocumentProcessingError(AppException):
    """PDF parsing, text extraction, or chunking failure."""

    def __init__(
        self,
        message: str,
        code: str = "DOCUMENT_PROCESSING_ERROR",
        status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
    ):
        super().__init__(message, code=code, status_code=status_code)


class SessionNotFoundError(AppException):
    """Document session not found or expired."""

    def __init__(self, message: str = "Session not found or has expired."):
        super().__init__(message, code="SESSION_NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND)


class SessionCapacityError(AppException):
    """Maximum concurrent sessions limit reached."""

    def __init__(self, message: str = "Maximum concurrent sessions limit reached. Please try again later."):
        super().__init__(message, code="SESSION_CAPACITY_EXCEEDED", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class RateLimitExceededError(AppException):
    """Upstream or internal rate limit reached."""

    def __init__(
        self, message: str = "Rate limit reached. Please retry after a brief delay.", retry_after: int | None = None
    ):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        self.retry_after = retry_after


class UpstreamProviderError(AppException):
    """External LLM or embedding provider error."""

    def __init__(
        self, message: str, code: str = "UPSTREAM_PROVIDER_ERROR", status_code: int = status.HTTP_502_BAD_GATEWAY
    ):
        super().__init__(message, code=code, status_code=status_code)
