"""ProxyServer - Local HTTP/HTTPS proxy using proxy.py."""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import os
import sys
import tempfile
import threading
import time
from typing import Any, Optional

from proxy.proxy import Proxy
from proxy.plugin import ProxyPoolPlugin
from proxy.http.parser import HttpParser

from aluvia_sdk.client.config_manager import ConfigManager
from aluvia_sdk.client.logger import Logger
from aluvia_sdk.client.rules import should_proxy
from aluvia_sdk.client.types import LogLevel
from aluvia_sdk.errors import ProxyStartError

IS_WINDOWS = sys.platform.startswith("win")

# Linux/macOS shared config (Manager-backed)
_manager: Any = None
_shared_config: Any = None
_logger: Logger | None = None

# Windows-only: use a JSON snapshot for rules so all spawned proxy.py workers
# read the same config (spawn re-imports module, globals/Manager aren’t shared).
_RULES_PATH = os.path.join(tempfile.gettempdir(), "aluvia_proxy_rules.json")

_rules_cache: list[Any] = []
_rules_mtime: float = 0.0
_last_check: float = 0.0


def _ensure_shared_config() -> Any:
    """
    Lazily initialize the multiprocessing Manager and shared dict.

    NOTE: This is NOT used on Windows for proxy decision rules because proxy.py can
    spawn processes that re-import modules, causing each process to create its own
    Manager() server. On Linux/macOS, this is typically OK.
    """
    global _manager, _shared_config
    if _manager is None:
        _manager = multiprocessing.Manager()
        _shared_config = _manager.dict()
    return _shared_config


def _write_rules_atomic(rules: Any) -> None:
    """Windows: write rules snapshot atomically to a shared file."""
    payload = {"rules": rules, "ts": time.time()}
    tmp_path = _RULES_PATH + ".tmp"

    # Write to temp file, flush+fsync, then atomic replace.
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
        f.flush()
        os.fsync(f.fileno())

    # Atomic on Windows (and POSIX)
    os.replace(tmp_path, _RULES_PATH)


