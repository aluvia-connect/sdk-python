# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-02-18

### Added

- **MCP Server (Model Context Protocol)** - New `aluvia_mcp` package providing MCP server for AI agent frameworks
  - `aluvia-mcp` command-line binary for running the MCP server
  - 10 MCP tools: `session_start`, `session_close`, `session_list`, `session_get`, `session_rotate_ip`, `session_set_geo`, `session_set_rules`, `account_get`, `account_usage`, `geos_list`
  - Stdio transport support for MCP clients (Claude Desktop, Claude Code, Cursor, VS Code)
  - Complete documentation in `aluvia_mcp/README.md`
  - `capture_output()` helper in CLI for MCP tool integration using ContextVar for thread-safe concurrent tool calls
- **Core CLI (`aluvia` / `aluvia-sdk`)** - New command-line interfaces for managing Aluvia sessions and accounts
  - Supports creating, listing, rotating, and closing sessions from the terminal
  - Provides commands for inspecting account status, usage, and available geos
  - Designed for both direct human use and scripting/automation
- **Block Detection & Auto-Unblock** - Built-in detection of blocked sessions with automatic unblock / rotation
  - Detects common block signals from target sites and rotates IPs / sessions when needed
  - Configurable retry behavior to improve reliability for long-running scraping / automation jobs
- **Session Lock-File Management** - Lock files to coordinate access to shared sessions
  - Prevents concurrent processes from corrupting or competing over the same session
  - Ensures safe cleanup when sessions are closed or rotated
- **`connect()` Helper for Existing Sessions** - New `connect()` function for attaching to running sessions
  - Allows tools and scripts to reuse an already-running session instead of creating a new one
  - Improves performance and reduces resource usage for multi-step workflows
- **Browser Session Daemon Mode** - Long-lived browser session process for persistent automation
  - Runs a background daemon that maintains a browser session across multiple CLI or SDK invocations
  - Enables advanced use cases like warm sessions, shared cookies, and cross-command state
- **CLI Handler Exports** - Added clean import path `aluvia_sdk.bin` for CLI handlers (aligns with Node.js SDK structure)
  - Exports: `handle_session`, `handle_account`, `handle_geos`, `handle_open`, `OpenOptions`, `capture_output`, `ToolResult`
  - Enables cleaner imports for MCP tools and other integrations

### Changed

- **BREAKING**: Dropped Python 3.9 support - Minimum Python version is now 3.10
  - Python 3.9 reached end-of-life in October 2025
  - Required by the `mcp>=0.9.0` dependency in `aluvia-mcp` package

## [1.1.0] - 2026-02-04

### Added

- `start_playwright` parameter in `AluviaClient` constructor to automatically launch a Chromium browser with built-in proxy settings
- `connection.browser` property that provides access to the auto-launched Playwright browser instance
- Comprehensive test suite for Playwright integration (10 unit tests + integration tests)
- Updated README with auto-launch Playwright browser example and documentation
- Integration guides section in README

## [1.0.2] - 2026-01-19

### Fixed

- Renamed the httpx, requests and aiohttp adapters to match the docs

## [1.0.1] - 2026-01-15

### Fixed

- Fixed `connection_id` not being extracted from API response when creating new connections, which caused "Cannot update config without connection_id" errors when calling `update_target_geo()`, `update_session_id()`, or `update_rules()`

## [1.0.0] - 2026-01-12

### Added

- Initial release of Aluvia Python SDK
- `AluviaClient` class for managing local proxy and connections
- `AluviaApi` class for REST API wrapper
- Support for dynamic routing rules
- Session ID management
- Geo targeting support
- Integration adapters for:
  - Playwright
  - Selenium
  - httpx
  - requests
  - aiohttp
- Gateway mode and client proxy mode
- Automatic config polling with ETag support
- Comprehensive test suite
- Usage examples and documentation
