"""
Entry point for running aluvia_mcp as a module.
Allows: python -m aluvia_mcp
"""
import asyncio
import sys
from .mcp_server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        print(f"Fatal error in MCP server: {err}", file=sys.stderr)
        sys.exit(1)
