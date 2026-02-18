#!/usr/bin/env python3
"""
Aluvia MCP Server

A Model Context Protocol server that exposes Aluvia CLI functionality as structured tools
for AI agents. Runs on stdio transport (stdin/stdout JSON-RPC).

Accepts tool calls without strict initialization to match Node.js SDK behavior.
"""
import sys
import json
import asyncio
from typing import Any, Dict
from . import mcp_tools


# Map tool names to their handler functions
TOOLS = {
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

# Tool definitions for tools/list
TOOL_DEFINITIONS = [
    {
        "name": "session_start",
        "description": "Start a browser session with Aluvia smart proxy. Spawns a headless browser connected through Aluvia gateway. Returns session details including CDP URL for remote debugging.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open in the browser"},
                "connectionId": {"type": "integer", "description": "Use a specific Aluvia connection ID", "minimum": 1},
                "headful": {"type": "boolean", "description": "Run browser in headful mode (default: headless)"},
                "browserSession": {"type": "string", "description": "Custom session name (auto-generated if omitted)"},
                "autoUnblock": {"type": "boolean", "description": "Auto-detect blocks and reload through Aluvia proxy"},
                "disableBlockDetection": {"type": "boolean", "description": "Disable block detection entirely"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "session_close",
        "description": "Close one or all running browser sessions. Sends SIGTERM for graceful shutdown, then SIGKILL if needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "browserSession": {"type": "string", "description": "Name of session to close (auto-selects if only one)"},
                "all": {"type": "boolean", "description": "Close all sessions"}
            }
        }
    },
    {
        "name": "session_list",
        "description": "List all active browser sessions with their PIDs, URLs, and proxy configuration.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "session_get",
        "description": "Get detailed information about a running session including proxy URLs, connection data, and block detection state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "browserSession": {"type": "string", "description": "Name of session (auto-selects if only one)"}
            }
        }
    },
    {
        "name": "session_rotate_ip",
        "description": "Rotate the IP address for a running session by generating a new session ID on the Aluvia connection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "browserSession": {"type": "string", "description": "Name of session (auto-selects if only one)"}
            }
        }
    },
    {
        "name": "session_set_geo",
        "description": "Set or clear the target geographic region for a running session. Affects which mobile IP pool is used.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "geo": {"type": "string", "description": 'Geo code to set (e.g. "US", "GB")'},
                "clear": {"type": "boolean", "description": "Clear the target geo instead of setting one"},
                "browserSession": {"type": "string", "description": "Name of session (auto-selects if only one)"}
            }
        }
    },
    {
        "name": "session_set_rules",
        "description": 'Append or remove proxy routing rules for a running session. Rules are hostname patterns (e.g. "example.com", "*.google.com").',
        "inputSchema": {
            "type": "object",
            "properties": {
                "rules": {"type": "string", "description": 'Comma-separated rules to append (e.g. "a.com,b.com")'},
                "remove": {"type": "string", "description": "Comma-separated rules to remove instead of appending"},
                "browserSession": {"type": "string", "description": "Name of session (auto-selects if only one)"}
            }
        }
    },
    {
        "name": "account_get",
        "description": "Get Aluvia account information including plan details and current balance.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "account_usage",
        "description": "Get Aluvia account usage statistics for a date range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": 'Start date filter (ISO8601 format, e.g. "2024-01-01T00:00:00Z")'},
                "end": {"type": "string", "description": "End date filter (ISO8601 format)"}
            }
        }
    },
    {
        "name": "geos_list",
        "description": "List all available geographic regions for proxy targeting.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a JSON-RPC request."""
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params", {})
    
    # Handle initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "experimental": {},
                    "tools": {"listChanged": False}
                },
                "serverInfo": {"name": "aluvia", "version": "1.0.0"}
            }
        }
    
    # Handle notifications/initialized (no response needed)
    if method == "notifications/initialized":
        return None
    
    # Handle tools/list
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOL_DEFINITIONS}
        }
    
    # Handle tools/call
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        try:
            # Call the tool
            tool_func = TOOLS[tool_name]
            result = await tool_func(**arguments)
            
            # Format response to match Node.js output
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.get("data"), indent=2)
                        }
                    ],
                    "isError": result.get("isError", False)
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }


async def main() -> None:
    """Main entry point for the MCP server."""
    print("Aluvia MCP server running on stdio", file=sys.stderr)
    
    # Read from stdin line by line
    loop = asyncio.get_event_loop()
    
    async def read_stdin():
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = await handle_request(request)
                
                # Send response if not None (some methods don't require response)
                if response is not None:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
    
    try:
        await read_stdin()
    except KeyboardInterrupt:
        pass


def run() -> None:
    """Synchronous entry point for script execution."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    run()
