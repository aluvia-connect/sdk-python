# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **MCP Server (Model Context Protocol)** - New `aluvia_mcp` package providing MCP server for AI agent frameworks
  - `aluvia-mcp` command-line binary for running the MCP server
  - 10 MCP tools: `session_start`, `session_close`, `session_list`, `session_get`, `session_rotate_ip`, `session_set_geo`, `session_set_rules`, `account_get`, `account_usage`, `geos_list`
  - Stdio transport support for MCP clients (Claude Desktop, Claude Code, Cursor, VS Code)
  - Complete documentation in `aluvia_mcp/README.md`
  - `capture_output()` helper in CLI for MCP tool integration using ContextVar for thread-safe concurrent tool calls

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
