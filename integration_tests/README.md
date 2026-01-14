# Integration Tests

Comprehensive real-world integration tests for the Aluvia Python SDK.

## Setup

1. **Set environment variables:**

   ```bash
   export ALUVIA_API_KEY="your_api_key_here"
   export ALUVIA_CONNECTION_ID="your_connection_id"  # Optional for some tests
   ```

   Or create a `.env` file (copy from `.env.example`):

   ```bash
   cp integration_tests/.env.example integration_tests/.env
   # Edit .env with your credentials
   source integration_tests/.env
   ```

## Quick Start

```bash
# Run all integration tests
./integration_tests/run_integration_tests.sh

# Or run individual tests
python integration_tests/integration_api_test.py      # API tests
python integration_tests/integration_sdk_test.py      # SDK tests
python integration_tests/integration_full_workflow.py # Complete workflow
python integration_tests/quick_test.py                # Quick smoke test
```

## What's Included

- **integration_api_test.py** - Tests all API CRUD operations (11 KB)
- **integration_sdk_test.py** - Tests all SDK client functionality (15 KB)
- **integration_full_workflow.py** - Complete end-to-end workflow (8.4 KB)
- **quick_test.py** - Fast smoke test (2.4 KB)
- **run_integration_tests.sh** - Run all tests with summary (1.9 KB)

## Documentation

See [INTEGRATION_TESTS_README.md](./INTEGRATION_TESTS_README.md) for complete documentation.

## Requirements

- Python 3.9+
- Valid Aluvia API key
- httpx (for workflow test): `pip install httpx`
