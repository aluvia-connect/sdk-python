"""Geos API endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from aluvia_sdk.api.types import Geo


class ApiContext(Protocol):
    """Protocol for API request context."""

    async def request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        etag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make an API request."""
        ...


async def _request_and_unwrap(ctx: ApiContext, method: str, path: str) -> Dict[str, Any]:
    """Make a request and unwrap the response envelope."""
    from aluvia_sdk.api.account import _request_and_unwrap as unwrap

    return await unwrap(ctx, method, path)


class GeosApi:
    """Geos API namespace."""

    def __init__(self, ctx: ApiContext) -> None:
        self.ctx = ctx

    async def list(self) -> List[Geo]:
        """List available geo-targeting options."""
        result = await _request_and_unwrap(self.ctx, "GET", "/geos")
        data = result["data"]
        return data if isinstance(data, list) else []
