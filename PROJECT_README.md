# Aluvia Python SDK

Complete Python port of the Aluvia Node.js SDK.

## Project Structure

```
sdk-python/
├── aluvia_sdk/              # Main package
│   ├── __init__.py          # Public exports
│   ├── errors.py            # Exception classes
│   ├── py.typed             # Type hints marker
│   ├── api/                 # API layer
│   │   ├── __init__.py
│   │   ├── aluvia_api.py    # AluviaApi class
│   │   ├── account.py       # Account endpoints
│   │   ├── geos.py          # Geo endpoints
│   │   ├── request.py       # HTTP request core
│   │   └── types.py         # API type definitions
│   └── client/              # Client layer
│       ├── __init__.py
│       ├── aluvia_client.py # AluviaClient class
│       ├── config_manager.py# ConfigManager
│       ├── proxy_server.py  # ProxyServer
│       ├── adapters.py      # Tool adapters
│       ├── rules.py         # Rules engine
│       ├── logger.py        # Logging
│       └── types.py         # Client types
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_rules.py
│   ├── test_aluvia_api.py
│   └── test_aluvia_client.py
├── examples/                # Usage examples
│   ├── playwright_example.py
│   ├── dynamic_unblocking.py
│   ├── httpx_example.py
│   └── api_example.py
├── docs/                    # Documentation
│   └── QUICKSTART.md
├── pyproject.toml           # Package configuration
├── requirements.txt         # Dependencies
├── requirements-dev.txt     # Dev dependencies
├── README.md               # Main documentation
├── LICENSE                 # MIT License
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guide
├── SECURITY.md            # Security policy
├── Makefile               # Build commands
└── verify_install.py      # Installation verification
```

## Development Setup

1. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Run tests:

```bash
pytest
```

4. Verify installation:

```bash
python verify_install.py
```

## Key Features Implemented

### AluviaClient

- ✅ Client initialization with API key validation
- ✅ Start/stop lifecycle management
- ✅ Local proxy server (HTTP/HTTPS) using aiohttp
- ✅ Config polling with ETag support
- ✅ Hostname-based routing rules
- ✅ Dynamic rule updates
- ✅ Session ID management
- ✅ Geo targeting support
- ✅ Gateway mode (no local proxy)
- ✅ Tool adapters (Playwright, Selenium, httpx, requests, aiohttp)

### AluviaApi

- ✅ API wrapper initialization
- ✅ Account endpoints (get, usage, payments)
- ✅ Connection endpoints (list, create, get, patch, delete)
- ✅ Geo endpoints (list)
- ✅ Low-level request method
- ✅ Error handling
- ✅ ETag support

### Rules Engine

- ✅ Pattern matching (\*, exact, subdomain, TLD wildcards)
- ✅ Negative patterns (exclusions)
- ✅ should_proxy() function

## Dependencies

### Core Dependencies

- **httpx** (>=0.24.0) - Async HTTP client with proxy support
- **aiohttp** (>=3.8.0) - Async HTTP server for local proxy

### Optional Dependencies

- **playwright** (>=1.40.0) - For Playwright integration
- **selenium** (>=4.0.0) - For Selenium integration

### Dev Dependencies

- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **mypy** - Type checking
- **black** - Code formatting
- **isort** - Import sorting

## Differences from Node.js Version

1. **Async by default**: Fully async using asyncio
2. **Context managers**: Uses `async with` for resource management
3. **Type hints**: Native Python type hints instead of TypeScript
4. **Proxy implementation**: Custom aiohttp-based proxy server
5. **Package structure**: Python package conventions

## Testing

Run tests:

```bash
make test
```

Run with coverage:

```bash
make test-cov
```

Format code:

```bash
make format
```

Type check:

```bash
make typecheck
```

## Building and Publishing

Build package:

```bash
make build
```

Publish to PyPI:

```bash
make publish
```

## Usage Examples

See `examples/` directory for complete examples:

- Basic Playwright integration
- Dynamic unblocking
- httpx HTTP client usage
- Direct API usage

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MIT - See LICENSE file
