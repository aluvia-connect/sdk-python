"""Core HTTP request handling for the API."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

import httpx

from aluvia_sdk.errors import ApiError, InvalidApiKeyError


async def request_core(
    api_base_url: str,
    api_key: str,
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    body: Any | None = None,
    headers: dict[str, str] | None = None,
    if_none_match: str | None = None,
    timeout_ms: int | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Core HTTP request function.

    Returns:
        Dictionary with 'status', 'etag', and 'body' keys.
    """
    url = f"{api_base_url}{path}"
    if query:
        # Filter out None values
        filtered_query = {k: v for k, v in query.items() if v is not None}
        if filtered_query:
            url = f"{url}?{urlencode(filtered_query)}"

    req_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "aluvia-sdk-python/1.0.0",
    }

    if headers:
        req_headers.update(headers)

    if if_none_match:
        req_headers["If-None-Match"] = if_none_match

    timeout = timeout_ms / 1000.0 if timeout_ms else 30.0

    should_close_client = False
    if client is None:
        client = httpx.AsyncClient()
        should_close_client = True

    try:
        response = await client.request(
            method=method,
            url=url,
            headers=req_headers,
            json=body if body is not None else None,
            timeout=timeout,
        )

        etag = response.headers.get("ETag")
        status = response.status_code

        # Handle empty responses
        if status == 204 or not response.content:
            return {"status": status, "etag": etag, "body": None}

        try:
            body_data = response.json()
        except Exception:
            body_data = None

        return {"status": status, "etag": etag, "body": body_data}

    except httpx.TimeoutException as e:
        raise ApiError(f"Request timeout: {e}", status_code=None)
    except httpx.RequestError as e:
        raise ApiError(f"Request failed: {e}", status_code=None)
    finally:
        if should_close_client:
            await client.aclose()
