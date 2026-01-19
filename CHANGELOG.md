# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
