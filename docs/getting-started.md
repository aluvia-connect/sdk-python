# Getting Started with Aluvia Python SDK

A step-by-step guide to installing, configuring, and running your first Aluvia-powered browser session in Python.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick start: CLI](#quick-start-cli)
- [Quick start: Programmatic](#quick-start-programmatic)
- [Quick start: MCP server](#quick-start-mcp-server)
- [Next steps](#next-steps)

---

## Prerequisites

- **Python 3.9+**
- **An Aluvia API key** — sign up at [dashboard.aluvia.io](https://dashboard.aluvia.io)

---

## Installation

```bash
pip install aluvia-sdk
```

`playwright` is an optional dependency — required only if you use browser sessions (`session start`, `connect()`, or Playwright integration). If you only need the REST API wrapper (`AluviaApi`) or the proxy client without a browser, you can skip it.

---

## Configuration

Set your API key as an environment variable:

```bash
export ALUVIA_API_KEY="your-api-key"
```

Or create a `.env` file in your project root:

```
ALUVIA_API_KEY=your-api-key
```

The SDK reads `ALUVIA_API_KEY` from the environment in CLI mode. In programmatic mode, pass the key directly to the constructor.

---
