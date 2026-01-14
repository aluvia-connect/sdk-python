"""Type definitions for the client layer."""

from typing import Any, Callable, Literal, Protocol, TypedDict, Union

GatewayProtocol = Literal["http", "https"]
LogLevel = Literal["silent", "info", "debug"]


class PlaywrightProxySettings(TypedDict, total=False):
    """Playwright proxy settings."""

    server: str
    username: str
    password: str


class AluviaClientOptions(TypedDict, total=False):
    """Options for AluviaClient."""

    api_key: str
    api_base_url: str
    poll_interval_ms: int
    timeout_ms: int
    gateway_protocol: GatewayProtocol
    gateway_port: int
    local_port: int
    log_level: LogLevel
    connection_id: Union[int, str]
    local_proxy: bool
    strict: bool


class AluviaClientConnection(Protocol):
    """Connection object returned by client.start()."""

    host: str
    port: int
    url: str

    def get_url(self) -> str:
        """Get the current proxy URL."""
        ...

    def as_playwright(self) -> PlaywrightProxySettings:
        """Get Playwright proxy settings."""
        ...

    def as_selenium(self) -> str:
        """Get Selenium proxy argument."""
        ...

    def as_httpx_proxies(self) -> dict[str, str]:
        """Get httpx proxy configuration."""
        ...

    def as_requests_proxies(self) -> dict[str, str]:
        """Get requests proxy configuration."""
        ...

    async def close(self) -> None:
        """Close the connection and stop the proxy."""
        ...

    async def stop(self) -> None:
        """Alias for close()."""
        ...
