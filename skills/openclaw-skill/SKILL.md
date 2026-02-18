---
name: aluvia

description: "Stop your AI agent from getting blocked. Aluvia routes traffic through real US mobile carrier IPs (AT&T, T-Mobile, Verizon) so websites treat your agent like a human. Bypasses Cloudflare, DataDome, PerimeterX, Akamai Bot Manager, and other anti-bot systems automatically. Use when your agent hits 403 Forbidden, Cloudflare challenges, CAPTCHAs, rate limits (429), IP bans, empty responses, or WAF blocks. Features auto block detection and bypass, one-command IP rotation, US geo-targeting, dynamic proxy routing rules, and managed headless Chromium via Playwright — all through a JSON-first CLI built for AI agents."
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["aluvia"], "env": ["ALUVIA_API_KEY"] },
        "primaryEnv": "ALUVIA_API_KEY",
        "emoji": "🌐",
      },
  }
---

# Aluvia Proxy: Unblock agent browser with proxies + playwright

## The Problem

Your OpenClaw agent gets blocked because anti-bot systems are built to stop cloud-based agent/bot traffic with datacenter IP addresses. You get 403 Forbidden, CAPTCHAs, 429 rate limits, IP bans, empty responses.

## The Solution

Aluvia routes your agent's traffic through **real US mobile carrier IPs** — the same IPs used by millions of real people on their phones. Websites cannot distinguish your agent from a legitimate user browsing on a mobile device.

Aluvia's proxies + Playwright + Chrome stack: detects website blocks and routes your agent's traffic through a clean mobile IP when necessary. All automatically. All without proxy configs. All without building custom routing rules.

## Features

- **Mobile carrier residential proxies** — Not datacenter or shared residential IPs. Real mobile carrier IPs that websites inherently trust. Highest-quality proxy tier available.
- **Automatic block detection and bypass** — Every page load is scored 0.0–1.0. Detects Cloudflare challenges, CAPTCHAs, 403/429 responses, soft blocks, and empty pages. With `--auto-unblock`, blocks are remediated automatically by rerouting through proxy and reloading.
- **One-command IP rotation** — Rotate to a fresh mobile IP mid-session without restarting the browser. Break through persistent blocks and rate limits instantly.
- **US geo-targeting** — Pin your exit IP to a specific US state (California, New York, Texas, etc.) for location-sensitive scraping and content access.
- **Dynamic proxy routing rules** — Proxy only the domains that need it. Add or remove hostnames on the fly as your agent navigates across sites and discovers new endpoints.
- **Managed headless Chromium with Playwright** — Full browser sessions with Chrome DevTools Protocol (CDP) access. No browser setup, no stealth plugins, no fingerprint patching required.
- **JSON-first CLI built for agents** — Every command returns structured JSON to stdout. Designed for programmatic use by AI agents, not for humans typing in a terminal.

## Installation

```bash
pip install aluvia-sdk
```

## CLI Interface
