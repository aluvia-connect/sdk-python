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

## Aluvia client

The Aluvia client runs a local rules-based proxy server on your agent's host, handles authentication and connection management, and provides ready-to-use adapters for popular tools like Playwright, Selenium, and httpx.

Simply point your automation tool at the local proxy address (`127.0.0.1`) and the client handles the rest. For each request, the client checks the destination hostname against user-defined (or agent-defined) routing rules and decides whether to send it through Aluvia's mobile IPs or direct to the destination.

```
┌──────────────────┐      ┌──────────────────────────┐      ┌──────────────────────┐
│                  │      │                          │      │                      │
│    Your Agent    │─────▶     Aluvia Client         ─────▶  gateway.aluvia.io    │
│                  │      │     127.0.0.1:port       │      │    (Mobile IPs)      │
│                  │      │                          │      │                      │
└──────────────────┘      │  Per-request routing:    │      └──────────────────────┘
                          │                          │
                          │  not-blocked.com ──────────────▶ Direct
                          │  blocked-site.com ─────────────▶ Via Aluvia
                          │                          │
                          └──────────────────────────┘
```

**Benefits:**

- **Avoid blocks:** Websites flag datacenter IPs as bot traffic, leading to 403s, CAPTCHAs, and rate limits. Mobile IPs appear as real users, so requests go through.
- **Reduce costs and latency:** Hostname-based routing rules let you proxy only the sites that need it. Traffic to non-blocked sites goes direct, saving money and reducing latency.
- **Unblock without restarts:** Rules update at runtime. When a site blocks your agent, add it to the proxy rules and retry—no need to restart workers or redeploy.
- **Simplify integration:** One SDK with ready-to-use adapters for Playwright, Selenium, httpx, requests, and aiohttp.

---

## Quick start

### Understand the basics

