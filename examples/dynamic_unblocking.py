"""Dynamic unblocking example with Playwright."""

import asyncio
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from aluvia_sdk import AluviaClient


async def main() -> None:
    """Main example demonstrating dynamic unblocking."""
    # Initialize the Aluvia client
    client = AluviaClient(api_key="your-api-key-here")

    try:
        # Start the client
        connection = await client.start()
        print(f"Proxy started on {connection.url}")

        # Configure geo targeting
        await client.update_target_geo("us_ca")
        await client.update_session_id("dynamic-session-1")

        # Track hostnames we've added to proxy rules
        proxied_hosts = set()

        async def visit_with_retry(url: str, max_retries: int = 2) -> str:
            """Visit URL with automatic retry on block detection."""
            async with async_playwright() as p:
                browser = await p.chromium.launch(proxy=connection.as_playwright())
                page = await browser.new_page()

                try:
                    for attempt in range(max_retries):
                        response = await page.goto(url, wait_until="domcontentloaded")
                        hostname = urlparse(url).hostname or ""

                        # Detect if the site blocked us
                        status = response.status if response else 0
                        title = await page.title()
                        is_blocked = status in (403, 429) or "blocked" in title.lower()

                        if is_blocked and hostname not in proxied_hosts:
                            print(f"Blocked by {hostname} — adding to proxy rules")

                            # Update routing rules to proxy this hostname
                            proxied_hosts.add(hostname)
                            await client.update_rules(list(proxied_hosts))

                            # Rotate to a fresh IP
                            await client.update_session_id(
                                f"retry-{asyncio.get_event_loop().time()}"
                            )

                            # Wait a bit before retry
                            await asyncio.sleep(1)
                            continue

                        # Success!
                        return await page.content()

                    raise Exception(f"Failed to access {url} after {max_retries} attempts")

                finally:
                    await page.close()
                    await browser.close()

        # Try visiting a site
        html = await visit_with_retry("https://example.com")
        print(f"Success! Retrieved {len(html)} bytes")

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
