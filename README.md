# Aluvia Python SDK

[![PyPI](https://img.shields.io/pypi/v/aluvia-sdk.svg)](https://pypi.org/project/aluvia-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/aluvia-sdk.svg)](https://pypi.org/project/aluvia-sdk/)
[![License](https://img.shields.io/pypi/l/aluvia-sdk.svg)](./LICENSE)

## Introduction

AI agents require reliable web access, yet they often encounter 403 blocks, CAPTCHAs, and rate limits. Real humans don't live in datacenters, so websites often treat agent coming from datacenter/cloud IPs as suspicious.

**Aluvia solves this problem** by connecting agents to the web through premium mobile IPs on US carrier networks. Unlike datacenter IPs, these reputable IPs are used by real humans, and they don't get blocked by websites.

**This Python SDK** makes it simple to integrate Aluvia into your agent workflow. There are two key components:

1. `AluviaClient` - a local client for connecting to Aluvia.
2. `AluviaApi` - a lightweight Python wrapper for the Aluvia REST API.

---

## Quick Start

### Installation

```bash
pip install aluvia-sdk
```

**Requirements:** Python 3.9 or later

### Get Aluvia API Key

1. Create an account at [dashboard.aluvia.io](https://dashboard.aluvia.io)
2. Go to **API and SDKs** and get your **API Key**

### Example: Dynamic unblocking with Playwright

```python
import asyncio
from playwright.async_api import async_playwright
from aluvia_sdk import AluviaClient

async def main():
    # Initialize the Aluvia client with your API key
    client = AluviaClient(api_key="your-api-key")

    # Start the client (launches local proxy, fetches connection config)
    connection = await client.start()

    # Configure geo targeting (use California IPs)
    await client.update_target_geo("us_ca")

    # Set session ID (requests with the same session ID use the same IP)
    await client.update_session_id("agentsession1")

    # Track hostnames we've added to proxy rules
    proxied_hosts = set()

    async with async_playwright() as p:
        # Launch browser using the Playwright integration adapter
        browser = await p.chromium.launch(proxy=connection.as_playwright())

        async def visit_with_retry(url: str) -> str:
            page = await browser.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                hostname = url.split("//")[1].split("/")[0]

                # Detect if the site blocked us
                status = response.status if response else 0
                title = await page.title()
                is_blocked = status in (403, 429) or "blocked" in title.lower()

                if is_blocked and hostname not in proxied_hosts:
                    print(f"Blocked by {hostname} — adding to proxy rules")

                    # Update routing rules to proxy this hostname
                    proxied_hosts.add(hostname)
                    await client.update_rules(list(proxied_hosts))

                    # Rotate to a fresh IP
                    await client.update_session_id(f"retry-{asyncio.get_event_loop().time()}")

                    await page.close()
                    return await visit_with_retry(url)

                return await page.content()
            finally:
                await page.close()

        try:
            html = await visit_with_retry("https://example.com/data")
            print("Success:", html[:200])
        finally:
            await browser.close()
            await connection.close()

asyncio.run(main())
```

---

## Features

- **Avoid blocks:** Websites flag datacenter IPs as bot traffic. Mobile IPs appear as real users.
- **Reduce costs and latency:** Hostname-based routing rules let you proxy only the sites that need it.
- **Unblock without restarts:** Rules update at runtime. Add sites to proxy rules and retry—no restart needed.
- **Simplify integration:** Ready-to-use adapters for Playwright, Selenium, httpx, requests, and aiohttp.

---

## Documentation

- [Client Technical Guide](docs/client-technical-guide.md)
- [API Technical Guide](docs/api-technical-guide.md)
- [Integration Guides](docs/integrations/)

---

## License

MIT — see [LICENSE](./LICENSE)
