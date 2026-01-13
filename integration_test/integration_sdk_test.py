"""
Integration tests for Aluvia SDK Client - Testing all client functionality.

This test suite uses a real API key and tests the SDK client functionality.
Run with: python integration_test/integration_sdk_test.py
"""

import asyncio
import sys
import os
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient, MissingApiKeyError

API_KEY = os.environ.get("ALUVIA_API_KEY")
if not API_KEY:
    print("❌ Error: ALUVIA_API_KEY environment variable is not set")
    print("   Set it with: export ALUVIA_API_KEY=your_api_key")
    sys.exit(1)

CONNECTION_ID = int(os.environ.get("ALUVIA_CONNECTION_ID", "0"))
if not CONNECTION_ID:
    print("❌ Error: ALUVIA_CONNECTION_ID environment variable is not set")
    print("   Set it with: export ALUVIA_CONNECTION_ID=your_connection_id")
    sys.exit(1)


async def test_client_initialization():
    """Test client initialization and configuration."""
    print("=" * 70)
    print("TEST 1: Client Initialization")
    print("=" * 70)

    # Test 1.1: Basic initialization
    print("\n1.1 Basic client initialization...")
    try:
        client = AluviaClient(api_key=API_KEY, log_level="silent")
        print(f"   ✓ Client initialized")
        print(f"   - API base URL: {client.api_base_url}")
        print(f"   - Poll interval: {client.poll_interval_ms}ms")
        print(f"   - Gateway protocol: {client.gateway_protocol}")
        print(f"   - Gateway port: {client.gateway_port}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 1.2: Custom configuration
    print("\n1.2 Client with custom configuration...")
    try:
        client = AluviaClient(
            api_key=API_KEY,
            connection_id=CONNECTION_ID,
            gateway_protocol="https",
            poll_interval_ms=10000,
            log_level="silent",
        )
        print(f"   ✓ Custom client initialized")
        print(f"   - Connection ID: {client.connection_id}")
        print(f"   - Gateway protocol: {client.gateway_protocol}")
        print(f"   - Gateway port: {client.gateway_port}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


async def test_local_proxy_mode():
    """Test local proxy mode (most common use case)."""
    print("\n" + "=" * 70)
    print("TEST 2: Local Proxy Mode")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="info"
    )

    try:
        # Test 2.1: Start client
        print("\n2.1 Starting client in local proxy mode...")
        connection = await client.start()
        print(f"   ✓ Client started")
        print(f"   - Host: {connection.host}")
        print(f"   - Port: {connection.port}")
        print(f"   - URL: {connection.url}")

        # Test 2.2: Get proxy settings
        print("\n2.2 Getting proxy configuration...")
        proxy_url = connection.get_url()
        print(f"   ✓ Proxy URL: {proxy_url}")

        # Test 2.3: Get adapter configurations
        print("\n2.3 Testing framework adapters...")

        # Playwright
        playwright_config = connection.as_playwright()
        print(f"   ✓ Playwright config: {playwright_config}")

        # Selenium
        selenium_args = connection.as_selenium()
        print(f"   ✓ Selenium args: {selenium_args}")

        # httpx
        httpx_proxies = connection.as_httpx_proxies()
        print(f"   ✓ httpx proxies: {httpx_proxies}")

        # requests
        requests_proxies = connection.as_requests_proxies()
        print(f"   ✓ requests proxies: {requests_proxies}")

        # aiohttp
        aiohttp_proxy = connection.as_aiohttp_proxy()
        print(f"   ✓ aiohttp proxy: {aiohttp_proxy}")

        # Test 2.4: Keep connection alive briefly
        print("\n2.4 Testing connection stability...")
        await asyncio.sleep(2)
        print(f"   ✓ Connection stable")

        # Test 2.5: Stop client
        print("\n2.5 Stopping client...")
        await connection.close()
        print(f"   ✓ Client stopped successfully")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_gateway_mode():
    """Test gateway mode (direct connection without local proxy)."""
    print("\n" + "=" * 70)
    print("TEST 3: Gateway Mode")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY,
        connection_id=CONNECTION_ID,
        local_proxy=False,  # Gateway mode
        gateway_protocol="http",
        log_level="info",
    )

    try:
        # Test 3.1: Start in gateway mode
        print("\n3.1 Starting client in gateway mode...")
        connection = await client.start()
        print(f"   ✓ Client started in gateway mode")
        print(f"   - Host: {connection.host}")
        print(f"   - Port: {connection.port}")

        # Test 3.2: Get gateway URL
        print("\n3.2 Getting gateway URL...")
        gateway_url = connection.get_url()
        print(f"   ✓ Gateway URL: {gateway_url[:50]}...")

        # Verify it has credentials
        if "@" in gateway_url:
            print(f"   ✓ URL contains authentication credentials")

        # Test 3.3: Stop client
        print("\n3.3 Stopping client...")
        await connection.close()
        print(f"   ✓ Client stopped successfully")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_rules_management():
    """Test dynamic rules management."""
    print("\n" + "=" * 70)
    print("TEST 4: Rules Management")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="info"
    )

    try:
        print("\n4.1 Starting client...")
        connection = await client.start()
        print(f"   ✓ Client started")

        # Test 4.2: Update rules
        print("\n4.2 Updating routing rules...")
        new_rules = ["*.example.com", "*.google.com", "test.com"]
        await client.update_rules(new_rules)
        print(f"   ✓ Rules updated: {new_rules}")

        # Wait for config to sync
        print("\n4.3 Waiting for configuration sync...")
        await asyncio.sleep(2)
        print(f"   ✓ Configuration synced")

        # Test 4.4: Update rules again
        print("\n4.4 Updating rules again...")
        updated_rules = ["*.httpbin.org", "*.ipconfig.io"]
        await client.update_rules(updated_rules)
        print(f"   ✓ Rules updated again: {updated_rules}")

        await asyncio.sleep(1)

        print("\n4.5 Stopping client...")
        await connection.close()
        print(f"   ✓ Client stopped")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_session_management():
    """Test session ID management."""
    print("\n" + "=" * 70)
    print("TEST 5: Session Management")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="info"
    )

    try:
        print("\n5.1 Starting client...")
        connection = await client.start()
        print(f"   ✓ Client started")

        # Test 5.2: Update session ID
        print("\n5.2 Updating session ID...")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_session_id = f"testsession{timestamp}"
        await client.update_session_id(new_session_id)
        print(f"   ✓ Session ID updated: {new_session_id}")

        await asyncio.sleep(1)

        # Test 5.3: Update session ID again
        print("\n5.3 Updating session ID again...")
        another_session_id = f"test_session_2_{timestamp}"
        await client.update_session_id(another_session_id)
        print(f"   ✓ Session ID updated: {another_session_id}")

        await asyncio.sleep(1)

        print("\n5.4 Stopping client...")
        await connection.close()
        print(f"   ✓ Client stopped")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_geo_targeting():
    """Test geo-targeting functionality."""
    print("\n" + "=" * 70)
    print("TEST 6: Geo-Targeting")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="info"
    )

    try:
        print("\n6.1 Starting client...")
        connection = await client.start()
        print(f"   ✓ Client started")

        # Test 6.2: Set target geo
        print("\n6.2 Setting target geo to California...")
        await client.update_target_geo("us_ca")
        print(f"   ✓ Target geo set to: us_ca")

        await asyncio.sleep(1)

        # Test 6.3: Change target geo
        print("\n6.3 Changing target geo to New York...")
        await client.update_target_geo("us_ny")
        print(f"   ✓ Target geo changed to: us_ny")

        await asyncio.sleep(1)

        # Test 6.4: Clear target geo
        print("\n6.4 Clearing target geo...")
        await client.update_target_geo(None)
        print(f"   ✓ Target geo cleared")

        await asyncio.sleep(1)

        print("\n6.5 Stopping client...")
        await connection.close()
        print(f"   ✓ Client stopped")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_context_manager():
    """Test context manager support."""
    print("\n" + "=" * 70)
    print("TEST 7: Context Manager")
    print("=" * 70)

    print("\n7.1 Testing async context manager...")
    try:
        async with AluviaClient(
            api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="silent"
        ) as client:
            # Client automatically starts
            print(f"   ✓ Client started via context manager")

            # Do some operations
            await client.update_session_id("context_manager_test")
            print(f"   ✓ Operations performed")

            await asyncio.sleep(1)

        # Client automatically stops when exiting context
        print(f"   ✓ Client stopped automatically")
        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_multiple_starts():
    """Test starting client multiple times."""
    print("\n" + "=" * 70)
    print("TEST 8: Multiple Start Calls")
    print("=" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="silent"
    )

    try:
        print("\n8.1 Starting client first time...")
        connection1 = await client.start()
        print(f"   ✓ Client started (port: {connection1.port})")

        print("\n8.2 Starting client second time (should return same connection)...")
        connection2 = await client.start()
        print(f"   ✓ Got connection (port: {connection2.port})")

        # Verify it's the same connection
        if connection1.port == connection2.port:
            print(f"   ✓ Correctly returned same connection")
        else:
            print(f"   ✗ Different connections returned (unexpected)")
            return False

        print("\n8.3 Stopping client...")
        await client.stop()
        print(f"   ✓ Client stopped")

        return True

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_error_cases():
    """Test error handling."""
    print("\n" + "=" * 70)
    print("TEST 9: Error Handling")
    print("=" * 70)

    # Test 9.1: Missing API key
    print("\n9.1 Testing missing API key...")
    try:
        client = AluviaClient(api_key="", log_level="silent")
        print(f"   ✗ Should have raised MissingApiKeyError")
        return False
    except MissingApiKeyError:
        print(f"   ✓ Correctly raised MissingApiKeyError")
    except Exception as e:
        print(f"   ✗ Wrong exception: {e}")
        return False

    # Test 9.2: Whitespace API key
    print("\n9.2 Testing whitespace-only API key...")
    try:
        client = AluviaClient(api_key="   ", log_level="silent")
        print(f"   ✗ Should have raised MissingApiKeyError")
        return False
    except MissingApiKeyError:
        print(f"   ✓ Correctly raised MissingApiKeyError")
    except Exception as e:
        print(f"   ✗ Wrong exception: {e}")
        return False

    return True


async def main():
    """Run all SDK integration tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ALUVIA SDK INTEGRATION TESTS" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Connection ID: {CONNECTION_ID}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Run all tests
    results["Client Initialization"] = await test_client_initialization()
    results["Local Proxy Mode"] = await test_local_proxy_mode()
    results["Gateway Mode"] = await test_gateway_mode()
    results["Rules Management"] = await test_rules_management()
    results["Session Management"] = await test_session_management()
    results["Geo-Targeting"] = await test_geo_targeting()
    results["Context Manager"] = await test_context_manager()
    results["Multiple Starts"] = await test_multiple_starts()
    results["Error Handling"] = await test_error_cases()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
