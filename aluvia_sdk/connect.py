"""Connect to running Aluvia browser sessions via CDP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from aluvia_sdk.session.lock import read_lock, list_sessions, is_process_alive, remove_lock
from aluvia_sdk.errors import ConnectError


@dataclass
class ConnectResult:
    """Result of connecting to a browser session."""

    browser: Any
    context: Any
    page: Any
    session_name: str
    cdp_url: str
    connection_id: Optional[int]
    _playwright: Any = None

    async def disconnect(self) -> None:
        """Disconnect from the browser session."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()


async def connect(session_name: Optional[str] = None) -> ConnectResult:
    """
    Connect to a running Aluvia browser session via CDP.

    - No args: auto-discovers a single running session.
    - With session name: connects to that specific session.

    Requires `playwright` as a peer dependency.

    Args:
        session_name: Optional name of the session to connect to.
                     If not provided, auto-discovers a single running session.

    Returns:
        ConnectResult object with browser, context, page, and session info.

    Raises:
        ConnectError: If connection fails or session is invalid.

    Example:
        >>> from aluvia_sdk import connect
        >>> result = await connect("my-session")
        >>> await result.page.goto("https://example.com")
        >>> await result.disconnect()
    """
    # 1. Import Playwright
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ConnectError(
            "Playwright is required for connect(). Install it: pip install playwright"
        )

    # 2. Resolve session
    resolved_name: str

    if session_name:
        resolved_name = session_name
    else:
        sessions = list_sessions()
        if not sessions:
            raise ConnectError(
                "No running Aluvia sessions found. Start one with: aluvia session start <url>"
            )
        if len(sessions) > 1:
            names = ", ".join(s["session"] for s in sessions)
            raise ConnectError(
                f"Multiple Aluvia sessions running ({names}). "
                f"Specify which one: connect('{sessions[0]['session']}')"
            )
        resolved_name = sessions[0]["session"]

    # 3. Validate session state
    lock = read_lock(resolved_name)
    if not lock:
        raise ConnectError(
            f"No Aluvia session found named '{resolved_name}'. "
            "Run 'aluvia session list' to list sessions."
        )

    if not is_process_alive(lock["pid"]):
        remove_lock(resolved_name)
        raise ConnectError(
            f"Session '{resolved_name}' is no longer running. Stale lock file removed."
        )

    if not lock.get("ready"):
        raise ConnectError(f"Session '{resolved_name}' is still starting up. Try again shortly.")

    cdp_url = lock.get("cdpUrl")
    if not cdp_url:
        raise ConnectError(f"Session '{resolved_name}' has no CDP URL.")

    # 4. Connect over CDP
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
    except Exception as err:
        try:
            await playwright.stop()
        except Exception:
            pass
        raise ConnectError(f"Failed to connect to session '{resolved_name}' at {cdp_url}: {err}")

    # 5. Get context and page
    try:
        contexts = browser.contexts
        context = contexts[0] if contexts else await browser.new_context()
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
    except Exception as err:
        try:
            await browser.close()
        except Exception:
            pass
        try:
            await playwright.stop()
        except Exception:
            pass
        raise ConnectError(f"Connected but failed to get page: {err}")

    return ConnectResult(
        browser=browser,
        context=context,
        page=page,
        session_name=resolved_name,
        cdp_url=cdp_url,
        connection_id=lock.get("connectionId"),
        _playwright=playwright,
    )
