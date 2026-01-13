"""Example using httpx HTTP client."""

import asyncio

import httpx

from aluvia_sdk import AluviaClient


async def main() -> None:
    """Main example using httpx."""
    # Initialize the Aluvia client
    client = AluviaClient(api_key="your-api-key-here")

    try:
        # Start the client
        connection = await client.start()
        print(f"Proxy started on {connection.url}")

        # Configure proxy rules
        await client.update_rules(["httpbin.org"])

        # Create httpx client with proxy
        async with httpx.AsyncClient(proxies=connection.as_httpx_proxies()) as http_client:
            # Make a request
            response = await http_client.get("https://httpbin.org/get")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
