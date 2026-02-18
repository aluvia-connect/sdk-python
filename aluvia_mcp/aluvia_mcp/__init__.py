"""
Aluvia MCP Server

A Model Context Protocol server that exposes Aluvia CLI functionality
as structured tools for AI agents.
"""

__version__ = "1.0.0"

from . import mcp_tools
from .mcp_server import create_server, main

__all__ = ["mcp_tools", "create_server", "main"]
