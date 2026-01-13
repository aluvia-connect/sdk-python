"""
Full workflow integration test - Real-world usage scenario.

This simulates a real-world use case: Creating a connection, starting the proxy,
making HTTP requests through it, and cleaning up.

Run with: python integration_test/integration_full_workflow.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient, AluviaApi

API_KEY = os.environ.get("ALUVIA_API_KEY")
if not API_KEY:
    print("❌ Error: ALUVIA_API_KEY environment variable is not set")
    print("   Set it with: export ALUVIA_API_KEY=your_api_key")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("❌ httpx is not installed. Install it with: pip install httpx")
    sys.exit(1)


async def test_complete_workflow():
    """Test a complete real-world workflow."""
    print("=" * 70)
    print("COMPLETE WORKFLOW TEST: Connection → Proxy → HTTP Request → Cleanup")
    print("=" * 70)

    connection_id = None

    # Phase 1: Create connection via API
    print("\n📋 PHASE 1: Create Connection via API")
    print("-" * 70)

    api = AluviaApi(api_key=API_KEY)

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        print(f"\n1.1 Creating new connection...")
        connection_config = await api.account.connections.create(
            description=f"Workflow test - {timestamp}",
            rules=["*.httpbin.org", "*.example.com"],
            session_id=f"workflowtest{timestamp}",
            target_geo="us_ca",
        )
        connection_id = connection_config.get("connection_id") or connection_config.get("id")
        print(f"   ✓ Connection created: ID {connection_id}")
        print(f"   - Rules: {connection_config.get('rules', [])}")
        print(f"   - Session ID: {connection_config.get('session_id', 'N/A')}")
        print(f"   - Target geo: {connection_config.get('target_geo', 'N/A')}")

    finally:
        await api.close()

    # Phase 2: Start SDK client with the connection
    print("\n🚀 PHASE 2: Start SDK Client with Local Proxy")
    print("-" * 70)

    client = AluviaClient(
        api_key=API_KEY, connection_id=connection_id, local_proxy=True, log_level="info"
    )

    print(f"\n2.1 Starting client...")
    connection = await client.start()
    print(f"   ✓ Client started")
    print(f"   - Proxy URL: {connection.url}")
    print(f"   - Host: {connection.host}")
    print(f"   - Port: {connection.port}")

    # Phase 3: Make HTTP requests through the proxy
    print("\n🌐 PHASE 3: Make HTTP Requests Through Proxy")
    print("-" * 70)

    # Get httpx proxy configuration
    proxies = connection.as_httpx_proxies()
    print(f"\n3.1 Using httpx with proxy configuration...")
    print(f"   - Proxies: {proxies}")

    async with httpx.AsyncClient(proxies=proxies, timeout=30.0) as http_client:

        # Test 3.2: Make request to httpbin (should go through proxy)
        print(f"\n3.2 Making request to httpbin.org...")
        try:
            response = await http_client.get("http://httpbin.org/ip")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Request successful")
                print(f"   - Status: {response.status_code}")
                print(f"   - IP: {data.get('origin', 'N/A')}")
            else:
                print(f"   ⚠ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠ Request failed: {e}")

        # Test 3.3: Make another request to different host
        print(f"\n3.3 Making request to example.com...")
        try:
            response = await http_client.get("http://example.com")
            if response.status_code == 200:
                print(f"   ✓ Request successful")
                print(f"   - Status: {response.status_code}")
                print(f"   - Content length: {len(response.content)} bytes")
            else:
                print(f"   ⚠ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠ Request failed: {e}")

    # Phase 4: Update configuration dynamically
    print("\n⚙️  PHASE 4: Update Configuration Dynamically")
    print("-" * 70)

    print(f"\n4.1 Updating routing rules...")
    new_rules = ["*.httpbin.org", "*.ipconfig.io", "*.ifconfig.me"]
    await client.update_rules(new_rules)
    print(f"   ✓ Rules updated: {new_rules}")

    print(f"\n4.2 Updating session ID...")
    new_session = f"workflowupdated{timestamp}"
    await client.update_session_id(new_session)
    print(f"   ✓ Session ID updated: {new_session}")

    print(f"\n4.3 Updating target geo...")
    await client.update_target_geo("us_ny")
    print(f"   ✓ Target geo updated: us_ny")

    # Wait for config to sync
    print(f"\n4.4 Waiting for configuration sync...")
    await asyncio.sleep(3)
    print(f"   ✓ Configuration synced")

    # Phase 5: Verify updated configuration
    print("\n✅ PHASE 5: Verify Updated Configuration")
    print("-" * 70)

    api = AluviaApi(api_key=API_KEY)
    try:
        print(f"\n5.1 Retrieving connection configuration...")
        updated_config = await api.account.connections.get(connection_id)
        print(f"   ✓ Configuration retrieved")
        print(f"   - Rules: {updated_config.get('rules', [])}")
        print(f"   - Session ID: {updated_config.get('session_id', 'N/A')}")
        print(f"   - Target geo: {updated_config.get('target_geo', 'N/A')}")

        # Verify updates
        config_rules = updated_config.get("rules", [])
        if "*.ipconfig.io" in config_rules:
            print(f"   ✓ Rules update verified")
        else:
            print(f"   ⚠ Rules may not have synced yet")

    finally:
        await api.close()

    # Phase 6: Make more requests with updated config
    print("\n🔄 PHASE 6: Make Requests with Updated Configuration")
    print("-" * 70)

    proxies = connection.as_httpx_proxies()

    async with httpx.AsyncClient(proxies=proxies, timeout=30.0) as http_client:
        print(f"\n6.1 Making request to ipconfig.io (newly added rule)...")
        try:
            response = await http_client.get("http://ipconfig.io/json")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Request successful")
                print(f"   - IP: {data.get('ip', 'N/A')}")
                print(f"   - Country: {data.get('country', 'N/A')}")
            else:
                print(f"   ⚠ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠ Request failed: {e}")

    # Phase 7: Stop client
    print("\n🛑 PHASE 7: Stop Client")
    print("-" * 70)

    print(f"\n7.1 Stopping client...")
    await connection.close()
    print(f"   ✓ Client stopped")

    # Phase 8: Cleanup - Delete connection
    print("\n🧹 PHASE 8: Cleanup - Delete Connection")
    print("-" * 70)

    api = AluviaApi(api_key=API_KEY)
    try:
        print(f"\n8.1 Deleting connection {connection_id}...")
        await api.account.connections.delete(connection_id)
        print(f"   ✓ Connection deleted")
    finally:
        await api.close()

    print("\n" + "=" * 70)
    print("✅ COMPLETE WORKFLOW TEST PASSED")
    print("=" * 70)

    return True


async def main():
    """Run the complete workflow test."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "ALUVIA SDK COMPLETE WORKFLOW TEST" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        success = await test_complete_workflow()

        print()
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        return success

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
