"""ProxyServer - Local HTTP/HTTPS proxy using proxy.py."""

from __future__ import annotations

import asyncio
import sys
import threading
from typing import Any

from proxy.proxy import Proxy
from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser

from aluvia_sdk.client.config_manager import ConfigManager
from aluvia_sdk.client.logger import Logger
from aluvia_sdk.client.rules import should_proxy
from aluvia_sdk.client.types import LogLevel
from aluvia_sdk.errors import ProxyStartError


# Global references for plugin
_config_manager: ConfigManager | None = None
_logger: Logger | None = None


class AluviaProxyPlugin(HttpProxyBasePlugin):
    """
    Plugin for proxy.py that implements Aluvia routing logic.
    Decides whether to route through Aluvia gateway or go direct.
    """

    def before_upstream_connection(self, request: HttpParser):
        """
        Called by proxy.py before establishing upstream connection.
        Return upstream proxy URL to route through it, or None to go direct.
        """
        global _config_manager, _logger

        try:
            # Extract hostname from request
            hostname = None

            # Check if this is a CONNECT request (for HTTPS tunneling)
            is_connect = request.method and request.method == b"CONNECT"

            if is_connect and request.path:
                # CONNECT request - path is "hostname:port" (e.g., "ipconfig.io:443")
                path_str = (
                    request.path.decode() if isinstance(request.path, bytes) else request.path
                )
                if path_str:
                    # Strip port number if present
                    hostname = path_str.split(":")[0]
                    if _logger:
                        _logger.debug(f"CONNECT request for {hostname}")
            elif request.host:
                # Regular HTTP request - use Host header
                hostname = (
                    request.host.decode() if isinstance(request.host, bytes) else request.host
                )
                if _logger:
                    _logger.debug(f"HTTP request for {hostname}")

            if not hostname:
                if _logger:
                    _logger.debug("Could not extract hostname, going direct")
                return None

            # Get current config
            if not _config_manager:
                return None

            config = _config_manager.get_config()
            if not config:
                if _logger:
                    _logger.debug("No config available, going direct")
                return None

            # Check if we should proxy this hostname
            # NOTE: With --proxy-pool configured, ALL traffic goes through Aluvia
            use_proxy = should_proxy(hostname, config.rules)

            if _logger:
                if use_proxy:
                    _logger.debug(f"Hostname {hostname} - routing through Aluvia")
                else:
                    _logger.debug(
                        f"Hostname {hostname} - would bypass (but all traffic uses --proxy-pool)"
                    )

            # Return request - proxy.py will route through configured --proxy-pool
            return request

        except Exception as e:
            if _logger:
                _logger.error(f"Error in routing decision: {e}")
            return None


class ProxyServer:
    """
    ProxyServer manages the local HTTP/HTTPS proxy that routes traffic
    through Aluvia or directly based on rules.

    Uses proxy.py library for full HTTP/HTTPS CONNECT support.
    """

    def __init__(self, config_manager: ConfigManager, log_level: LogLevel = "info") -> None:
        self.config_manager = config_manager
        self.logger = Logger(log_level)
        self._proxy: Proxy | None = None
        self._proxy_thread: threading.Thread | None = None
        self._bind_host = "127.0.0.1"
        self._actual_port: int = 0

    async def start(self, port: int | None = None) -> dict[str, Any]:
        """
        Start the local proxy server.

        Args:
            port: Optional port to listen on. If not provided, OS assigns a free port.

        Returns:
            Dictionary with 'host', 'port', and 'url' keys

        Raises:
            ProxyStartError: If server fails to start
        """
        global _config_manager, _logger

        listen_port = port or 0

        try:
            # Set global references for plugin
            _config_manager = self.config_manager
            _logger = self.logger

            # Register plugin
            module_name = f"{__name__}.AluviaProxyPlugin"

            # Build proxy arguments
            args = [
                "--hostname",
                self._bind_host,
                "--port",
                str(listen_port),
                "--plugins",
                module_name,
            ]

            # Configure Aluvia gateway as upstream proxy for ALL requests
            # TODO: Selective routing per-request isn't easily supported by proxy.py
            config = self.config_manager.get_config()
            if config:
                protocol = config.raw_proxy.protocol
                host = config.raw_proxy.host
                port = config.raw_proxy.port
                username = config.raw_proxy.username
                password = config.raw_proxy.password
                upstream = f"{protocol}://{username}:{password}@{host}:{port}"
                args.extend(["--proxy-pool", upstream])
                self.logger.info(f"Upstream proxy: {protocol}://{username}:***@{host}:{port}")

            self._proxy = Proxy(input_args=args)

            # Start proxy in a separate thread (proxy.py is blocking)
            self._proxy_thread = threading.Thread(target=self._run_proxy, daemon=True)
            self._proxy_thread.start()

            # Wait for proxy to actually start and get the port
            await self._wait_for_startup()

            info = {
                "host": self._bind_host,
                "port": self._actual_port,
                "url": f"http://{self._bind_host}:{self._actual_port}",
            }

            self.logger.info(f"Proxy server listening on {info['url']}")
            return info

        except Exception as e:
            raise ProxyStartError(f"Failed to start proxy server: {e}")

    def _run_proxy(self) -> None:
        """Run the proxy (called in separate thread)."""
        try:
            # Setup the proxy
            self._proxy.setup()

            # Get the actual port (important when port was 0)
            if hasattr(self._proxy.flags, "port"):
                self._actual_port = self._proxy.flags.port

            # Run the proxy's main loop
            # proxy.py's Proxy class doesn't have a run() method
            # The acceptor loop runs automatically after setup()
            # We just need to keep the thread alive
            import time

            while self._proxy:
                time.sleep(1)
        except Exception as e:
            self.logger.error(f"Proxy thread error: {e}")

    async def _wait_for_startup(self) -> None:
        """Wait for proxy to start and get the actual port."""
        max_attempts = 50
        for i in range(max_attempts):
            await asyncio.sleep(0.1)
            if self._proxy and hasattr(self._proxy, "flags") and self._proxy.flags.port:
                self._actual_port = self._proxy.flags.port
                return

        # Fallback: check if thread is running
        if self._proxy_thread and self._proxy_thread.is_alive():
            if self._proxy and hasattr(self._proxy, "flags"):
                self._actual_port = self._proxy.flags.port or 0
            return

        raise ProxyStartError("Proxy failed to start within timeout")

    async def stop(self) -> None:
        """Stop the local proxy server."""
        if self._proxy:
            try:
                self._proxy.shutdown()
            except Exception as e:
                self.logger.debug(f"Error during proxy shutdown: {e}")
            self._proxy = None
            self._proxy_thread = None
            self.logger.info("Proxy server stopped")
