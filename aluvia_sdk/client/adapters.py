"""Tool integration adapters."""

from typing import Any


def to_playwright_proxy_settings(server_url: str) -> dict[str, str]:
    """
    Convert proxy URL to Playwright proxy settings.

    Args:
        server_url: Proxy server URL

    Returns:
        Dictionary with 'server' key
    """
    return {"server": server_url}


def to_selenium_args(server_url: str) -> str:
    """
    Convert proxy URL to Selenium/Chromium proxy argument.

    Args:
        server_url: Proxy server URL

    Returns:
        Proxy server argument string
    """
    return f"--proxy-server={server_url}"


def to_httpx(server_url: str) -> dict[str, str]:
    """
    Convert proxy URL to httpx proxies configuration.

    Args:
        server_url: Proxy server URL

    Returns:
        Dictionary with proxy configuration
    """
    return {"http://": server_url, "https://": server_url}


def to_requests(server_url: str) -> dict[str, str]:
    """
    Convert proxy URL to requests proxies configuration.

    Args:
        server_url: Proxy server URL

    Returns:
        Dictionary with proxy configuration
    """
    return {"http": server_url, "https": server_url}


def to_aiohttp(server_url: str) -> str:
    """
    Convert proxy URL to aiohttp proxy string.

    Args:
        server_url: Proxy server URL

    Returns:
        Proxy URL string
    """
    return server_url
