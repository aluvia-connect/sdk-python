"""AluviaApi - REST API wrapper."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from aluvia_sdk.api.account import AccountApi
from aluvia_sdk.api.geos import GeosApi
from aluvia_sdk.api.request import request_core
from aluvia_sdk.errors import MissingApiKeyError


class AluviaApi:
    """
    AluviaApi is a typed wrapper for the Aluvia REST API.

    Example:
        >>> api = AluviaApi(api_key="your-api-key")
        >>> account = await api.account.get()
        >>> print(account["balance_gb"])
    """

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.aluvia.io/v1",
        timeout_ms: Optional[int] = None,
    ) -> None:
        """
        Initialize the API wrapper.

        Args:
            api_key: Aluvia API key (required)
            api_base_url: Base URL for the API (default: https://api.aluvia.io/v1)
            timeout_ms: Request timeout in milliseconds (default: 30000)
        """
        api_key = str(api_key or "").strip()
        if not api_key:
            raise MissingApiKeyError("Aluvia API key is required")

        self.api_key = api_key
        self.api_base_url = api_base_url
        self.timeout_ms = timeout_ms or 30000
        self._client = httpx.AsyncClient()

        # Create context for endpoint implementations
        ctx = type("ApiContext", (), {"request": self._request})()

        self.account = AccountApi(ctx)
        self.geos = GeosApi(ctx)

    async def _request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        etag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Internal request method."""
        return await request_core(
            api_base_url=self.api_base_url,
            api_key=self.api_key,
            method=method,
            path=path,
            query=query,
            body=body,
            headers=headers,
            if_none_match=etag,
            timeout_ms=self.timeout_ms,
            client=self._client,
        )

    async def request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Low-level request method for custom API calls.

        Returns:
            Dictionary with 'status', 'etag', and 'body' keys.
        """
        return await self._request(method, path, query, body, headers)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AluviaApi":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
