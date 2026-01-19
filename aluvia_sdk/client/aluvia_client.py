"""AluviaClient - Main client for the Aluvia SDK."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from aluvia_sdk.api.aluvia_api import AluviaApi
from aluvia_sdk.client.adapters import (
    to_httpx,
    to_playwright_proxy_settings,
    to_requests,
    to_selenium_args,
)
from aluvia_sdk.client.config_manager import ConfigManager
from aluvia_sdk.client.logger import Logger
from aluvia_sdk.client.proxy_server import ProxyServer
from aluvia_sdk.client.types import GatewayProtocol, LogLevel, PlaywrightProxySettings
from aluvia_sdk.errors import ApiError, MissingApiKeyError


class ConnectionObject:
    """Connection object returned by client.start()."""

    def __init__(
        self,
        host: str,
        port: int,
        url: str,
        get_url_fn: Any,
        as_playwright_fn: Any,
        as_selenium_fn: Any,
        as_httpx_fn: Any,
        as_requests_fn: Any,
        close_fn: Any,
    ) -> None:
        self.host = host
        self.port = port
        self.url = url
        self._get_url_fn = get_url_fn
        self._as_playwright_fn = as_playwright_fn
        self._as_selenium_fn = as_selenium_fn
        self._as_httpx_fn = as_httpx_fn
        self._as_requests_fn = as_requests_fn
        self._close_fn = close_fn

    def get_url(self) -> str:
        """Get the current proxy URL."""
        return self._get_url_fn()

    def as_playwright(self) -> PlaywrightProxySettings:
        """Get Playwright proxy settings."""
        return self._as_playwright_fn()

    def as_selenium(self) -> str:
        """Get Selenium proxy argument."""
        return self._as_selenium_fn()

    def as_httpx(self) -> Dict[str, str]:
        """Get httpx proxy configuration."""
        return self._as_httpx_fn()

    def as_requests(self) -> Dict[str, str]:
        """Get requests proxy configuration."""
        return self._as_requests_fn()

    def as_aiohttp(self) -> str:
        """Get aiohttp proxy URL."""
        return self.url

    async def close(self) -> None:
        """Close the connection and stop the proxy."""
        await self._close_fn()

    async def stop(self) -> None:
        """Alias for close()."""
        await self.close()


class AluviaClient:
    """
    AluviaClient is the main entry point for the Aluvia SDK.

    It manages the local proxy server and configuration polling.

    Example:
        >>> client = AluviaClient(api_key="your-api-key")
        >>> connection = await client.start()
        >>> # Use connection with your tools
        >>> await connection.close()
    """

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.aluvia.io/v1",
        poll_interval_ms: int = 5000,
        timeout_ms: Optional[int] = None,
        gateway_protocol: GatewayProtocol = "http",
        gateway_port: Optional[int] = None,
        local_port: Optional[int] = None,
        log_level: LogLevel = "info",
        connection_id: Optional[Union[int, str]] = None,
        local_proxy: bool = True,
        strict: bool = True,
    ) -> None:
        """
        Initialize AluviaClient.

        Args:
            api_key: Aluvia API key (required)
            api_base_url: Base URL for the API
            poll_interval_ms: Polling interval for config updates
            timeout_ms: Request timeout in milliseconds
            gateway_protocol: Protocol to use for gateway ('http' or 'https')
            gateway_port: Gateway port (defaults based on protocol)
            local_port: Local proxy port (0 for auto-assign)
            log_level: Logging level ('silent', 'info', or 'debug')
            connection_id: Existing connection ID to use
            local_proxy: Whether to start local proxy (default: True)
            strict: Strict mode for error handling
        """
        api_key = str(api_key or "").strip()
        if not api_key:
            raise MissingApiKeyError("Aluvia API key is required")

        self.api_key = api_key
        self.api_base_url = api_base_url
        self.poll_interval_ms = poll_interval_ms
        self.timeout_ms = timeout_ms
        self.gateway_protocol = gateway_protocol
        self.gateway_port = gateway_port or (8443 if gateway_protocol == "https" else 8080)
        self.local_port = local_port
        self.log_level = log_level
        self.connection_id = connection_id
        self.local_proxy = local_proxy
        self.strict = strict

        self.logger = Logger(log_level)
        self._connection: Optional[ConnectionObject] = None
        self._started = False
        self._start_lock = asyncio.Lock()

        # Create ConfigManager
        self.config_manager = ConfigManager(
            api_key=api_key,
            api_base_url=api_base_url,
            poll_interval_ms=poll_interval_ms,
            gateway_protocol=gateway_protocol,
            gateway_port=self.gateway_port,
            log_level=log_level,
            connection_id=connection_id,
            strict=strict,
        )

        # Create ProxyServer
        self.proxy_server = ProxyServer(self.config_manager, log_level=log_level)

        # Create API wrapper
        self.api = AluviaApi(
            api_key=api_key,
            api_base_url=api_base_url,
            timeout_ms=timeout_ms,
        )

    async def start(self) -> ConnectionObject:
        """
        Start the Aluvia Client connection.

        Returns:
            Connection object with proxy settings and adapters
        """
        async with self._start_lock:
            # Return existing connection if already started
            if self._started and self._connection:
                return self._connection

            # Fetch initial configuration
            await self.config_manager.init()

            # Check if we have config in gateway mode
            if not self.local_proxy and not self.config_manager.get_config():
                raise ApiError("Failed to load connection config; cannot start in gateway mode")

            if not self.local_proxy:
                # Gateway mode - no local proxy
                self.logger.debug("localProxy disabled — local proxy will not start")
                connection = self._create_gateway_connection()
            else:
                # Client proxy mode - start local proxy
                self.config_manager.start_polling()
                info = await self.proxy_server.start(self.local_port)
                connection = self._create_local_connection(info)

            self._connection = connection
            self._started = True
            return connection

    def _create_gateway_connection(self) -> ConnectionObject:
        """Create connection object for gateway mode."""
        config = self.config_manager.get_config()

        def get_proxy_url() -> str:
            cfg = self.config_manager.get_config()
            if not cfg:
                return "http://127.0.0.1"
            username = quote(cfg.raw_proxy.username)
            password = quote(cfg.raw_proxy.password)
            return (
                f"{cfg.raw_proxy.protocol}://{username}:{password}@"
                f"{cfg.raw_proxy.host}:{cfg.raw_proxy.port}"
            )

        def as_playwright() -> PlaywrightProxySettings:
            cfg = self.config_manager.get_config()
            if not cfg:
                return {"server": ""}
            url = f"{cfg.raw_proxy.protocol}://{cfg.raw_proxy.host}:{cfg.raw_proxy.port}"
            return {
                **to_playwright_proxy_settings(url),
                "username": cfg.raw_proxy.username,
                "password": cfg.raw_proxy.password,
            }

        def as_selenium() -> str:
            cfg = self.config_manager.get_config()
            if not cfg:
                return ""
            url = f"{cfg.raw_proxy.protocol}://{cfg.raw_proxy.host}:{cfg.raw_proxy.port}"
            return to_selenium_args(url)

        def as_httpx() -> Dict[str, str]:
            return to_httpx(get_proxy_url())

        def as_requests() -> Dict[str, str]:
            return to_requests(get_proxy_url())

        async def close() -> None:
            await self.config_manager.stop_polling()
            self._connection = None
            self._started = False

        initial_url = get_proxy_url()

        return ConnectionObject(
            host=config.raw_proxy.host if config else "127.0.0.1",
            port=config.raw_proxy.port if config else 0,
            url=initial_url,
            get_url_fn=get_proxy_url,
            as_playwright_fn=as_playwright,
            as_selenium_fn=as_selenium,
            as_httpx_fn=as_httpx,
            as_requests_fn=as_requests,
            close_fn=close,
        )

    def _create_local_connection(self, info: Dict[str, Any]) -> ConnectionObject:
        """Create connection object for local proxy mode."""
        url = info["url"]

        def get_url() -> str:
            return url

        def as_playwright() -> PlaywrightProxySettings:
            return to_playwright_proxy_settings(url)

        def as_selenium() -> str:
            return to_selenium_args(url)

        def as_httpx() -> Dict[str, str]:
            return to_httpx(url)

        def as_requests() -> Dict[str, str]:
            return to_requests(url)

        async def close() -> None:
            await self.proxy_server.stop()
            await self.config_manager.stop_polling()
            self._connection = None
            self._started = False

        return ConnectionObject(
            host=info["host"],
            port=info["port"],
            url=url,
            get_url_fn=get_url,
            as_playwright_fn=as_playwright,
            as_selenium_fn=as_selenium,
            as_httpx_fn=as_httpx,
            as_requests_fn=as_requests,
            close_fn=close,
        )

    async def stop(self) -> None:
        """Stop the client and clean up resources."""
        if not self._started:
            return

        if self.local_proxy:
            await self.proxy_server.stop()

        await self.config_manager.stop_polling()
        self._connection = None
        self._started = False

    async def update_rules(self, rules: List[str]) -> None:
        """
        Update the filtering rules used by the proxy.

        Args:
            rules: List of hostname patterns to proxy
        """
        await self.config_manager.set_config(rules=rules)

    async def update_session_id(self, session_id: str) -> None:
        """
        Update the upstream session_id.

        Args:
            session_id: New session ID
        """
        await self.config_manager.set_config(session_id=session_id)

    async def update_target_geo(self, target_geo: Optional[str]) -> None:
        """
        Update the upstream target_geo (geo targeting).

        Args:
            target_geo: Geo code (e.g., 'us_ca') or None to clear
        """
        if target_geo is None:
            await self.config_manager.set_config(target_geo=None)
            return

        trimmed = target_geo.strip()
        await self.config_manager.set_config(target_geo=trimmed if trimmed else None)

    async def __aenter__(self) -> "AluviaClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
