"""Account API endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Union

from aluvia_sdk.api.types import (
    Account,
    AccountConnection,
    AccountConnectionDeleteResult,
    AccountPayment,
    AccountUsage,
)
from aluvia_sdk.errors import ApiError, InvalidApiKeyError


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


def _is_dict(value: Any) -> bool:
    """Check if value is a dictionary."""
    return isinstance(value, dict)


def _format_error_details(details: Any) -> str:
    """Format error details for display."""
    if details is None:
        return ""
    try:
        import json

        json_str = json.dumps(details)
        return json_str[:500] + "…" if len(json_str) > 500 else json_str
    except Exception:
        return str(details)


def _throw_for_non_2xx(result: Dict[str, Any]) -> None:
    """Raise appropriate exception for non-2xx status codes."""
    status = result["status"]

    if status in (401, 403):
        raise InvalidApiKeyError(f"Authentication failed (HTTP {status}). Check token validity.")

    body = result.get("body")
    if _is_dict(body) and body.get("success") is False:
        error = body.get("error", {})
        code = error.get("code", "unknown")
        message = error.get("message", "Unknown error")
        details = _format_error_details(error.get("details"))
        details_suffix = f" details={details}" if details else ""
        raise ApiError(
            f"API request failed (HTTP {status}) code={code} message={message}{details_suffix}",
            status_code=status,
        )

    raise ApiError(f"API request failed (HTTP {status})", status_code=status)


async def _request_and_unwrap(
    ctx: ApiContext,
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    etag: Optional[str] = None,
) -> Dict[str, Any]:
    """Make a request and unwrap the response envelope."""
    result = await ctx.request(method, path, query, body, headers, etag)

    if result["status"] < 200 or result["status"] >= 300:
        _throw_for_non_2xx(result)

    body_data = result.get("body")
    etag_result = result.get("etag")

    # Unwrap success envelope
    data = None
    if _is_dict(body_data):
        if body_data.get("success") is True and "data" in body_data:
            data = body_data["data"]
        elif "data" in body_data:
            data = body_data["data"]

    return {"data": data, "etag": etag_result}


class ConnectionsApi:
    """Account connections API."""

    def __init__(self, ctx: ApiContext) -> None:
        self.ctx = ctx

    async def list(self) -> List[AccountConnection]:
        """List all account connections."""
        result = await _request_and_unwrap(self.ctx, "GET", "/account/connections")
        data = result["data"]
        return data if isinstance(data, list) else []

    async def create(
        self,
        description: Optional[str] = None,
        rules: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        target_geo: Optional[str] = None,
    ) -> AccountConnection:
        """Create a new account connection."""
        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description
        if rules is not None:
            body["rules"] = rules
        if session_id is not None:
            body["session_id"] = session_id
        if target_geo is not None:
            body["target_geo"] = target_geo

        result = await _request_and_unwrap(self.ctx, "POST", "/account/connections", body=body)
        return result["data"] or {}

    async def get(self, connection_id: Union[int, str]) -> AccountConnection:
        """Get a specific connection by ID."""
        result = await _request_and_unwrap(self.ctx, "GET", f"/account/connections/{connection_id}")
        return result["data"] or {}

    async def patch(
        self,
        connection_id: Union[int, str],
        description: Optional[str] = None,
        rules: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        target_geo: Optional[str] = None,
        **kwargs: Any,
    ) -> AccountConnection:
        """Update a connection."""
        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description
        if rules is not None:
            body["rules"] = rules
        if session_id is not None:
            body["session_id"] = session_id
        if target_geo is not None:
            body["target_geo"] = target_geo
        # Allow additional fields
        body.update(kwargs)

        result = await _request_and_unwrap(
            self.ctx, "PATCH", f"/account/connections/{connection_id}", body=body
        )
        return result["data"] or {}

    async def delete(self, connection_id: Union[int, str]) -> AccountConnectionDeleteResult:
        """Delete a connection."""
        result = await _request_and_unwrap(
            self.ctx, "DELETE", f"/account/connections/{connection_id}"
        )
        return result["data"] or {"connection_id": str(connection_id), "deleted": False}


class AccountApi:
    """Account API namespace."""

    def __init__(self, ctx: ApiContext) -> None:
        self.ctx = ctx
        self.connections = ConnectionsApi(ctx)

    async def get(self) -> Account:
        """Get account information."""
        result = await _request_and_unwrap(self.ctx, "GET", "/account")
        return result["data"] or {}

    async def usage(self) -> AccountUsage:
        """Get account usage."""
        result = await _request_and_unwrap(self.ctx, "GET", "/account/usage")
        return result["data"] or {}

    async def payments(self) -> List[AccountPayment]:
        """Get account payments."""
        result = await _request_and_unwrap(self.ctx, "GET", "/account/payments")
        data = result["data"]
        return data if isinstance(data, list) else []
