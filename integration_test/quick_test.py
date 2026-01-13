#!/usr/bin/env python3
"""
Quick Integration Test - Run a fast subset of tests for smoke testing.

This runs the most critical tests to quickly verify everything works.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient, AluviaApi

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


async def quick_api_test():
    """Quick API smoke test."""
    print("🔍 Quick API Test...", end=" ", flush=True)
    try:
        async with AluviaApi(api_key=API_KEY) as api:
            account = await api.account.get()
            connections = await api.account.connections.list()
            geos = await api.geos.list()
            assert account is not None
            assert isinstance(connections, list)
            assert isinstance(geos, list)
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({e})")
        return False


async def quick_sdk_test():
    """Quick SDK smoke test."""
    print("🔍 Quick SDK Test...", end=" ", flush=True)
    try:
        client = AluviaClient(
            api_key=API_KEY, connection_id=CONNECTION_ID, local_proxy=True, log_level="silent"
        )
        connection = await client.start()

        # Test basic operations
        await client.update_session_id("quicktest")
        await client.update_rules(["*.example.com"])

        await connection.close()
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({e})")
        return False


async def main():
    """Run quick smoke tests."""
    print("\n⚡ Quick Integration Test (Smoke Test)")
    print("=" * 50)

    results = []
    results.append(await quick_api_test())
    results.append(await quick_sdk_test())

    print("=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All quick tests passed ({passed}/{total})")
        return True
    else:
        print(f"❌ Some tests failed ({passed}/{total})")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Interrupted")
        sys.exit(130)
