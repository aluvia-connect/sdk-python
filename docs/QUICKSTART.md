# Quick Start Guide

## Installation

```bash
pip install aluvia-sdk
```

## Basic Usage

### 1. Import and Initialize

```python
import asyncio
from aluvia_sdk import AluviaClient

async def main():
    # Initialize with your API key
    client = AluviaClient(api_key="your-api-key")

    # Start the client
    connection = await client.start()

    # Your code here...

    # Clean up
    await connection.close()

asyncio.run(main())
```

### 2. Using with Playwright

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        proxy=connection.as_playwright()
    )
    page = await browser.new_page()
    await page.goto("https://example.com")
    # ...
    await browser.close()
```

### 3. Using with httpx

```python
import httpx

async with httpx.AsyncClient(proxies=connection.as_httpx_proxies()) as client:
    response = await client.get("https://example.com")
    print(response.status_code)
```

### 4. Dynamic Routing Rules

```python
# Update rules at runtime
await client.update_rules(["example.com", "*.google.com"])

# Update session ID (rotate IP)
await client.update_session_id("new-session")

# Update geo targeting
await client.update_target_geo("us_ca")
```

## Configuration Options

```python
client = AluviaClient(
    api_key="your-api-key",
    api_base_url="https://api.aluvia.io/v1",  # API base URL
    poll_interval_ms=5000,                     # Config poll interval
    gateway_protocol="http",                   # "http" or "https"
    gateway_port=8080,                         # Gateway port
    local_port=None,                           # Local proxy port (auto)
    log_level="info",                          # "silent", "info", "debug"
    connection_id=None,                        # Existing connection ID
    local_proxy=True,                          # Enable local proxy
    strict=True,                               # Strict error handling
)
```

## Operating Modes

### Client Proxy Mode (Default)

Runs a local proxy that routes traffic based on rules:

```python
client = AluviaClient(api_key="key", local_proxy=True)
```

### Gateway Mode

Connects directly to Aluvia gateway (all traffic proxied):

```python
client = AluviaClient(api_key="key", local_proxy=False)
```

## API Usage

```python
from aluvia_sdk import AluviaApi

api = AluviaApi(api_key="your-api-key")

# Get account info
account = await api.account.get()

# List connections
connections = await api.account.connections.list()

# Create connection
conn = await api.account.connections.create(
    description="my-agent",
    rules=["example.com"],
)

# Update connection
updated = await api.account.connections.patch(
    connection_id=conn["connection_id"],
    rules=["example.com", "google.com"],
)

# Delete connection
await api.account.connections.delete(conn["connection_id"])

await api.close()
```

## Examples

See the `examples/` directory for complete working examples:

- `playwright_example.py` - Basic Playwright integration
- `dynamic_unblocking.py` - Dynamic unblocking on 403/429
- `httpx_example.py` - Using httpx HTTP client
- `api_example.py` - Direct API usage

## Troubleshooting

### "Missing API key" error

Make sure you're passing a valid API key to the constructor.

### Connection fails to start

Check that your API key is valid and you have network connectivity to api.aluvia.io.

### Proxy not routing correctly

Verify your routing rules with `client.update_rules()`.

## Support

- Documentation: https://docs.aluvia.io
- GitHub Issues: https://github.com/aluvia-connect/sdk-python/issues
- Email: support@aluvia.io
