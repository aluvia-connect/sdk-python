#!/usr/bin/env python3
"""
Simple test to verify MCP server can be imported and initialized.

Usage:
    # First, install in development mode:
    cd aluvia_mcp
    pip install -e .
    
    # Then run the test:
    python test_mcp_import.py

This script verifies that the MCP server module structure is correct
and can be imported without errors.
"""

import sys


def test_import():
    """Test that aluvia_mcp module can be imported."""
    print("Testing aluvia_mcp module import...")
    print("(If this fails, make sure you've run: cd aluvia_mcp && pip install -e .)\n")
    
    try:
        import aluvia_mcp
        print("✓ aluvia_mcp package imported successfully")
        print(f"  Version: {aluvia_mcp.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import aluvia_mcp: {e}")
        print("\n  To fix: cd aluvia_mcp && pip install -e .")
        return False
    
    try:
        from aluvia_mcp import mcp_tools
        print("✓ aluvia_mcp.mcp_tools imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import mcp_tools: {e}")
        return False
    
    try:
        # Check that all tool functions exist
        required_tools = [
            'session_start', 'session_close', 'session_list', 'session_get',
            'session_rotate_ip', 'session_set_geo', 'session_set_rules',
            'account_get', 'account_usage', 'geos_list'
        ]
        
        for tool_name in required_tools:
            if not hasattr(mcp_tools, tool_name):
                print(f"✗ Missing tool function: {tool_name}")
                return False
        
        print(f"✓ All {len(required_tools)} tool functions found")
    except Exception as e:
        print(f"✗ Error checking tool functions: {e}")
        return False
    
    print("\n✓ All import tests passed!")
    print("\nNote: To run the MCP server, you need to install the MCP library:")
    print("  pip install 'aluvia-sdk[mcp]'")
    print("\nThen run:")
    print("  export ALUVIA_API_KEY='your-api-key'")
    print("  aluvia-mcp")
    
    return True


if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)
