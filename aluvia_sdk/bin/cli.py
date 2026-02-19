#!/usr/bin/env python3
"""
Aluvia CLI - Command-line interface for Aluvia SDK
"""
import sys
import json
import asyncio
from contextvars import ContextVar
from typing import Any, Dict, NoReturn, List, Callable, Awaitable, TypedDict

# MCP output capture context (for MCP server integration)
_mcp_capture_context: ContextVar[bool] = ContextVar('mcp_capture', default=False)


class MCPOutputCapture(Exception):
    """Exception raised when in MCP mode to capture output."""
    def __init__(self, data: Dict[str, Any], exit_code: int = 0):
        self.data = data
        self.exit_code = exit_code
        super().__init__()


class ToolResult(TypedDict):
    """Result from a tool execution."""
    data: Dict[str, Any]
    isError: bool


def is_capturing() -> bool:
    """Check if CLI is running in MCP capture mode."""
    return _mcp_capture_context.get()


async def capture_output(fn: Callable[[], Awaitable[None]]) -> ToolResult:
    """
    Run a CLI handler function in capture mode.
    Returns the data that output() would have written to stdout.
    Safe for concurrent use — each call gets its own context.
    """
    token = _mcp_capture_context.set(True)
    try:
        await fn()
        # Handler completed without calling output() — shouldn't happen for CLI handlers
        return {"data": {"error": "Handler did not produce output"}, "isError": True}
    except MCPOutputCapture as err:
        return {
            "data": err.data,
            "isError": err.exit_code != 0,
        }
    except Exception as err:
        # Unexpected error (not from output())
        return {
            "data": {"error": f"Unexpected error: {str(err)}"},
            "isError": True,
        }
    finally:
        _mcp_capture_context.reset(token)


def output(data: Dict[str, Any], exit_code: int = 0) -> NoReturn:
    """
    Output JSON data and exit.
    In MCP mode, raises MCPOutputCapture instead of exiting.
    """
    if is_capturing():
        raise MCPOutputCapture(data, exit_code)
    print(json.dumps(data))
    sys.exit(exit_code)


def print_help(to_stderr: bool = False) -> None:
    """Print CLI help message."""
    log = sys.stderr.write if to_stderr else sys.stdout.write
    
    help_text = """Aluvia CLI

Usage:
  aluvia session start <url> [options]       Start a browser session
  aluvia session close [options]              Stop a browser session
  aluvia session list                         List active browser sessions
  aluvia session get [options]                Get session details and proxy URLs
  aluvia session rotate-ip [options]          Rotate IP on a running session
  aluvia session set-geo <geo> [options]      Set target geo on a running session
  aluvia session set-rules <rules> [options]  Set routing rules on a running session

  aluvia account                              Show account info
  aluvia account usage [options]              Show usage stats
  aluvia geos                                 List available geos
  aluvia help [--json]                        Show this help

Session start options:
  --connection-id <id>       Use a specific connection ID
  --headful                  Run browser in headful mode
  --browser-session <name>   Name for this session (auto-generated if omitted)
  --auto-unblock             Auto-detect blocks and reload through Aluvia
  --disable-block-detection  Disable block detection entirely
  --run <script>             Run a script with page, browser, context injected

Session close options:
  --browser-session <name>   Close a specific session
  --all                      Close all sessions

Session targeting (get, rotate-ip, set-geo, set-rules):
  --browser-session <name>   Target a specific session (auto-selects if only one)

Session set-rules:
  <rules>                    Comma-separated rules to append (e.g. "a.com,b.com")
  --remove <rules>           Remove specific rules instead of appending

Session set-geo:
  <geo>                      Geo code to set (e.g. "US")
  --clear                    Clear target geo

Account usage options:
  --start <ISO8601>          Start date filter
  --end <ISO8601>            End date filter

Environment:
  ALUVIA_API_KEY   Required. Your Aluvia API key.

Output:
  All commands output JSON to stdout.
"""
    log(help_text)


