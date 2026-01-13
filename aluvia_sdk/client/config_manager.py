"""ConfigManager - Control plane for connection configuration."""

from __future__ import annotations

import asyncio
from typing import Any

from aluvia_sdk.api.request import request_core
from aluvia_sdk.client.logger import Logger
from aluvia_sdk.client.types import GatewayProtocol, LogLevel
from aluvia_sdk.errors import ApiError, InvalidApiKeyError


class RawProxyConfig:
    """Raw proxy configuration."""

    def __init__(
        self,
        protocol: GatewayProtocol,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class ConnectionNetworkConfig:
    """Complete connection network configuration."""

    def __init__(
        self,
        raw_proxy: RawProxyConfig,
        rules: list[str],
        session_id: str | None,
        target_geo: str | None,
        etag: str | None,
    ) -> None:
        self.raw_proxy = raw_proxy
        self.rules = rules
        self.session_id = session_id
        self.target_geo = target_geo
        self.etag = etag


class ConfigManager:
    """
    ConfigManager handles fetching and updating connection configuration.

    It manages:
    - Fetching initial config from the API
    - Polling for config updates
    - Pushing config changes (rules, session_id, target_geo)
    """

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        poll_interval_ms: int,
        gateway_protocol: GatewayProtocol,
        gateway_port: int,
        log_level: LogLevel,
        connection_id: int | str | None = None,
        strict: bool = True,
    ) -> None:
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.poll_interval_ms = poll_interval_ms
        self.gateway_protocol = gateway_protocol
        self.gateway_port = gateway_port
        self.connection_id = connection_id
        self.strict = strict
        self.logger = Logger(log_level)

        self._config: ConnectionNetworkConfig | None = None
        self._polling_task: asyncio.Task[None] | None = None
        self._stop_polling = False

    async def init(self) -> None:
        """Initialize by fetching the initial configuration."""
        self.logger.debug("ConfigManager: Fetching initial configuration")

        if self.connection_id is not None:
            # Use existing connection
            path = f"/account/connections/{self.connection_id}"
            method = "GET"
            body = None
        else:
            # Create new connection
            path = "/account/connections"
            method = "POST"
            body = {}

        try:
            result = await request_core(
                api_base_url=self.api_base_url,
                api_key=self.api_key,
                method=method,
                path=path,
                body=body,
            )

            if result["status"] < 200 or result["status"] >= 300:
                self._handle_error_response(result)

            self._parse_and_update_config(result)
            self.logger.info("ConfigManager: Initial configuration loaded")

        except (InvalidApiKeyError, ApiError):
            raise
        except Exception as e:
            raise ApiError(f"Failed to fetch initial configuration: {e}")

    def _handle_error_response(self, result: dict[str, Any]) -> None:
        """Handle error responses from the API."""
        status = result["status"]
        if status in (401, 403):
            raise InvalidApiKeyError(f"Authentication failed (HTTP {status})")
        raise ApiError(f"API request failed (HTTP {status})", status_code=status)

    def _parse_rules(self, rules_data: Any) -> list[str]:
        """
        Parse rules from API response.

        Rules can be in two formats:
        1. Array of strings: ["*.google.com", "example.com"]
        2. Object with type and items: {"type": "hostname", "items": "example.com"}
           where items can be a comma-separated string
        """
        if isinstance(rules_data, list):
            return rules_data

        if isinstance(rules_data, dict):
            items = rules_data.get("items", "")
            if isinstance(items, str):
                # Split comma-separated hostnames
                return [item.strip() for item in items.split(",") if item.strip()]
            elif isinstance(items, list):
                return items

        return []

    def _parse_and_update_config(self, result: dict[str, Any]) -> None:
        """Parse API response and update configuration."""
        body = result.get("body", {})
        etag = result.get("etag")

        if not isinstance(body, dict):
            if self.strict:
                raise ApiError("Invalid API response format")
            return

        data = body.get("data", {})
        if not isinstance(data, dict):
            if self.strict:
                raise ApiError("Invalid API response data")
            return

        # Extract proxy credentials
        proxy_username = data.get("proxy_username", "")
        proxy_password = data.get("proxy_password", "")

        if not proxy_username or not proxy_password:
            if self.strict:
                raise ApiError("Missing proxy credentials in API response")
            return

        # Build configuration
        raw_proxy = RawProxyConfig(
            protocol=self.gateway_protocol,
            host="gateway.aluvia.io",
            port=self.gateway_port,
            username=proxy_username,
            password=proxy_password,
        )

        # Parse rules - can be a list or dict with {type, items}
        rules_data = data.get("rules", [])
        rules = self._parse_rules(rules_data)

        session_id = data.get("session_id")
        target_geo = data.get("target_geo")

        self._config = ConnectionNetworkConfig(
            raw_proxy=raw_proxy,
            rules=rules,
            session_id=session_id,
            target_geo=target_geo,
            etag=etag,
        )

    def get_config(self) -> ConnectionNetworkConfig | None:
        """Get the current configuration."""
        return self._config

    def start_polling(self) -> None:
        """Start polling for configuration updates."""
        if self._polling_task is not None:
            return

        self._stop_polling = False
        self._polling_task = asyncio.create_task(self._poll_loop())
        self.logger.debug("ConfigManager: Started polling")

    def stop_polling(self) -> None:
        """Stop polling for configuration updates."""
        if self._polling_task is None:
            return

        self._stop_polling = True
        self._polling_task.cancel()
        self._polling_task = None
        self.logger.debug("ConfigManager: Stopped polling")

    async def _poll_loop(self) -> None:
        """Background polling loop."""
        while not self._stop_polling:
            try:
                await asyncio.sleep(self.poll_interval_ms / 1000.0)
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"ConfigManager: Polling error: {e}")

    async def _poll_once(self) -> None:
        """Poll for configuration updates once."""
        if self._config is None or self.connection_id is None:
            return

        try:
            result = await request_core(
                api_base_url=self.api_base_url,
                api_key=self.api_key,
                method="GET",
                path=f"/account/connections/{self.connection_id}",
                if_none_match=self._config.etag,
            )

            # 304 Not Modified - no changes
            if result["status"] == 304:
                return

            if result["status"] >= 200 and result["status"] < 300:
                self._parse_and_update_config(result)
                self.logger.debug("ConfigManager: Configuration updated")

        except Exception as e:
            self.logger.error(f"ConfigManager: Poll failed: {e}")

    async def set_config(
        self,
        rules: list[str] | None = None,
        session_id: str | None = None,
        target_geo: str | None = None,
    ) -> None:
        """
        Update configuration on the server.

        Args:
            rules: New routing rules (optional)
            session_id: New session ID (optional)
            target_geo: New target geo (optional)
        """
        if self.connection_id is None:
            raise ApiError("Cannot update config without connection_id")

        body: dict[str, Any] = {}
        if rules is not None:
            body["rules"] = rules
        if session_id is not None:
            body["session_id"] = session_id
        if target_geo is not None:
            body["target_geo"] = target_geo

        try:
            result = await request_core(
                api_base_url=self.api_base_url,
                api_key=self.api_key,
                method="PATCH",
                path=f"/account/connections/{self.connection_id}",
                body=body,
            )

            if result["status"] < 200 or result["status"] >= 300:
                self._handle_error_response(result)

            self._parse_and_update_config(result)
            self.logger.info("ConfigManager: Configuration updated on server")

        except (InvalidApiKeyError, ApiError):
            raise
        except Exception as e:
            raise ApiError(f"Failed to update configuration: {e}")
