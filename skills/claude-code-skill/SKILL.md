---
name: aluvia-claude-code
description: "Unblock web requests using Aluvia mobile carrier proxies. Use when hitting 403 Forbidden, Cloudflare challenges, CAPTCHAs, rate limits (429), IP bans, WAF blocks, empty responses, or when websites detect and block automated traffic. Routes traffic through real US mobile carrier IPs (AT&T, T-Mobile, Verizon) so websites treat your agent like a human."
allowed-tools: Bash(aluvia *)
---

# Aluvia Proxy: Unblock Web Requests with Mobile Carrier Proxies

## The Problem

Anti-bot systems block cloud-based and datacenter traffic. You get 403 Forbidden, CAPTCHAs, 429 rate limits, IP bans, or empty responses.

## The Solution

Aluvia routes traffic through **real US mobile carrier IPs** — the same IPs used by millions of people on their phones. Websites cannot distinguish your requests from legitimate mobile users.

The CLI manages headless Chromium sessions with automatic block detection and bypass. Every command returns structured JSON to stdout.

## Prerequisites Check

Before using any command, verify the environment:

```bash
# 1. Check API key is set (never log the full value)
echo "${ALUVIA_API_KEY:0:8}..."

# 2. Verify the CLI binary is available
aluvia help --json

# 3. Verify Playwright is installed (required for browser sessions)
python -c "import playwright"
```

If the API key is missing, tell the user to set `ALUVIA_API_KEY` from the [Aluvia dashboard](https://dashboard.aluvia.io). If `aluvia` is not found, run `pip install aluvia-sdk`. If Playwright is missing, run `pip install playwright`.

## Core Commands Quick Reference

| Command                     | Purpose                              | Example                                                                             |
| --------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------- |
| `session start <url>`       | Launch a headless browser session    | `aluvia session start https://example.com --auto-unblock --browser-session my-task` |
| `session close`             | Stop a running session               | `aluvia session close --browser-session my-task`                                    |
| `session list`              | List all active sessions             | `aluvia session list`                                                               |
| `session get`               | Get session details + block status   | `aluvia session get --browser-session my-task`                                      |
| `session rotate-ip`         | Rotate to a new upstream IP          | `aluvia session rotate-ip --browser-session my-task`                                |
| `session set-geo <geo>`     | Target IPs from a US region          | `aluvia session set-geo us_ca --browser-session my-task`                            |
| `session set-rules <rules>` | Add hostnames to proxy routing       | `aluvia session set-rules "example.com,api.example.com" --browser-session my-task`  |
| `account`                   | Show account info and balance        | `aluvia account`                                                                    |
| `account usage`             | Show bandwidth usage stats           | `aluvia account usage`                                                              |
| `geos`                      | List available geo-targeting regions | `aluvia geos`                                                                       |
