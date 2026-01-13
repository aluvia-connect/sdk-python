"""Example using the AluviaApi directly."""

import asyncio

from aluvia_sdk import AluviaApi


async def main() -> None:
    """Main example using AluviaApi."""
    # Create API wrapper
    api = AluviaApi(api_key="your-api-key-here")

    try:
        # Get account information
        account = await api.account.get()
        print(f"Account balance: {account.get('balance_gb', 0)} GB")

        # List available geos
        geos = await api.geos.list()
        print(f"Available geos: {[g.get('code') for g in geos]}")

        # List connections
        connections = await api.account.connections.list()
        print(f"Active connections: {len(connections)}")

        # Create a new connection
        new_conn = await api.account.connections.create(
            description="api-example",
            rules=["example.com"],
            target_geo="us_ca",
        )
        print(f"Created connection: {new_conn.get('connection_id')}")

        # Update the connection
        updated = await api.account.connections.patch(
            connection_id=new_conn["connection_id"],
            rules=["example.com", "google.com"],
        )
        print(f"Updated rules: {updated.get('rules')}")

        # Delete the connection
        result = await api.account.connections.delete(new_conn["connection_id"])
        print(f"Deleted: {result.get('deleted')}")

    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