- [What is Aluvia?](https://docs.aluvia.io/)
- [Understanding connections](https://docs.aluvia.io/fundamentals/connections)

### Get Aluvia API key

1. Create an account at [dashboard.aluvia.io](https://dashboard.aluvia.io)
2. Go to **API and SDKs** and get your **API Key**

### Install the SDK

```bash
pip install aluvia-sdk
```

**Requirements:** Python 3.9 or later

### Example: Dynamic unblocking with Playwright

This example shows how an agent can use the Aluvia client to dynamically unblock websites. It demonstrates starting the client, using the Playwright integration adapter, configuring geo targeting and session ID, detecting blocks, and updating routing rules on the fly.

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

    # Launch browser using the Playwright integration adapter
    # The adapter returns proxy settings in Playwright's expected format
    async with async_playwright() as p:
        browser = await p.chromium.launch(proxy=connection.as_playwright())

        # Track hostnames we've added to proxy rules
        proxied_hosts = set()

        async def visit_with_retry(url: str) -> str:
            page = await browser.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                hostname = url.split("//")[1].split("/")[0]

                # Detect if the site blocked us (403, 429, or challenge page)
                status = response.status if response else 0
                title = await page.title()
                is_blocked = status in (403, 429) or "blocked" in title.lower()

                if is_blocked and hostname not in proxied_hosts:
                    print(f"Blocked by {hostname} — adding to proxy rules")

                    # Update routing rules to proxy this hostname through Aluvia
                    # Rules update at runtime—no need to restart the browser
                    proxied_hosts.add(hostname)
                    await client.update_rules(list(proxied_hosts))

                    # Rotate to a fresh IP by changing the session ID
                    import time
                    await client.update_session_id(f"retry{int(time.time())}")

                    await page.close()
                    return await visit_with_retry(url)

                return await page.content()
            finally:
                await page.close()

        try:
            # First attempt goes direct; if blocked, retries through Aluvia
            html = await visit_with_retry("https://example.com/data")
            print("Success:", html[:200])
        finally:
            # Always close the browser and connection when done
            await browser.close()
            await connection.close()

asyncio.run(main())
```

---

## Architecture

The client is split into two independent **planes**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AluviaClient                             │
├─────────────────────────────┬───────────────────────────────────┤
│       Control Plane         │          Data Plane               │
│       (ConfigManager)       │          (ProxyServer)            │
├─────────────────────────────┼───────────────────────────────────┤
│ • Fetches/creates config    │ • Local HTTP proxy (proxy.py)     │
│ • Polls for updates (ETag)  │ • Per-request routing decisions   │
│ • PATCH updates (rules,     │ • Uses rules engine to decide:    │
│   session, geo)             │   direct vs gateway               │
└─────────────────────────────┴───────────────────────────────────┘
```

### Control Plane (ConfigManager)

- Communicates with the Aluvia REST API (`/account/connections/...`)
- Fetches proxy credentials and routing rules
- Polls for configuration updates
- Pushes updates (rules, session ID, geo)

### Data Plane (ProxyServer)

- Runs a local HTTP proxy on `127.0.0.1`
- For each request, uses the **rules engine** to decide whether to route direct or via Aluvia.
- Because the proxy reads the latest config per-request, rule updates take effect immediately

---

## Operating modes

The Aluvia client has two operating modes: **Client Proxy Mode** (default) and **Gateway Mode**.

### Client Proxy Mode

**How it works:** The SDK runs a local proxy on `127.0.0.1`. For each request, it checks your routing rules and sends traffic either direct or through Aluvia.

**Why use it:**

- Selective routing reduces cost and latency (only proxy what you need)
- Credentials stay inside the SDK (nothing secret in your config)
- Rule changes apply immediately (no restarts)

**Best for:** Using per-hostname routing rules.

### Gateway Mode

Set `local_proxy=False` to enable.

**How it works:** No local proxy. Your tools connect directly to `gateway.aluvia.io` and **ALL** traffic goes through Aluvia.

**Why use it:**

- No local process to manage
- Simpler setup for tools with native proxy auth support

**Best for:** When you want all traffic proxied without selective routing.

---

## Using Aluvia client

### 1. Create a client

```python
client = AluviaClient(
    api_key=os.environ["ALUVIA_API_KEY"],
    connection_id=123,  # Optional: reuse an existing connection
    local_proxy=True,   # Optional: default True (recommended)
)
```

### 2. Start the client and get a connection

```python
connection = await client.start()
```

This starts the local proxy and returns a connection object you'll use with your tools.

### 3. Use the connection with your tools

Pass the connection to your automation tool using the appropriate adapter:

```python
browser = await p.chromium.launch(proxy=connection.as_playwright())
```

### 4. Update routing as necessary

While your agent is running, you can update routing rules, rotate IPs, or change geo targeting—no restart needed:

```python
await client.update_rules(["blocked-site.com"])    # Add hostname to proxy rules
await client.update_session_id("newsession")       # Rotate to a new IP
await client.update_target_geo("us_ca")            # Target California IPs
```

### 5. Clean up when done

```python
await connection.close()  # Stops proxy, polling, and releases resources
```

---

## Routing rules

The Aluvia Client starts a local proxy server that routes each request based on hostname rules that you (or your agent) set. **Rules can be updated at runtime without restarting the agent.**

Traffic can be sent either:

- direct (using the agent's datacenter/cloud IP) or,
- through Aluvia's mobile proxy IPs,

### Benefits

- Selectively routing traffic to mobile proxies reduces proxy costs and connection latency.
- Rules can be updated during runtime, allowing agents to work around website blocks on the fly.

### Example rules

```python
await client.update_rules(["*"])                              # Proxy all traffic
await client.update_rules(["target-site.com", "*.google.com"]) # Proxy specific hosts
await client.update_rules(["*", "-api.stripe.com"])           # Proxy all except specified
await client.update_rules([])                                 # Route all traffic direct
```

### Supported routing rule patterns:

| Pattern         | Matches                               |
| --------------- | ------------------------------------- |
| `*`             | All hostnames                         |
| `example.com`   | Exact match                           |
| `*.example.com` | Subdomains of example.com             |
| `google.*`      | google.com, google.co.uk, and similar |
| `-example.com`  | Exclude from proxying                 |

---

## Dynamic unblocking

Most proxy solutions require you to decide upfront which sites to proxy. If a site blocks you later, you're stuck—restart your workers, redeploy your fleet, or lose the workflow.

**With Aluvia, your agent can unblock itself.** When a request fails with a 403 or 429, your agent adds that hostname to its routing rules and retries. The update takes effect immediately—no restart, no redeployment, no lost state.

This turns blocking from a workflow-ending failure into a minor speed bump.

```python
response = await page.goto(url)

if response and response.status in (403, 429):
    # Blocked! Add this hostname to proxy rules and retry
    hostname = url.split("//")[1].split("/")[0]
    await client.update_rules([*current_rules, hostname])
    await page.goto(url)  # This request goes through Aluvia
```

Your agent learns which sites need proxying as it runs. Sites that don't block you stay direct (faster, cheaper). Sites that do block you get routed through mobile IPs automatically.

---

## Tool integration adapters

Every tool has its own way of configuring proxies—Playwright wants a dict with server/username/password, Selenium wants a string, httpx wants an agent, and some tools don't support proxies at all. The SDK handles all of this for you:

| Tool       | Method                       | Returns                                                   |
| ---------- | ---------------------------- | --------------------------------------------------------- |
| Playwright | `connection.as_playwright()` | `{"server": "...", "username": "...", "password": "..."}` |
| Selenium   | `connection.as_selenium()`   | `"--proxy-server=..."`                                    |
| httpx      | `connection.as_httpx()`      | `httpx.HTTPTransport(proxy=...)`                          |
| requests   | `connection.as_requests()`   | `{"http": "...", "https": "..."}`                         |
| aiohttp    | `connection.as_aiohttp()`    | `"http://username:password@host:port"`                    |

---

## Aluvia API

`AluviaApi` is a typed wrapper for the Aluvia REST API. Use it to manage connections, query account info, or build custom tooling—without starting a proxy.

### What you can do

| Endpoint                             | Description                             |
| ------------------------------------ | --------------------------------------- |
| `api.account.get()`                  | Get account info (balance, usage)       |
| `api.account.connections.list()`     | List all connections                    |
| `api.account.connections.create()`   | Create a new connection                 |
| `api.account.connections.get(id)`    | Get connection details                  |
| `api.account.connections.patch(id)`  | Update connection (rules, geo, session) |
| `api.account.connections.delete(id)` | Delete a connection                     |
| `api.geos.list()`                    | List available geo-targeting options    |

### Example

```python
from aluvia_sdk import AluviaApi

api = AluviaApi(api_key=os.environ["ALUVIA_API_KEY"])

# Check account balance
account = await api.account.get()
print(f"Balance: {account['balance_gb']} GB")

# Create a connection for a new agent
connection = await api.account.connections.create(
    description="pricing-scraper",
    rules=["competitor-site.com"],
    target_geo="us_ca",
)
print(f"Created: {connection['connection_id']}")

# List available geos
geos = await api.geos.list()
print("Geos:", [g["code"] for g in geos])
```

**Tip:** `AluviaApi` is also available as `client.api` when using `AluviaClient`.

---

## License

MIT — see [LICENSE](./LICENSE)
