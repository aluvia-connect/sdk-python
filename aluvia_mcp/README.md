# Aluvia MCP Server

<p align="center">
  <strong>Unblockable browser automation for AI agents.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/aluvia-sdk/"><img src="https://img.shields.io/pypi/v/aluvia-sdk.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/aluvia-sdk/"><img src="https://img.shields.io/pypi/pyversions/aluvia-sdk.svg" alt="Python versions"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/pypi/l/aluvia-sdk.svg" alt="license"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-1.0-compatible?labelColor=2d2d2d&color=5f5f5f" alt="MCP compatible"></a>
</p>

---

**Stop getting blocked.** The Aluvia MCP server exposes browser session management, geo-targeting, and account operations as [Model Context Protocol](https://modelcontextprotocol.io) tools for AI agents. Route traffic through premium US mobile carrier IPs and bypass 403s, CAPTCHAs, and WAFs that stop other tools. Works with Claude Desktop, Claude Code, Cursor, VS Code, and any MCP-compatible client.

## Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Client Configuration](#client-configuration)
- [Available Tools](#available-tools)
- [Use Cases](#use-cases)
- [Why Aluvia](#why-aluvia)
- [Links](#links)
- [License](#license)

---

## Quick Start

```bash
pip install aluvia-sdk mcp
export ALUVIA_API_KEY="your-api-key"
python -m aluvia_mcp.mcp_server
```

Get your API key at [dashboard.aluvia.io](https://dashboard.aluvia.io). The server runs on **stdio** (stdin/stdout JSON-RPC) — MCP clients spawn it and communicate over stdio.

---

## Requirements

- **Python** 3.9+
- **Aluvia API key** — sign up at [dashboard.aluvia.io](https://dashboard.aluvia.io)
- **Playwright** (optional) — required for browser sessions: `pip install playwright && playwright install chromium`

---

## Installation

```bash
pip install aluvia-sdk mcp
```

Or install with all optional dependencies:

```bash
pip install "aluvia-sdk[playwright]" mcp
playwright install chromium
```

Set your API key:

```bash
export ALUVIA_API_KEY="your-api-key"
```

---

## Client Configuration

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "aluvia": {
      "command": "python",
      "args": ["-m", "aluvia_mcp.mcp_server"],
      "env": {
        "ALUVIA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Claude Code (VS Code Extension)

Add to your VS Code settings (`.vscode/settings.json` or User Settings):

```json
{
  "mcp.servers": {
    "aluvia": {
      "command": "python",
      "args": ["-m", "aluvia_mcp.mcp_server"],
      "env": {
        "ALUVIA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "aluvia": {
      "command": "python",
      "args": ["-m", "aluvia_mcp.mcp_server"],
      "env": {
        "ALUVIA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Generic MCP Client

Any MCP-compatible client can use the server by spawning it with stdio transport:

```python
import subprocess
import json

proc = subprocess.Popen(
    ["python", "-m", "aluvia_mcp.mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    env={"ALUVIA_API_KEY": "your-api-key"}
)

# Send JSON-RPC requests to proc.stdin
# Read JSON-RPC responses from proc.stdout
```

---

## Available Tools

### Session Management

- **`session_start`** — Start a browser session with Aluvia smart proxy
- **`session_close`** — Close one or all running sessions
- **`session_list`** — List all active sessions
- **`session_get`** — Get detailed session info (CDP URL, proxy config, block detection state)
- **`session_rotate_ip`** — Rotate IP address for a session
- **`session_set_geo`** — Set or clear target geographic region
- **`session_set_rules`** — Add or remove proxy routing rules

### Account Management

- **`account_get`** — Get account info (plan, balance)
- **`account_usage`** — Get usage statistics for a date range

### Geo-Targeting

- **`geos_list`** — List available geographic regions

---

## Use Cases

### 1. **AI Agent Web Scraping**

AI agents need to scrape data from websites that block automated traffic. Aluvia routes requests through mobile IPs, making them appear as real users.

**Example workflow:**

1. Agent calls `session_start` with `--auto-unblock` to launch a browser
2. Agent navigates to target websites
3. If blocked, Aluvia detects it and automatically reroutes through mobile IPs
4. Agent extracts data successfully
5. Agent calls `session_close` when done

### 2. **Multi-Region Testing**

Test how websites behave for users in different US regions.

**Example workflow:**

1. Agent calls `geos_list` to see available regions
2. Agent calls `session_start` and then `session_set_geo` with `us_ca` for California IPs
3. Agent verifies location-specific content
4. Agent calls `session_set_geo` with `us_ny` to switch to New York IPs
5. Agent compares results

### 3. **Dynamic Unblocking**

Agent adapts to blocks in real-time without restarting.

**Example workflow:**

1. Agent calls `session_start` without proxy rules (all traffic goes direct)
2. Agent encounters a block on `example.com`
3. Agent calls `session_set_rules` with `"example.com"` to add it to proxy rules
4. Agent retries the request — now routed through Aluvia
5. Request succeeds

---

## Why Aluvia

**The Problem:** Websites block datacenter IPs (AWS, GCP, Azure) because they're commonly used by bots. This breaks AI agents that need web access.

**The Solution:** Aluvia routes traffic through **real US mobile carrier IPs** — the same IPs used by millions of people on AT&T, T-Mobile, and Verizon. Websites can't distinguish these requests from legitimate mobile users.

**Key Features:**

- **Automatic block detection** — detects 403s, CAPTCHAs, WAFs, and Cloudflare challenges
- **Auto-unblocking** — when blocked, Aluvia reroutes through mobile IPs and reloads the page
- **Smart routing** — only proxy sites that need it; everything else goes direct (saves cost and latency)
- **Runtime rule updates** — add sites to proxy rules on the fly, no restarts
- **IP rotation** — rotate IPs or target specific US regions at runtime
- **CDP debugging** — get Chrome DevTools Protocol URLs for remote debugging

---

## Links

- **Homepage:** [aluvia.io](https://aluvia.io)
- **Documentation:** [docs.aluvia.io](https://docs.aluvia.io)
- **Dashboard:** [dashboard.aluvia.io](https://dashboard.aluvia.io)
- **GitHub (Node.js SDK):** [github.com/aluvia-connect/sdk-node](https://github.com/aluvia-connect/sdk-node)
- **GitHub (Python SDK):** [github.com/aluvia-connect/sdk-python](https://github.com/aluvia-connect/sdk-python)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## License

MIT License — see [LICENSE](../LICENSE) for details.
