"""Tests for Playwright integration with start_playwright parameter."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from aluvia_sdk import AluviaClient
from aluvia_sdk.errors import ApiError

# Check if Playwright is available
try:
    import playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TestPlaywrightIntegration:
    """Tests for start_playwright functionality."""

    def test_start_playwright_defaults_to_false(self) -> None:
        """Test that start_playwright defaults to False."""
        client = AluviaClient(api_key="test-api-key", log_level="silent")
        assert not client._start_playwright

    def test_start_playwright_can_be_set_to_true(self) -> None:
        """Test that start_playwright can be set to True."""
        client = AluviaClient(api_key="test-api-key", start_playwright=True, log_level="silent")
        assert client._start_playwright

    @pytest.mark.asyncio
    async def test_browser_is_none_when_start_playwright_false(self) -> None:
        """Test that browser property is None when start_playwright is False."""
        client = AluviaClient(api_key="test-api-key", start_playwright=False, log_level="silent")

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )

        connection = await client.start()

        assert connection.browser is None
        await connection.close()

    @pytest.mark.asyncio
    async def test_browser_is_none_by_default(self) -> None:
        """Test that browser property is None by default (start_playwright not set)."""
        client = AluviaClient(api_key="test-api-key", log_level="silent")

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )

        connection = await client.start()

        assert connection.browser is None
        await connection.close()

    @pytest.mark.asyncio
    async def test_raises_error_when_playwright_not_installed(self) -> None:
        """Test that ApiError is raised when Playwright is not installed but start_playwright is True."""
        client = AluviaClient(api_key="test-api-key", start_playwright=True, log_level="silent")

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )

        # Mock Playwright import to fail by patching sys.modules
        with patch.dict("sys.modules", {"playwright.async_api": None}):
            with pytest.raises(ApiError) as exc_info:
                await client.start()

            assert "Failed to start Playwright" in str(exc_info.value)

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_launches_browser_in_local_proxy_mode(self) -> None:
        """Test that browser is launched in local proxy mode when start_playwright is True."""
        client = AluviaClient(
            api_key="test-api-key",
            start_playwright=True,
            local_proxy=True,
            log_level="silent",
        )

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )

        # Mock Playwright
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        async def mock_async_playwright_start():
            return mock_playwright

        mock_async_playwright_class = MagicMock()
        mock_async_playwright_instance = MagicMock()
        mock_async_playwright_instance.start = mock_async_playwright_start
        mock_async_playwright_class.return_value = mock_async_playwright_instance

        with patch("playwright.async_api.async_playwright", mock_async_playwright_class):
            connection = await client.start()

            # Verify browser was launched
            assert mock_chromium.launch.called
            launch_args = mock_chromium.launch.call_args
            assert "proxy" in launch_args[1]
            proxy_settings = launch_args[1]["proxy"]
            assert "server" in proxy_settings
            assert "127.0.0.1:54321" in proxy_settings["server"]

            # Verify browser is attached to connection
            assert connection.browser is mock_browser

            await connection.close()

            # Verify browser was closed
            assert mock_browser.close.called

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_launches_browser_in_gateway_mode(self) -> None:
        """Test that browser is launched in gateway mode when start_playwright is True."""
        client = AluviaClient(
            api_key="test-api-key",
            start_playwright=True,
            local_proxy=False,
            log_level="silent",
        )

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.get_config = MagicMock(
            return_value=MagicMock(
                raw_proxy=MagicMock(
                    protocol="http",
                    host="gateway.aluvia.io",
                    port=8080,
                    username="test_user",
                    password="test_pass",
                )
            )
        )
        client.config_manager.stop_polling = AsyncMock()

        # Mock Playwright
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        async def mock_async_playwright_start():
            return mock_playwright

        mock_async_playwright_class = MagicMock()
        mock_async_playwright_instance = MagicMock()
        mock_async_playwright_instance.start = mock_async_playwright_start
        mock_async_playwright_class.return_value = mock_async_playwright_instance

        with patch("playwright.async_api.async_playwright", mock_async_playwright_class):
            connection = await client.start()

            # Verify browser was launched
            assert mock_chromium.launch.called
            launch_args = mock_chromium.launch.call_args
            assert "proxy" in launch_args[1]
            proxy_settings = launch_args[1]["proxy"]
            assert "server" in proxy_settings
            assert "gateway.aluvia.io" in proxy_settings["server"]

            # Verify browser is attached to connection
            assert connection.browser is mock_browser

            await connection.close()

            # Verify browser was closed
            assert mock_browser.close.called

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_connection_close_closes_browser(self) -> None:
        """Test that connection.close() properly closes the browser."""
        client = AluviaClient(
            api_key="test-api-key",
            start_playwright=True,
            local_proxy=True,
            log_level="silent",
        )

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )
        client.proxy_server.stop = AsyncMock()
        client.config_manager.stop_polling = AsyncMock()

        # Mock Playwright
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        async def mock_async_playwright_start():
            return mock_playwright

        mock_async_playwright_class = MagicMock()
        mock_async_playwright_instance = MagicMock()
        mock_async_playwright_instance.start = mock_async_playwright_start
        mock_async_playwright_class.return_value = mock_async_playwright_instance

        with patch("playwright.async_api.async_playwright", mock_async_playwright_class):
            connection = await client.start()
            assert connection.browser is mock_browser
            assert not mock_browser.close.called

            # Close connection
            await connection.close()

            # Verify browser.close() was called
            assert mock_browser.close.called

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_client_stop_closes_browser(self) -> None:
        """Test that client.stop() properly closes the browser."""
        client = AluviaClient(
            api_key="test-api-key",
            start_playwright=True,
            local_proxy=True,
            log_level="silent",
        )

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )
        client.proxy_server.stop = AsyncMock()
        client.config_manager.stop_polling = AsyncMock()

        # Mock Playwright
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        async def mock_async_playwright_start():
            return mock_playwright

        mock_async_playwright_class = MagicMock()
        mock_async_playwright_instance = MagicMock()
        mock_async_playwright_instance.start = mock_async_playwright_start
        mock_async_playwright_class.return_value = mock_async_playwright_instance

        with patch("playwright.async_api.async_playwright", mock_async_playwright_class):
            connection = await client.start()
            assert connection.browser is mock_browser
            assert not mock_browser.close.called

            # Stop client
            await client.stop()

            # Verify browser.close() was called
            assert mock_browser.close.called

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_browser_close_handles_errors_gracefully(self) -> None:
        """Test that browser close errors are handled gracefully."""
        client = AluviaClient(
            api_key="test-api-key",
            start_playwright=True,
            local_proxy=True,
            log_level="silent",
        )

        # Mock dependencies
        client.config_manager.init = AsyncMock()
        client.config_manager.start_polling = MagicMock()
        client.proxy_server.start = AsyncMock(
            return_value={"host": "127.0.0.1", "port": 54321, "url": "http://127.0.0.1:54321"}
        )
        client.proxy_server.stop = AsyncMock()
        client.config_manager.stop_polling = AsyncMock()

        # Mock Playwright with browser that throws error on close
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock(side_effect=Exception("Browser already closed"))
        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium

        async def mock_async_playwright_start():
            return mock_playwright

        mock_async_playwright_class = MagicMock()
        mock_async_playwright_instance = MagicMock()
        mock_async_playwright_instance.start = mock_async_playwright_start
        mock_async_playwright_class.return_value = mock_async_playwright_instance

        with patch("playwright.async_api.async_playwright", mock_async_playwright_class):
            connection = await client.start()

            # Close should not raise even if browser.close() throws
            await connection.close()  # Should not raise

            assert mock_browser.close.called