def _load_rules_cached(ttl_seconds: float = 0.5) -> list[Any]:
    """
    Windows: load rules from snapshot file, with small per-process cache.

    ttl_seconds prevents os.stat() on every request under heavy load.
    mtime change triggers reload.
    """
    global _rules_cache, _rules_mtime, _last_check

    now = time.time()
    if now - _last_check < ttl_seconds:
        return _rules_cache
    _last_check = now

    try:
        st = os.stat(_RULES_PATH)
        if st.st_mtime != _rules_mtime:
            with open(_RULES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            _rules_cache = data.get("rules", []) or []
            _rules_mtime = st.st_mtime
    except FileNotFoundError:
        _rules_cache = []
    except Exception:
        # Keep last known good cache on transient read/parse errors
        pass

    return _rules_cache


def _get_rules() -> list[Any]:
    """Get current rules using the appropriate mechanism per platform."""
    if IS_WINDOWS:
        return _load_rules_cached(ttl_seconds=0.5)

    shared_config = _ensure_shared_config()
    return shared_config.get("rules", []) or []


def _set_rules(rules: Any) -> None:
    """Set current rules using the appropriate mechanism per platform."""
    if IS_WINDOWS:
        _write_rules_atomic(rules)
        return

    shared_config = _ensure_shared_config()
    shared_config["rules"] = rules


class AluviaProxyPlugin(ProxyPoolPlugin):
    """
    Plugin for proxy.py that implements Aluvia routing logic.

    Extends ProxyPoolPlugin to get proper upstream proxy handling.
    Decides whether to route through Aluvia gateway or go direct based on hostname rules.
    """

    def before_upstream_connection(self, request: HttpParser) -> Optional[HttpParser]:
        """
        Called by proxy.py before establishing upstream connection.

        Returns:
            - request: Go direct (bypass upstream proxy)
            - None: Route through upstream proxy (calls parent which uses --proxy-pool)
        """
        global _logger

        try:
            # Extract hostname from request
            hostname = self._extract_hostname(request)

            if not hostname:
                if _logger:
                    _logger.debug("Could not extract hostname, going direct")
                return request  # Direct connection

            rules = _get_rules()
            if not rules:
                if _logger:
                    _logger.debug("No rules available, going direct")
                return request

            # Check if we should proxy this hostname
            use_proxy = should_proxy(hostname, rules)

            if not use_proxy:
                if _logger:
                    _logger.debug(f"Hostname {hostname} - bypassing (direct connection)")
                return request  # Direct connection

            # Route through Aluvia gateway - let parent class handle it
            if _logger:
                _logger.debug(f"Hostname {hostname} - routing through Aluvia (via parent)")

            # Call parent class which will use --proxy-pool to connect to Aluvia
            return super().before_upstream_connection(request)

        except Exception as e:
            if _logger:
                _logger.error(f"Error in routing decision: {e}")
            # On error, go direct
            return request

    def _extract_hostname(self, request: HttpParser) -> str | None:
        """Extract hostname from HTTP request or CONNECT tunnel."""
        # Check if this is a CONNECT request (for HTTPS tunneling)
        is_connect = request.method and request.method == b"CONNECT"

        if is_connect and request.path:
            # CONNECT request - path is "hostname:port" (e.g., "ipconfig.io:443")
            path_str = request.path.decode() if isinstance(request.path, bytes) else request.path
            if path_str:
                # Strip port number if present
                hostname = path_str.split(":")[0]
                return hostname if hostname else None

        elif request.host:
            # Regular HTTP request - use Host header
            hostname = request.host.decode() if isinstance(request.host, bytes) else request.host
            return hostname if hostname else None

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
        self._shutdown_event = threading.Event()

        # Set callback to update shared config when ConfigManager updates
        self.config_manager._shared_config_callback = self._update_shared_config

    def _update_shared_config(self, key: str, value: Any) -> None:
        """Callback to update shared config dict when ConfigManager updates."""
        if key == "rules":
            _set_rules(value)
            self.logger.debug(f"Updated shared config: {key} = {value}")
            return

        # Only maintain manager-backed shared config on non-Windows
        if not IS_WINDOWS:
            shared_config = _ensure_shared_config()
            shared_config[key] = value

        self.logger.debug(f"Updated shared config: {key} = {value}")

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
        global _logger

        listen_port = port or 0

        try:
            # Set shared config for plugin (accessible across all processes)
            _logger = self.logger

            # Get initial config and populate shared dict
            config = self.config_manager.get_config()
            if not config:
                raise ProxyStartError(
                    "No configuration available - cannot start proxy without Aluvia gateway credentials"
                )

            # Windows=file snapshot, non-Windows=Manager
            _set_rules(config.rules)

            # Register plugin
            module_name = f"{__name__}.AluviaProxyPlugin"

            # Build Aluvia gateway URL for --proxy-pool
            protocol = config.raw_proxy.protocol
            host = config.raw_proxy.host
            port_num = config.raw_proxy.port
            username = config.raw_proxy.username
            password = config.raw_proxy.password

            # Format: http://username:password@host:port
            aluvia_proxy_url = f"{protocol}://{username}:{password}@{host}:{port_num}"

            # Build proxy arguments
            args = [
                "--hostname",
                self._bind_host,
                "--port",
                str(listen_port),
                "--plugins",
                module_name,
                "--proxy-pool",
                aluvia_proxy_url,  # This is what ProxyPoolPlugin will use
                "--num-workers",
                "0",  # Single process mode - required for config sharing
            ]

            # Log configuration status
            self.logger.info(f"Aluvia gateway: {protocol}://{username}:***@{host}:{port_num}")
            self.logger.info("Proxy routing: Rules-based (per-request hostname matching)")

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
            # We keep the thread alive until shutdown is signaled
            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(timeout=1.0)
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
                # Signal the thread to stop
                self._shutdown_event.set()

                # Give thread time to exit gracefully
                if self._proxy_thread and self._proxy_thread.is_alive():
                    self._proxy_thread.join(timeout=2.0)

                self._proxy.shutdown()
            except Exception as e:
                self.logger.debug(f"Error during proxy shutdown: {e}")
            self._proxy = None
            self._proxy_thread = None
            self._shutdown_event.clear()
            self.logger.info("Proxy server stopped")
