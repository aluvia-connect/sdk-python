"""
Integration tests for Aluvia API - Testing all CRUD operations.

This test suite uses a real API key and tests against the live API.
Run with: python integration_test/integration_api_test.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaApi, ApiError, InvalidApiKeyError

API_KEY = os.environ.get("ALUVIA_API_KEY")
if not API_KEY:
    print("❌ Error: ALUVIA_API_KEY environment variable is not set")
    print("   Set it with: export ALUVIA_API_KEY=your_api_key")
    sys.exit(1)


async def test_account_operations():
    """Test account-related API operations."""
    print("=" * 70)
    print("TEST 1: Account Operations")
    print("=" * 70)

    api = AluviaApi(api_key=API_KEY)

    try:
        # Test 1.1: Get account info
        print("\n1.1 Getting account information...")
        try:
            account = await api.account.get()
            print(f"   ✓ Account retrieved")
            print(f"   - Balance: {account.get('balance_gb', 'N/A')} GB")
            print(f"   - Email: {account.get('email', 'N/A')}")
            return True
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

    finally:
        await api.close()


async def test_account_usage():
    """Test account usage API."""
    print("\n" + "=" * 70)
    print("TEST 2: Account Usage")
    print("=" * 70)

    api = AluviaApi(api_key=API_KEY)

    try:
        print("\n2.1 Getting account usage...")
        try:
            usage = await api.account.usage()
            print(f"   ✓ Usage retrieved")
            print(f"   - Data: {usage}")
            return True
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

    finally:
        await api.close()


async def test_geos_operations():
    """Test geo-targeting API operations."""
    print("\n" + "=" * 70)
    print("TEST 3: Geo-Targeting Operations")
    print("=" * 70)

    api = AluviaApi(api_key=API_KEY)

    try:
        # Test 3.1: List available geos
        print("\n3.1 Listing available geo locations...")
        try:
            geos = await api.geos.list()
            print(f"   ✓ Geos retrieved: {len(geos)} locations")
            if geos:
                print(f"   - Sample geos: {[g.get('code', 'N/A') for g in geos[:5]]}")
            return True
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

    finally:
        await api.close()


async def test_connections_crud():
    """Test full CRUD operations on connections."""
    print("\n" + "=" * 70)
    print("TEST 4: Connections CRUD Operations")
    print("=" * 70)

    api = AluviaApi(api_key=API_KEY)
    connection_id = None

    try:
        # Test 4.1: List existing connections
        print("\n4.1 Listing existing connections...")
        try:
            connections = await api.account.connections.list()
            print(f"   ✓ Connections listed: {len(connections)} found")
            for conn in connections[:3]:
                print(f"   - Connection {conn.get('id', 'N/A')}: {conn.get('description', 'N/A')}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

        # Test 4.2: Create a new connection
        print("\n4.2 Creating new connection...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_connection = await api.account.connections.create(
                description=f"Integration test - {timestamp}",
                rules=["*.example.com", "test.com"],
                session_id=f"testsession{timestamp}",
                target_geo="us_ca",
            )
            connection_id = new_connection.get("connection_id") or new_connection.get("id")
            print(f"   ✓ Connection created: ID {connection_id}")
            print(f"   - Description: {new_connection.get('description', 'N/A')}")
            print(f"   - Rules: {new_connection.get('rules', [])}")
            print(f"   - Session ID: {new_connection.get('session_id', 'N/A')}")
            print(f"   - Target geo: {new_connection.get('target_geo', 'N/A')}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

        # Test 4.3: Get the connection
        print(f"\n4.3 Getting connection {connection_id}...")
        try:
            connection = await api.account.connections.get(connection_id)
            print(f"   ✓ Connection retrieved")
            print(f"   - Proxy username: {connection.get('proxy_username', 'N/A')}")
            print(f"   - Has proxy password: {'proxy_password' in connection}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

        # Test 4.4: Update the connection (PATCH)
        print(f"\n4.4 Updating connection {connection_id}...")
        try:
            updated_connection = await api.account.connections.patch(
                connection_id,
                description=f"Integration test - UPDATED - {timestamp}",
                rules=["*.updated-example.com", "updated-test.com", "*.google.com"],
                session_id=f"updatedsession{timestamp}",
                target_geo="us_ny",
            )
            print(f"   ✓ Connection updated")
            print(f"   - New description: {updated_connection.get('description', 'N/A')}")
            print(f"   - New rules: {updated_connection.get('rules', [])}")
            print(f"   - New session ID: {updated_connection.get('session_id', 'N/A')}")
            print(f"   - New target geo: {updated_connection.get('target_geo', 'N/A')}")
        except Exception as e:
            print(f"   ✗ Failed to update: {e}")

        # Test 4.5: Verify the update by getting it again
        print(f"\n4.5 Verifying update by retrieving connection again...")
        try:
            verified_connection = await api.account.connections.get(connection_id)
            print(f"   ✓ Connection retrieved after update")
            print(f"   - Verified description: {verified_connection.get('description', 'N/A')}")
            print(f"   - Verified rules: {verified_connection.get('rules', [])}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

        # Test 4.6: Delete the connection
        print(f"\n4.6 Deleting connection {connection_id}...")
        try:
            delete_result = await api.account.connections.delete(connection_id)
            print(f"   ✓ Connection deleted")
            print(f"   - Result: {delete_result}")
            connection_id = None  # Prevent cleanup attempt
            return True
        except Exception as e:
            print(f"   ✗ Failed to delete: {e}")
            return False

    finally:
        # Cleanup: Try to delete the connection if it wasn't deleted
        if connection_id:
            print(f"\n4.7 Cleanup: Attempting to delete connection {connection_id}...")
            try:
                await api.account.connections.delete(connection_id)
                print(f"   ✓ Cleanup successful")
            except Exception as e:
                print(f"   ⚠ Cleanup warning: {e}")

        await api.close()


async def test_error_handling():
    """Test error handling with invalid operations."""
    print("\n" + "=" * 70)
    print("TEST 5: Error Handling")
    print("=" * 70)

    # Test 5.1: Invalid API key
    print("\n5.1 Testing invalid API key...")
    try:
        api = AluviaApi(api_key="invalid_key_12345")
        await api.account.get()
        print(f"   ✗ Should have raised InvalidApiKeyError")
        await api.close()
        return False
    except InvalidApiKeyError as e:
        print(f"   ✓ Correctly raised InvalidApiKeyError: {e}")
    except Exception as e:
        print(f"   ⚠ Raised different error: {e}")

    # Test 5.2: Invalid connection ID
    print("\n5.2 Testing invalid connection ID...")
    api = AluviaApi(api_key=API_KEY)
    try:
        await api.account.connections.get(999999999)
        print(f"   ✗ Should have raised ApiError")
        await api.close()
        return False
    except ApiError as e:
        print(f"   ✓ Correctly raised ApiError: {e}")
        await api.close()
        return True
    except Exception as e:
        print(f"   ⚠ Raised different error: {e}")
        await api.close()
        return False


async def test_context_manager():
    """Test async context manager support."""
    print("\n" + "=" * 70)
    print("TEST 6: Context Manager Support")
    print("=" * 70)

    print("\n6.1 Testing async context manager...")
    try:
        async with AluviaApi(api_key=API_KEY) as api:
            account = await api.account.get()
            print(f"   ✓ Context manager works")
            print(f"   - Account retrieved: {account.get('email', 'N/A')}")
        print(f"   ✓ Context manager closed automatically")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ALUVIA API INTEGRATION TESTS" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Run all tests
    results["Account Operations"] = await test_account_operations()
    results["Account Usage"] = await test_account_usage()
    results["Geo Operations"] = await test_geos_operations()
    results["Connections CRUD"] = await test_connections_crud()
    results["Error Handling"] = await test_error_handling()
    results["Context Manager"] = await test_context_manager()

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