def print_help_json() -> NoReturn:
    """Print help as JSON and exit."""
    help_data = {
        "commands": [
            {
                "command": "session start <url>",
                "description": "Start a browser session",
                "options": [
                    {"flag": "--connection-id <id>", "description": "Use a specific connection ID"},
                    {"flag": "--headful", "description": "Run browser in headful mode"},
                    {"flag": "--browser-session <name>", "description": "Name for this session (auto-generated if omitted)"},
                    {"flag": "--auto-unblock", "description": "Auto-detect blocks and reload through Aluvia"},
                    {"flag": "--disable-block-detection", "description": "Disable block detection entirely"},
                    {"flag": "--run <script>", "description": "Run a script with page, browser, context injected"},
                ],
            },
            {
                "command": "session close",
                "description": "Stop a browser session",
                "options": [
                    {"flag": "--browser-session <name>", "description": "Close a specific session"},
                    {"flag": "--all", "description": "Close all sessions"},
                ],
            },
            {
                "command": "session list",
                "description": "List active browser sessions",
                "options": [],
            },
            {
                "command": "session get",
                "description": "Get session details and proxy URLs",
                "options": [
                    {"flag": "--browser-session <name>", "description": "Target a specific session (auto-selects if only one)"},
                ],
            },
            {
                "command": "session rotate-ip",
                "description": "Rotate IP on a running session",
                "options": [
                    {"flag": "--browser-session <name>", "description": "Target a specific session (auto-selects if only one)"},
                ],
            },
            {
                "command": "session set-geo <geo>",
                "description": "Set target geo on a running session",
                "options": [
                    {"flag": "--browser-session <name>", "description": "Target a specific session (auto-selects if only one)"},
                    {"flag": "--clear", "description": "Clear target geo"},
                ],
            },
            {
                "command": "session set-rules <rules>",
                "description": "Set routing rules on a running session",
                "options": [
                    {"flag": "--browser-session <name>", "description": "Target a specific session (auto-selects if only one)"},
                    {"flag": "--remove <rules>", "description": "Remove specific rules instead of appending"},
                ],
            },
            {
                "command": "account",
                "description": "Show account info",
                "options": [],
            },
            {
                "command": "account usage",
                "description": "Show usage stats",
                "options": [
                    {"flag": "--start <ISO8601>", "description": "Start date filter"},
                    {"flag": "--end <ISO8601>", "description": "End date filter"},
                ],
            },
            {
                "command": "geos",
                "description": "List available geos",
                "options": [],
            },
            {
                "command": "help",
                "description": "Show this help",
                "options": [
                    {"flag": "--json", "description": "Output help as JSON"},
                ],
            },
        ],
    }
    output(help_data)


def print_help_and_exit(args: List[str]) -> NoReturn:
    """Print help and exit."""
    if "--json" in args:
        print_help_json()
    print_help()
    sys.exit(0)


async def main_async() -> None:
    """Main async entry point for CLI."""
    from .session import handle_session
    from .account import handle_account
    from .geos import handle_geos
    from .open import handle_open_daemon, OpenOptions
    from ..session.lock import validate_session_name
    
    args = sys.argv[1:]
    command = args[0] if args else ""
    
    # Internal: --daemon mode (spawned by `session start` in detached child)
    if command == "--daemon":
        from .session import parse_session_args
        
        parsed = parse_session_args(args[1:])
        
        if parsed.get("session_name") and not validate_session_name(parsed["session_name"]):
            output({
                "error": "Invalid session name. Use only letters, numbers, hyphens, and underscores."
            }, 1)
        
        if not parsed.get("url"):
            output({"error": "URL is required for daemon mode."}, 1)
        
        opts = OpenOptions(
            url=parsed["url"],
            connection_id=parsed.get("connection_id"),
            headless=not parsed.get("headed", False),
            session_name=parsed.get("session_name"),
            auto_unblock=parsed.get("auto_unblock", False),
            disable_block_detection=parsed.get("disable_block_detection", False),
            run=parsed.get("run"),
        )
        await handle_open_daemon(opts)
        return
    
    # Check for --help / -h anywhere in args
    wants_help = "--help" in args or "-h" in args
    
    if command == "session":
        if wants_help:
            print_help_and_exit(args)
        await handle_session(args[1:])
    elif command == "account":
        if wants_help:
            print_help_and_exit(args)
        await handle_account(args[1:])
    elif command == "geos":
        if wants_help:
            print_help_and_exit(args)
        await handle_geos()
    elif command in ("help", "--help", "-h", ""):
        print_help_and_exit(args)
    else:
        output({"error": f"Unknown command: '{command}'. Run 'aluvia help' for usage."}, 1)


def main() -> None:
    """Main entry point for CLI."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as err:
        output({"error": str(err)}, 1)


if __name__ == "__main__":
    main()
