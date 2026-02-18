"""AluviaClient - Main client for the Aluvia SDK."""

from __future__ import annotations

import asyncio
import time
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
from aluvia_sdk.client.block_detection import (
    BlockDetection,
    BlockDetectionConfig,
    BlockDetectionResult,
)
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
        browser: Any = None,
        browser_context: Any = None,
        cdp_url: str = "",
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
        self.browser = browser
        self.browser_context = browser_context
        self.cdp_url = cdp_url

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
        start_playwright: bool = False,
        playwright_options: Optional[Dict[str, Any]] = None,
        block_detection: Optional[BlockDetectionConfig] = None,
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
            start_playwright: Automatically start Playwright and return browser instance
                            (default: False). Browser available via connection.browser
            playwright_options: Options to pass to playwright.chromium.launch()
                              (e.g., {"headless": False, "slow_mo": 50})
            block_detection: Configuration for block detection. If None and start_playwright=True,
                           defaults to {"enabled": True}. Set to {"enabled": False} to disable.
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
        self._start_playwright = start_playwright
        self._playwright_options = playwright_options or {}
        self._browser = None
        self._playwright = None
        self._browser_context = None
        self._cdp_url = ""
        self._block_detection: Optional[BlockDetection] = None
        self._page_states: Dict[Any, Dict[str, Any]] = {}
        self._detection_mutex = asyncio.Lock()

        # Initialize block detection if configured or if using Playwright
        if block_detection is not None or start_playwright:
            self.logger.debug("Initializing block detection")
            detection_config = block_detection or BlockDetectionConfig(enabled=True)
            self._block_detection = BlockDetection(detection_config, self.logger)

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

            browser = None
            if self._start_playwright:
                try:
                    from playwright.async_api import async_playwright

                    playwright = await async_playwright().start()
                    # Use Chromium, configure proxy
                    proxy_settings = None
                    if not self.local_proxy:
                        proxy_settings = self._create_gateway_connection().as_playwright()
                    else:
                        # Use the local proxy URL
                        info = await self.proxy_server.start(self.local_port)
                        proxy_settings = self._create_local_connection(info).as_playwright()

                    # Merge playwright options with proxy settings
                    launch_options = {**self._playwright_options}
                    launch_options["proxy"] = {k: v for k, v in proxy_settings.items() if v}

                    # Find a free port for CDP and configure remote debugging
                    cdp_url = ""
                    for attempt in range(3):
                        cdp_port = await self._find_free_port()
                        try:
                            # Ensure args list exists
                            if "args" not in launch_options:
                                launch_options["args"] = []

                            # Add CDP port arg
                            args = [
                                arg
                                for arg in launch_options["args"]
                                if "--remote-debugging-port" not in str(arg)
                            ]
                            args.append(f"--remote-debugging-port={cdp_port}")
                            launch_options["args"] = args

                            browser = await playwright.chromium.launch(**launch_options)
                            cdp_url = f"http://127.0.0.1:{cdp_port}"
                            self._browser = browser
                            self._playwright = playwright
                            self._cdp_url = cdp_url
                            break
                        except Exception as err:
                            if attempt == 2 or "EADDRINUSE" not in str(err):
                                raise
                            self.logger.debug(f"Port {cdp_port} taken, retrying browser launch")

                except Exception as e:
                    raise ApiError(f"Failed to start Playwright: {e}")

            if not self.local_proxy:
                # Gateway mode - no local proxy
                self.logger.debug("localProxy disabled — local proxy will not start")
                connection = self._create_gateway_connection()
            else:
                # Client proxy mode - start local proxy
                self.config_manager.start_polling()
                info = await self.proxy_server.start(self.local_port)
                connection = self._create_local_connection(info)

            # Attach browser if started
            if browser:
                connection.browser = browser
                # Set CDP URL if available
                if hasattr(self, "_cdp_url"):
                    connection.cdp_url = self._cdp_url

                # Attach block detection to browser context if enabled
                if self._block_detection and self._block_detection.is_enabled():
                    # Get or create browser context
                    contexts = browser.contexts
                    if contexts:
                        browser_context = contexts[0]
                    else:
                        browser_context = await browser.new_context()

                    connection.browser_context = browser_context
                    self._attach_block_detection_listener(browser_context)

            self._connection = connection
            self._started = True
            return connection

    async def _find_free_port(self) -> int:
        """Find a free port for CDP remote debugging."""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            return port
        finally:
            sock.close()

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
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
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
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
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

        # Close Playwright browser if started
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        # Stop Playwright instance if started
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

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

    def _attach_page_listeners(self, page: Any) -> None:
        """Attach block detection listeners to a page"""
        if not self._block_detection:
            return

        # Track page state
        page_state = {
            "last_response": None,
            "last_analysis_ts": 0,
            "skip_full_pass": False,
            "fast_result": None,
        }
        self._page_states[page] = page_state

        # Capture navigation responses on main frame
        def on_response(response: Any) -> None:
            try:
                if (
                    response.request.is_navigation_request()
                    and response.request.frame == page.main_frame
                ):
                    page_state["last_response"] = response
                    page_state["skip_full_pass"] = False
                    page_state["fast_result"] = None
            except Exception:
                pass

        page.on("response", on_response)

        # Fast pass at domcontentloaded
        async def on_domcontentloaded() -> None:
            if not self._block_detection:
                return
            try:
                result = await self._block_detection.analyze_fast(page, page_state["last_response"])
                page_state["fast_result"] = result
                page_state["last_analysis_ts"] = time.time()

                if result.score >= 0.9:
                    page_state["skip_full_pass"] = True
                    await self._handle_detection_result(result, page)
            except Exception as error:
                self.logger.warn(f"Error in fast-pass detection: {error}")

        page.on("domcontentloaded", lambda: asyncio.create_task(on_domcontentloaded()))

        # Full pass at load
        async def on_load() -> None:
            if not self._block_detection or page_state["skip_full_pass"]:
                return
            try:
                # Wait for networkidle with timeout cap
                try:
                    await page.wait_for_load_state(
                        "networkidle", timeout=self._block_detection.get_network_idle_timeout_ms()
                    )
                except Exception:
                    # Timeout is ok, proceed anyway
                    pass

                result = await self._block_detection.analyze_full(
                    page, page_state["last_response"], page_state["fast_result"]
                )
                page_state["last_analysis_ts"] = time.time()

                await self._handle_detection_result(result, page)
            except Exception as error:
                self.logger.warn(f"Error in full-pass detection: {error}")

        page.on("load", lambda: asyncio.create_task(on_load()))

        # SPA detection via framenavigated
        async def on_framenavigated(frame: Any) -> None:
            if not self._block_detection:
                return
            try:
                # Only handle main frame
                if frame != page.main_frame:
                    return

                # Debounce per-page
                now = time.time()
                if now - page_state["last_analysis_ts"] < 0.2:  # 200ms
                    return

                # Wait 50ms and check if a new response arrived
                response_before = page_state["last_response"]
                await asyncio.sleep(0.05)
                if page_state["last_response"] != response_before:
                    return  # Not SPA

                result = await self._block_detection.analyze_spa(page)
                page_state["last_analysis_ts"] = now

                await self._handle_detection_result(result, page)
            except Exception as error:
                self.logger.warn(f"Error in SPA detection: {error}")

        page.on("framenavigated", lambda frame: asyncio.create_task(on_framenavigated(frame)))

    def _attach_block_detection_listener(self, context: Any) -> None:
        """Attach block detection listener to all existing and future pages in a context"""
        if not self._block_detection:
            return

        self.logger.debug("Attaching block detection listener to context")

        # Attach to existing pages
        try:
            existing_pages = context.pages
            for page in existing_pages:
                self._attach_page_listeners(page)
                # Check if page has already loaded (not about:blank)
                if page.url != "about:blank" and self._block_detection:

                    async def analyze_existing() -> None:
                        try:
                            result = await self._block_detection.analyze_full(page, None)
                            await self._handle_detection_result(result, page)
                        except Exception as error:
                            self.logger.warn(f"Error analyzing existing page: {error}")

                    asyncio.create_task(analyze_existing())
        except Exception:
            pass

        # Attach to future pages
        def on_page(page: Any) -> None:
            self.logger.debug(f"New page detected: {page.url}")
            self._attach_page_listeners(page)

        context.on("page", on_page)

    async def _handle_detection_result(self, result: BlockDetectionResult, page: Any) -> None:
        """Handle a block detection result"""
        if not self._block_detection:
            return

        # Fire user's onDetection callback for all tiers (including clear)
        on_detection = self._block_detection.get_on_detection()
        if on_detection:
            try:
                # Create a shallow clone
                snapshot = BlockDetectionResult(
                    url=result.url,
                    hostname=result.hostname,
                    block_status=result.block_status,
                    score=result.score,
                    signals=result.signals.copy(),
                    pass_type=result.pass_type,
                    persistent_block=result.persistent_block,
                    redirect_chain=result.redirect_chain.copy(),
                )
                await on_detection(snapshot, page)
            except Exception as error:
                self.logger.warn(f"Error in onDetection callback: {error}")

        # If auto-reload is disabled, stop here (detection-only mode)
        if not self._block_detection.is_auto_unblock():
            return

        # Check if auto-reload should fire for this blockStatus
        should_reload = result.block_status == "blocked" or (
            result.block_status == "suspected"
            and self._block_detection.is_auto_unblock_on_suspected()
        )

        if not should_reload:
            return

        # Serialize the critical section
        async with self._detection_mutex:
            await self._handle_auto_unblock(result, page)

    async def _handle_auto_unblock(self, result: BlockDetectionResult, page: Any) -> None:
        """Auto-unblock critical section. Must only be called under _detection_mutex."""
        if not self._block_detection:
            return

        url = result.url
        hostname = result.hostname

        # Check persistent block escalation
        if hostname in self._block_detection.persistent_hostnames:
            result.persistent_block = True
            self.logger.warn(f"Persistent block on {hostname}, skipping reload")
            return

        if url in self._block_detection.retried_urls:
            # Second block for this URL - mark hostname as persistent
            result.persistent_block = True
            self._block_detection.persistent_hostnames.add(hostname)
            self.logger.warn(f"Persistent block detected for {hostname} after retry of {url}")
            return

        # First block for this URL - cap set size to prevent unbounded growth
        if len(self._block_detection.retried_urls) >= 10_000:
            self._block_detection.retried_urls.clear()
        self._block_detection.retried_urls.add(url)

        # Add hostname to proxy routing rules
        try:
            config = self.config_manager.get_config()
            current_rules = config.rules if config else []
            if hostname not in current_rules:
                self.logger.info(
                    f"Auto-adding {hostname} to routing rules due to detection "
                    f"(blockStatus: {result.block_status})"
                )
                await self.update_rules([*current_rules, hostname])
        except Exception as error:
            self.logger.warn(f"Failed to auto-add rule for {hostname}: {error}")

        # Reload page
        try:
            self.logger.info(f"Reloading page after adding {hostname} to rules")
            await page.reload()
        except Exception as error:
            self.logger.warn(f"Failed to reload page for {hostname}: {error}")

    async def __aenter__(self) -> "AluviaClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
