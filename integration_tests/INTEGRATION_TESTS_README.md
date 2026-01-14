# Integration Tests

This folder contains comprehensive real-world integration tests for the Aluvia SDK using an actual API key and making real API calls.

## Test Files

### 1. `integration_api_test.py` - API Integration Tests

Tests all API CRUD operations:

- ✅ Account operations (get account info, usage, payments)
- ✅ Geo-targeting operations (list available geos)
- ✅ Full CRUD on connections (Create, Read, Update, Delete)
- ✅ Error handling (invalid API keys, invalid connection IDs)
- ✅ Context manager support

**Run with:**

```bash
python integration_tests/integration_api_test.py
# or
.venv/bin/python integration_tests/integration_api_test.py
```

### 2. `integration_sdk_test.py` - SDK Client Integration Tests

Tests all SDK client functionality:

- ✅ Client initialization and configuration
- ✅ Local proxy mode (starting/stopping)
- ✅ Gateway mode (direct connection)
- ✅ Rules management (dynamic updates)
- ✅ Session ID management
- ✅ Geo-targeting configuration
- ✅ Framework adapters (Playwright, Selenium, httpx, requests, aiohttp)
- ✅ Context manager support
- ✅ Multiple start calls handling
- ✅ Error handling

**Run with:**

```bash
python integration_tests/integration_sdk_test.py
# or
.venv/bin/python integration_tests/integration_sdk_test.py
```

### 3. `integration_full_workflow.py` - Complete Workflow Test

Tests a complete real-world scenario:

- 📋 Phase 1: Create connection via API
- 🚀 Phase 2: Start SDK client with local proxy
- 🌐 Phase 3: Make HTTP requests through proxy (httpbin.org, example.com)
- ⚙️ Phase 4: Update configuration dynamically (rules, session, geo)
- ✅ Phase 5: Verify updated configuration via API
- 🔄 Phase 6: Make requests with updated config
- 🛑 Phase 7: Stop client
- 🧹 Phase 8: Cleanup - delete connection

**Run with:**

```bash
python integration_tests/integration_full_workflow.py
# or
.venv/bin/python integration_tests/integration_full_workflow.py
```

### 4. `run_integration_tests.sh` - Run All Tests

Bash script that runs all three test suites in sequence and provides a summary.

**Run with:**

```bash
./integration_tests/run_integration_tests.sh
# or
bash integration_tests/run_integration_tests.sh
```

## Configuration

The integration tests use environment variables for credentials:

- **ALUVIA_API_KEY**: Your Aluvia API key (required)
- **ALUVIA_CONNECTION_ID**: Connection ID for SDK tests (required for `integration_sdk_test.py`)

### Setup Environment Variables

**Option 1: Export directly**

```bash
export ALUVIA_API_KEY="your_api_key_here"
export ALUVIA_CONNECTION_ID="your_connection_id"
```

**Option 2: Use .env file**

```bash
# Copy the example file
cp integration_tests/.env.example integration_tests/.env

# Edit with your credentials
nano integration_tests/.env

# Source it
source integration_tests/.env
```

## Prerequisites

1. **Install the SDK** (editable mode):

   ```bash
   pip install -e .
   ```

2. **Install httpx** (for workflow test):

   ```bash
   pip install httpx
   ```

3. **Valid API key** with sufficient balance

## Test Coverage

### API Tests (`integration_api_test.py`)

- ✅ Account.get() - Get account information
- ✅ Account.usage() - Get usage statistics
- ✅ Account.payments() - Get payment history
- ✅ Geos.list() - List available geo locations
- ✅ Connections.list() - List all connections
- ✅ Connections.create() - Create new connection
- ✅ Connections.get(id) - Get specific connection
- ✅ Connections.patch(id) - Update connection
- ✅ Connections.delete(id) - Delete connection
- ✅ Error handling for invalid inputs
- ✅ Async context manager support

### SDK Tests (`integration_sdk_test.py`)

- ✅ Client initialization with various configs
- ✅ Local proxy mode start/stop
- ✅ Gateway mode start/stop
- ✅ Connection object methods (get_url, as_playwright, etc.)
- ✅ Framework adapters (all 5 adapters)
- ✅ update_rules() - Dynamic rule updates
- ✅ update_session_id() - Session management
- ✅ update_target_geo() - Geo-targeting
- ✅ Context manager support
- ✅ Multiple start() calls handling
- ✅ Error handling for missing/invalid API keys

### Workflow Test (`integration_full_workflow.py`)

- ✅ End-to-end workflow: Create → Use → Update → Cleanup
- ✅ Real HTTP requests through proxy
- ✅ Dynamic configuration updates
- ✅ Configuration verification
- ✅ httpx integration

## Expected Results

All tests should pass with output like:

```
╔══════════════════════════════════════════════════════════════════╗
║               ALUVIA API INTEGRATION TESTS                       ║
╚══════════════════════════════════════════════════════════════════╝

...

TEST SUMMARY
======================================================================
✓ PASSED: Account Operations
✓ PASSED: Account Usage
✓ PASSED: Geo Operations
✓ PASSED: Connections CRUD
✓ PASSED: Error Handling
✓ PASSED: Context Manager

Results: 6/6 tests passed
```

## Notes

- Tests create temporary connections and clean them up automatically
- Tests use real API calls and consume minimal bandwidth
- Each test is isolated and can be run independently
- Failed tests will show detailed error messages
- All tests support Ctrl+C for graceful interruption

## Troubleshooting

### "API key is invalid"

- Verify the API key is correct
- Check if the API key has sufficient permissions

### "Connection timeout"

- Check your internet connection
- Verify the API endpoint is accessible

### "Balance insufficient"

- Check account balance with `api.account.get()`
- Add credits to your account

### "Port already in use" (local proxy tests)

- Another proxy is already running
- Stop other instances or let the SDK auto-assign a port

## Manual Tests (Legacy)

The folder also contains legacy manual test scripts:

- `api_test.py` - Original API test script
- `browser.py` - Playwright browser automation test
- `sdk.py` - Basic SDK test
- `curl_test.py` - cURL-based test
- And others...

These are kept for backward compatibility but the integration tests above are more comprehensive.
