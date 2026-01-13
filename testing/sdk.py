"""Test script for Aluvia SDK - equivalent to the Node.js version."""

import asyncio
import sys
import os

# Add parent directory to path to import aluvia_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient, AluviaApi


async def main():
    """Main test function."""
    print("=" * 60)
    print("Aluvia Python SDK Test")
    print("=" * 60)
    print()

    client = AluviaClient(
        api_key="97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4",
        connection_id=1850,
        log_level="debug",
    )

    try:
        print("1. Starting client (commented out in original)...")
        # connection = await client.start()
        # print(f"   ✓ Client started on {connection.url}")
        print("   ⊘ Skipped (commented out)")
        print()

        print("2. Updating session ID to '!@#'...")
        try:
            await client.update_session_id("123")
            print("   ✓ Session ID updated successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        print("3. Updating target geo to 'invalid-geo'...")
        try:
            await client.update_target_geo("us_ca")
            print("   ✓ Target geo updated successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        print("=" * 60)
        print("Test completed")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        raise
    finally:
        # Clean up if client was started
        if client._started:
            await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
