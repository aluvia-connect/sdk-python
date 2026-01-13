"""Geos API endpoints."""

from __future__ import annotations

from typing import Any, Protocol

from aluvia_sdk.api.types import Geo


class ApiContext(Protocol):
    """Protocol for API request context."""

    async def request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
        etag: str | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        ...


async def _request_and_unwrap(ctx: ApiContext, method: str, path: str) -> dict[str, Any]:
    """Make a request and unwrap the response envelope."""
    from aluvia_sdk.api.account import _request_and_unwrap as unwrap

    return await unwrap(ctx, method, path)


class GeosApi:
    """Geos API namespace."""

    def __init__(self, ctx: ApiContext) -> None:
        self.ctx = ctx

    async def list(self) -> list[Geo]:
        """List available geo-targeting options."""
        result = await _request_and_unwrap(self.ctx, "GET", "/geos")
        data = result["data"]
        return data if isinstance(data, list) else []
