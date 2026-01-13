"""Quick test using httpx with proxy."""

import asyncio
from aluvia_sdk import AluviaClient


async def main():
    client = AluviaClient(
        api_key="97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4",
        connection_id=1850,
        local_proxy=True,
        log_level="info",
    )

    conn = await client.start()
    print(f"✓ Proxy running on: {conn.url}")

    # Test with httpx (use 'proxy' not 'proxies')
    import httpx

    async with httpx.AsyncClient(proxy=conn.url, timeout=30.0) as http_client:
        print("\nTesting HTTPS request through proxy...")
        response = await http_client.get("https://ipconfig.io/json")
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ IP: {data.get('ip')}")
        print(f"✓ Country: {data.get('country')}")

    await client.stop()
    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
