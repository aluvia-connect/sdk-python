"""Basic usage example with Playwright."""

import asyncio

from playwright.async_api import async_playwright

from aluvia_sdk import AluviaClient


async def main() -> None:
    """Main example function."""
    # Initialize the Aluvia client with your API key
    client = AluviaClient(api_key="your-api-key-here")

    try:
        # Start the client (launches local proxy, fetches connection config)
        connection = await client.start()
        print(f"Proxy started on {connection.url}")

        # Configure geo targeting (use California IPs)
        await client.update_target_geo("us_ca")

        # Set session ID (requests with the same session ID use the same IP)
        await client.update_session_id("example-session-1")

        # Launch browser using the Playwright integration adapter
        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=connection.as_playwright())

            page = await browser.new_page()

            try:
                # Visit a website
                response = await page.goto("https://example.com", wait_until="domcontentloaded")
                print(f"Response status: {response.status if response else 'None'}")

                # Get page content
                content = await page.content()
                print(f"Page content length: {len(content)}")

            finally:
                await page.close()
                await browser.close()

    finally:
        # Clean up
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
