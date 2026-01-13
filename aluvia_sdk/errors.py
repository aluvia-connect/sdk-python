"""Error classes for Aluvia SDK."""

from __future__ import annotations


class MissingApiKeyError(ValueError):
    """Raised when the API key is not provided to AluviaClient or AluviaApi."""

    def __init__(self, message: str = "Aluvia API key is required") -> None:
        super().__init__(message)


class InvalidApiKeyError(Exception):
    """Raised when the API returns 401 or 403, indicating the API key is invalid."""

    def __init__(self, message: str = "Invalid or expired Aluvia API key") -> None:
        super().__init__(message)


class ApiError(Exception):
    """Raised for general API errors (non-2xx responses other than auth errors)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProxyStartError(Exception):
    """Raised when the local proxy server fails to start."""

    def __init__(self, message: str = "Failed to start local proxy server") -> None:
        super().__init__(message)
