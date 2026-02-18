# CLI Technical Guide (Python)

A comprehensive reference for the Aluvia Python CLI — a JSON-output command-line interface for managing browser sessions, account info, and proxy connections. Designed for AI agent frameworks and automation pipelines.

## Table of Contents

- [Overview](#overview)
- [Installation and setup](#installation-and-setup)
- [Output format](#output-format)
- [Command reference](#command-reference)
  - [session start](#session-start)
  - [session close](#session-close)
  - [session list](#session-list)
  - [session get](#session-get)
  - [session rotate-ip](#session-rotate-ip)
  - [session set-geo](#session-set-geo)
  - [session set-rules](#session-set-rules)
  - [account](#account)
  - [account usage](#account-usage)
  - [geos](#geos)
  - [help](#help)
- [Connecting to a running browser](#connecting-to-a-running-browser)
  - [Using --run](#using---run)
  - [Using connect()](#using-connect)
- [Session management internals](#session-management-internals)
  - [Daemon architecture](#daemon-architecture)
  - [Lock files](#lock-files)
  - [Session naming](#session-naming)
  - [Process lifecycle](#process-lifecycle)
- [Block detection in sessions](#block-detection-in-sessions)
- [Error handling](#error-handling)
- [Validation rules](#validation-rules)

---

## Overview

The CLI is available via two equivalent binary names:

```bash
aluvia <command>
aluvia-sdk <command>
```

Both point to the same entry point. All commands output JSON to stdout and use exit code `0` for success, `1` for errors. This makes the CLI easy to integrate with AI agent frameworks that parse JSON output.

**Environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| ALUVIA_API_KEY | Yes | Your Aluvia API key |
