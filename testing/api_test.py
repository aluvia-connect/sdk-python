"""API Test script - equivalent to the Node.js API tests."""

import asyncio
import sys
import os

# Add parent directory to path to import aluvia_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient, AluviaApi


async def test_direct_api():
    """Test using AluviaApi directly."""
    print("=" * 60)
    print("Testing AluviaApi (Direct)")
    print("=" * 60)
    print()

    api = AluviaApi(api_key="97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4")

    try:
        # Check account balance
        print("1. Getting account balance...")
        try:
            account = await api.account.get()
            balance = account.get("balance_gb", "N/A")
            print(f"   Balance: {balance} GB")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Create a connection for a new agent
        print("2. Creating a new connection...")
        try:
            connection = await api.account.connections.create(
                description="us-ok - competitor site access",
                rules=["competitor-site.com"],
                target_geo="us_az",  # Use valid geo code
                session_id="competitorsession001",
            )
            connection_id = connection.get("connection_id", "N/A")
            print(f"   Created: {connection_id}")
            created_conn_id = connection_id
        except Exception as e:
            print(f"   ✗ Error: {e}")
            created_conn_id = None
        print()

        # List available geos
        print("3. Listing available geos...")
        try:
            geos = await api.geos.list()
            geo_codes = [g.get("code") for g in geos]
            print(f"   Geos: {geo_codes}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # List connections
        print("4. Listing all connections...")
        try:
            connections = await api.account.connections.list()
            conn_info = [
                {
                    "id": c.get("connection_id"),
                    "desc": c.get("description"),
                    "geo": c.get("target_geo"),
                    "rules": c.get("rules"),
                }
                for c in connections
            ]
            print(f"   Connections: {conn_info[:3]}...")  # Show first 3
            print(f"   Total: {len(connections)} connections")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Get connection by ID
        if created_conn_id:
            print(f"5. Getting connection by ID ({created_conn_id})...")
            try:
                connection_by_id = await api.account.connections.get(created_conn_id)
                print(f"   Connection {created_conn_id}: {connection_by_id}")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            print()

            # Update connection (patch)
            print(f"6. Updating connection {created_conn_id}...")
            try:
                updated_connection = await api.account.connections.patch(
                    created_conn_id,
                    description="Updated description",
                    rules=["updated-site.com"],
                )
                print(f"   Updated Connection {created_conn_id}: {updated_connection}")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            print()

            # Delete connection
            print(f"7. Deleting connection {created_conn_id}...")
            try:
                deleted = await api.account.connections.delete(created_conn_id)
                print(f"   Deleted Connection {created_conn_id}: {deleted}")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            print()
        else:
            print("5-7. Skipping get/patch/delete tests (no connection created)")
            print()

    finally:
        await api.close()


async def test_client_api():
    """Test using AluviaClient's embedded API."""
    print("=" * 60)
    print("Testing AluviaClient.api")
    print("=" * 60)
    print()

    client = AluviaClient(
        api_key="97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4",
        connection_id=1850,
        log_level="info",
    )

    try:
        print("1. Getting account via client.api...")
        try:
            account = await client.api.account.get()
            print(f"   Account: {account}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        print("2. Listing connections via client.api...")
        try:
            connections = await client.api.account.connections.list()
            print(f"   Found {len(connections)} connections")
            if connections:
                print(f"   First connection: {connections[0]}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

    finally:
        # Clean up if client was started
        if client._started:
            await client.stop()


async def main():
    """Main test runner."""
    print("\n" + "=" * 60)
    print("ALUVIA API TEST SUITE")
    print("=" * 60)
    print()

    # Test direct API usage
    await test_direct_api()

    print("\n")

    # Test client.api usage
    await test_client_api()

    print("\n" + "=" * 60)
    print("All tests completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
