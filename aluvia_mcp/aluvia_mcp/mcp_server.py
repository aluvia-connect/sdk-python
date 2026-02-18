#!/usr/bin/env python3
"""
Aluvia MCP Server

A Model Context Protocol server that exposes Aluvia CLI functionality as structured tools
for AI agents. Runs on stdio transport (stdin/stdout JSON-RPC).
"""
import sys
import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import Field

from . import mcp_tools


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("aluvia")
    
    # --- Session tools ---
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="session_start",
                description="Start a browser session with Aluvia smart proxy. Spawns a headless browser connected through Aluvia gateway. Returns session details including CDP URL for remote debugging.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to open in the browser"
                        },
                        "connectionId": {
                            "type": "integer",
                            "description": "Use a specific Aluvia connection ID",
                            "minimum": 1
                        },
                        "headful": {
                            "type": "boolean",
                            "description": "Run browser in headful mode (default: headless)"
                        },
                        "browserSession": {
                            "type": "string",
                            "description": "Custom session name (auto-generated if omitted)"
                        },
                        "autoUnblock": {
                            "type": "boolean",
                            "description": "Auto-detect blocks and reload through Aluvia proxy"
                        },
                        "disableBlockDetection": {
                            "type": "boolean",
                            "description": "Disable block detection entirely"
                        }
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="session_close",
                description="Close one or all running browser sessions. Sends SIGTERM for graceful shutdown, then SIGKILL if needed.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browserSession": {
                            "type": "string",
                            "description": "Name of session to close (auto-selects if only one)"
                        },
                        "all": {
                            "type": "boolean",
                            "description": "Close all sessions"
                        }
                    }
                }
            ),
            Tool(
                name="session_list",
                description="List all active browser sessions with their PIDs, URLs, and proxy configuration.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="session_get",
                description="Get detailed information about a running session including proxy URLs, connection data, and block detection state.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browserSession": {
                            "type": "string",
                            "description": "Name of session (auto-selects if only one)"
                        }
                    }
                }
            ),
            Tool(
                name="session_rotate_ip",
                description="Rotate the IP address for a running session by generating a new session ID on the Aluvia connection.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browserSession": {
                            "type": "string",
                            "description": "Name of session (auto-selects if only one)"
                        }
                    }
                }
            ),
            Tool(
                name="session_set_geo",
                description="Set or clear the target geographic region for a running session. Affects which mobile IP pool is used.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "geo": {
                            "type": "string",
                            "description": 'Geo code to set (e.g. "US", "GB")'
                        },
                        "clear": {
                            "type": "boolean",
                            "description": "Clear the target geo instead of setting one"
                        },
                        "browserSession": {
                            "type": "string",
                            "description": "Name of session (auto-selects if only one)"
                        }
                    }
                }
            ),
            Tool(
                name="session_set_rules",
                description='Append or remove proxy routing rules for a running session. Rules are hostname patterns (e.g. "example.com", "*.google.com").',
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rules": {
                            "type": "string",
                            "description": 'Comma-separated rules to append (e.g. "a.com,b.com")'
                        },
                        "remove": {
                            "type": "string",
                            "description": "Comma-separated rules to remove instead of appending"
                        },
                        "browserSession": {
                            "type": "string",
                            "description": "Name of session (auto-selects if only one)"
                        }
                    }
                }
            ),
            Tool(
                name="account_get",
                description="Get Aluvia account information including plan details and current balance.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="account_usage",
                description="Get Aluvia account usage statistics for a date range.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "string",
                            "description": 'Start date filter (ISO8601 format, e.g. "2024-01-01T00:00:00Z")'
                        },
                        "end": {
                            "type": "string",
                            "description": "End date filter (ISO8601 format)"
                        }
                    }
                }
            ),
            Tool(
                name="geos_list",
                description="List all available geographic regions for proxy targeting.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            # Map tool names to functions
            tool_map = {
                "session_start": mcp_tools.session_start,
                "session_close": mcp_tools.session_close,
                "session_list": mcp_tools.session_list,
                "session_get": mcp_tools.session_get,
                "session_rotate_ip": mcp_tools.session_rotate_ip,
                "session_set_geo": mcp_tools.session_set_geo,
                "session_set_rules": mcp_tools.session_set_rules,
                "account_get": mcp_tools.account_get,
                "account_usage": mcp_tools.account_usage,
                "geos_list": mcp_tools.geos_list,
            }
            
            if name not in tool_map:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]
            
            # Convert camelCase to snake_case for Python function arguments
            snake_case_args = {}
            for key, value in arguments.items():
                # Convert camelCase to snake_case
                snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                snake_case_args[snake_key] = value
            
            # Call the tool function
            result = await tool_map[name](**snake_case_args)
            
            return [TextContent(
                type="text",
                text=json.dumps(result["data"], indent=2)
            )]
        
        except Exception as err:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(err)})
            )]
    
    return server


async def main() -> None:
    """Main entry point for the MCP server."""
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        print(f"Fatal error in MCP server: {err}", file=sys.stderr)
        sys.exit(1)
