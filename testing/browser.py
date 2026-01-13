"""Browser test script using Playwright - equivalent to the Node.js browser test."""

import asyncio
import sys
import os

# Add parent directory to path to import aluvia_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aluvia_sdk import AluviaClient

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright is not installed.")
    print("Install it with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)


async def main():
    """Main browser test."""
    print("=" * 60)
    print("Aluvia Python SDK - Browser Test (Playwright)")
    print("=" * 60)
    print()
    print("Note: Using local proxy with full HTTPS support (proxy.py)")
    print("      The browser will stay open until you press Ctrl+C.")
    print()

    # Initialize client with LOCAL PROXY (now supports HTTPS!)
    client = AluviaClient(
        api_key="97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4",
        connection_id=1850,
        local_proxy=True,  # Local proxy now works with HTTPS
        log_level="debug",
    )

    print("1. Starting client (local proxy mode)...")
    connection = await client.start()
    print(f"   ✓ Client started")
    print()

    # Launch browser with proxy
    print("2. Launching Chromium browser with proxy...")
    async with async_playwright() as p:
        try:
            # In local proxy mode, asPlaywright() returns simple proxy URL
            proxy_settings = connection.asPlaywright()
            print(f"   Using proxy: {proxy_settings.get('server')}")

            browser = await p.chromium.launch(
                proxy=proxy_settings,
                headless=False,
            )
            print(f"   ✓ Browser launched")
            print()

            print("3. Opening new page and navigating to ipconfig.io...")
            page = await browser.new_page()

            try:
                await page.goto("https://ipconfig.io/json", timeout=30000)
                print(f"   ✓ Page loaded")
                print()

                # Get page content to show the IP info
                content = await page.content()
                if "ip" in content.lower():
                    print("4. Page content loaded successfully!")
                    print(f"   Content length: {len(content)} bytes")

                    # Try to extract IP info
                    text = await page.text_content("body")
                    if text:
                        print(f"   Data: {text[:200]}...")
                print()
            except Exception as error:
                print(f"   ⚠ Error loading page: {error}")
                print("   Browser will stay open anyway for manual testing.")
                print()

            # Keep browser open indefinitely - this runs regardless of page load success
            print("5. Browser is now open and ready to use.")
            print("   Press Ctrl+C to close the browser and exit.")
            print()

            # Wait indefinitely (or until Ctrl+C)
            try:
                await asyncio.sleep(float("inf"))
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\n   ✓ Received exit signal")
                print()

        except Exception as e:
            print(f"   ✗ Error launching browser: {e}")
            print()
        finally:
            if "browser" in locals():
                print("6. Closing browser...")
                await browser.close()
                print(f"   ✓ Browser closed")
                print()

    # Cleanup
    print("7. Closing connection...")
    await connection.close()
    print(f"   ✓ Connection closed")
    print()

    print("=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
