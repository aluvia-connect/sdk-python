"""Quick script to add ipconfig.io rule."""

import asyncio
import httpx


async def main():
    api_key = "97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4"

    async with httpx.AsyncClient() as client:
        # Add rule to route ipconfig.io through proxy
        response = await client.patch(
            "https://api.aluvia.io/v1/account/connections/1850",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"rules": {"type": "hostname", "items": ["ipconfig.io"]}},
        )
        result = response.json()
        print(f"Response: {result}")


if __name__ == "__main__":
    asyncio.run(main())
