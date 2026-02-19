#!/usr/bin/env python3
"""
Smoke test: run aluvia-mcp, send MCP initialize + tools/list, check response.

Usage (from sdk-python directory):
    python aluvia_mcp/test_stdio.py

Exits 0 if tools/list returns expected tools; 1 on failure or timeout.
"""
import sys
import json
import subprocess
import time


def main():
    # Start the MCP server
    proc = subprocess.Popen(
        [sys.executable, "-m", "aluvia_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    def send(obj):
        msg = json.dumps(obj) + "\n"
        proc.stdin.write(msg)
        proc.stdin.flush()
        print(f"SENT: {msg.strip()}", file=sys.stderr)
    
    def recv():
        line = proc.stdout.readline()
        if line:
            print(f"RECV: {line.strip()}", file=sys.stderr)
            return json.loads(line)
        return None
    
    try:
        # Step 1: Send initialize
        send({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            },
            "id": 1
        })
        
        # Wait for initialize response
        response = recv()
        if not response or response.get("id") != 1:
            print("FAIL: No initialize response", file=sys.stderr)
            return 1
        
        print(f"✓ Initialize OK", file=sys.stderr)
        
        # Step 2: Send initialized notification
        send({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        })
        
        # Step 3: Send tools/list
        send({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        })
        
        # Wait for tools/list response
        response = recv()
        if not response or not response.get("result", {}).get("tools"):
            print("FAIL: No tools/list response", file=sys.stderr)
            return 1
        
        # Check tools
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        expected = ["session_start", "session_list", "account_get", "geos_list"]
        
        ok = all(e in tool_names for e in expected)
        if ok:
            print(f"✓ OK: tools/list returned expected tools", file=sys.stderr)
            print(f"✓ Tools: {', '.join(tool_names)}", file=sys.stderr)
            return 0
        else:
            print(f"✗ FAIL: missing tools", file=sys.stderr)
            print(f"  Expected: {expected}", file=sys.stderr)
            print(f"  Got: {tool_names}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    sys.exit(main())
