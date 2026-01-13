# Testing Scripts

This folder contains test scripts for the Aluvia Python SDK.

## Files

### 1. sdk.py - Connection Update Test
Python equivalent of the Node.js test that validates error handling for connection updates.

**What it tests:**
- `update_session_id()` with invalid session ID (`"!@#"`)
- `update_target_geo()` with invalid geo code (`"invalid-geo"`)

**Expected behavior:** Both operations should fail with HTTP 422 errors (validation errors).

**Run:**
```bash
python sdk.py
# or
./run_test.sh
```

### 2. api_test.py - Comprehensive API Test
Complete test suite covering all API operations.

**What it tests:**
- Get account balance
- Create a new connection
- List available geos
- List all connections
- Get connection by ID
- Update connection (patch)
- Delete connection
- Access API via `AluviaClient.api`

**Run:**
```bash
python api_test.py
# or
./run_api_test.sh
```

### 3. browser.py - Browser Integration Test
Browser automation test using Playwright to validate proxy functionality.

**What it tests:**
- Starting the Aluvia client
- Launching Chromium with proxy configuration
- Navigating to a test page (ipconfig.io/json)
- Verifying proxy is working
- Cleanup and connection closing

**Requirements:**
```bash
pip install playwright
playwright install chromium
playwright install-deps chromium  # System dependencies (requires sudo)
```

**Run:**
```bash
python browser.py
# or
./run_browser_test.sh
```

**Note:** The browser will open in non-headless mode and stay open for 10 seconds. You can modify the `asyncio.sleep(10)` duration in the script.

## Setup

All scripts automatically add the parent directory to the Python path, so they work without installing the package.

## Configuration

All tests use the same API key:
```
97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4
```

- `sdk.py` uses connection_id: 1850
- `api_test.py` creates and deletes its own test connections
- `browser.py` uses connection_id: 1850
