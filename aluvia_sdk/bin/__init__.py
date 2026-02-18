"""
CLI package for Aluvia SDK

Exports CLI handlers for use by MCP server and other integrations.
This module provides a clean import path similar to @aluvia/sdk/cli in Node.js.
"""

from .session import handle_session
from .account import handle_account
from .geos import handle_geos
from .open import handle_open, OpenOptions
from .cli import capture_output, ToolResult

__all__ = [
    "handle_session",
    "handle_account",
    "handle_geos",
    "handle_open",
    "OpenOptions",
    "capture_output",
    "ToolResult",
]
