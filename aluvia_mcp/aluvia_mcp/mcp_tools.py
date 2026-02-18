"""
MCP tool implementations.

Each tool wraps the corresponding CLI handler via capture_output(),
converting the handler's JSON output into MCP tool results.
"""
from typing import Optional, Dict, Any
from aluvia_sdk.bin.cli import capture_output, ToolResult
from aluvia_sdk.bin.session import handle_session
from aluvia_sdk.bin.account import handle_account
from aluvia_sdk.bin.geos import handle_geos
from aluvia_sdk.bin.open import handle_open, OpenOptions


async def session_start(
    url: str,
    connection_id: Optional[int] = None,
    headful: Optional[bool] = None,
    browser_session: Optional[str] = None,
    auto_unblock: Optional[bool] = None,
    disable_block_detection: Optional[bool] = None,
) -> ToolResult:
    """Start a browser session."""
    return await capture_output(
        lambda: handle_open(
            OpenOptions(
                url=url,
                connection_id=connection_id,
                headless=not headful if headful is not None else True,
                session_name=browser_session,
                auto_unblock=auto_unblock or False,
                disable_block_detection=disable_block_detection or False,
            )
        )
    )


async def session_close(
    browser_session: Optional[str] = None,
    all: Optional[bool] = None,
) -> ToolResult:
    """Close a browser session."""
    cli_args = ["close"]
    if browser_session:
        cli_args.extend(["--browser-session", browser_session])
    if all:
        cli_args.append("--all")
    return await capture_output(lambda: handle_session(cli_args))


async def session_list() -> ToolResult:
    """List all active browser sessions."""
    return await capture_output(lambda: handle_session(["list"]))


async def session_get(browser_session: Optional[str] = None) -> ToolResult:
    """Get detailed information about a running session."""
    cli_args = ["get"]
    if browser_session:
        cli_args.extend(["--browser-session", browser_session])
    return await capture_output(lambda: handle_session(cli_args))


async def session_rotate_ip(browser_session: Optional[str] = None) -> ToolResult:
    """Rotate the IP address for a running session."""
    cli_args = ["rotate-ip"]
    if browser_session:
        cli_args.extend(["--browser-session", browser_session])
    return await capture_output(lambda: handle_session(cli_args))


async def session_set_geo(
    geo: Optional[str] = None,
    clear: Optional[bool] = None,
    browser_session: Optional[str] = None,
) -> ToolResult:
    """Set or clear the target geographic region for a running session."""
    cli_args = ["set-geo"]
    if geo:
        cli_args.append(geo)
    if clear:
        cli_args.append("--clear")
    if browser_session:
        cli_args.extend(["--browser-session", browser_session])
    return await capture_output(lambda: handle_session(cli_args))


async def session_set_rules(
    rules: Optional[str] = None,
    remove: Optional[str] = None,
    browser_session: Optional[str] = None,
) -> ToolResult:
    """Append or remove proxy routing rules for a running session."""
    cli_args = ["set-rules"]
    if rules:
        cli_args.append(rules)
    if remove:
        cli_args.extend(["--remove", remove])
    if browser_session:
        cli_args.extend(["--browser-session", browser_session])
    return await capture_output(lambda: handle_session(cli_args))


async def account_get() -> ToolResult:
    """Get Aluvia account information."""
    return await capture_output(lambda: handle_account([]))


async def account_usage(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> ToolResult:
    """Get Aluvia account usage statistics."""
    cli_args = ["usage"]
    if start:
        cli_args.extend(["--start", start])
    if end:
        cli_args.extend(["--end", end])
    return await capture_output(lambda: handle_account(cli_args))


async def geos_list() -> ToolResult:
    """List all available geographic regions."""
    return await capture_output(lambda: handle_geos())
