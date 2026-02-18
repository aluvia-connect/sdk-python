# MCP Server Guide (Python)

A complete reference for the Aluvia MCP (Model Context Protocol) server — an MCP-compatible interface that exposes all Aluvia CLI functionality as structured tools for AI agents.

## Table of Contents

- [Overview](#overview)
- [Installation and setup](#installation-and-setup)
- [Client configuration](#client-configuration)
  - [Claude Desktop](#claude-desktop)
  - [Claude Code](#claude-code)
  - [Generic MCP client](#generic-mcp-client)
- [Tool reference](#tool-reference)
  - [Session tools](#session-tools)
  - [Account tools](#account-tools)
  - [Geo tools](#geo-tools)
- [Architecture](#architecture)
- [Error handling](#error-handling)

---

## Overview

The Aluvia MCP server implements the [Model Context Protocol](https://modelcontextprotocol.io) over stdio transport. It exposes browser session management, account operations, and geo-targeting as structured MCP tools that AI agents can invoke programmatically.

**Binary:** `aluvia-mcp`

**Transport:** stdio (stdin/stdout JSON-RPC)

**Server name:** `aluvia`

**Version:** Matches the `aluvia-mcp` package version

---

## Installation and setup

For MCP only (recommended if you only need the MCP server):

```bash
pip install aluvia-mcp
```

For the full SDK (CLI + programmatic API + MCP):

```bash
pip install aluvia-sdk[mcp]
```

Set the API key:

```bash
export ALUVIA_API_KEY="your-api-key"
```
