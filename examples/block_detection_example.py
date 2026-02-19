"""
Example: Using Block Detection with AluviaClient

This example demonstrates how to use the block detection system to automatically
detect and handle website blocks, CAPTCHAs, and WAF challenges.
"""
import asyncio
from aluvia_sdk import AluviaClient, BlockDetectionConfig


async def example_with_detection_callback():
    """Example with custom detection callback"""
    print("Example 1: Block Detection with Custom Callback\n")
    
    # Define callback to handle detection results
    async def on_detection(result, page):
        print(f"\n🔍 Block Detection:")
        print(f"  URL: {result.url}")
        print(f"  Status: {result.block_status}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Signals: {len(result.signals)}")
        for signal in result.signals[:3]:  # Show first 3 signals
            print(f"    - {signal.name} (weight: {signal.weight}): {signal.details}")
    
    # Configure block detection with callback
    block_config = BlockDetectionConfig(
        enabled=True,
        on_detection=on_detection,
        auto_unblock=False,  # Manual handling
    )
    
    # Note: You need a valid API key to run this
    # client = AluviaClient(
    #     api_key="your-api-key",
    #     start_playwright=True,
    #     block_detection=block_config,
    # )
    # connection = await client.start()
    # # Use connection.browser to navigate...
    # await client.stop()
    
    print("✓ Configuration created successfully")


async def example_with_auto_unblock():
    """Example with automatic unblocking"""
    print("\nExample 2: Block Detection with Auto-Unblock\n")
    
    # Configure auto-unblock for blocked and suspected blocks
    block_config = BlockDetectionConfig(
        enabled=True,
        auto_unblock=True,
        auto_unblock_on_suspected=True,  # Also retry suspected blocks
    )
    
    # The client will automatically:
    # 1. Detect blocks via fast pass (HTTP status, headers)
    # 2. Detect blocks via full pass (content analysis after page load)
    # 3. Add blocked hostnames to routing rules
    # 4. Reload the page through Aluvia proxy
    
    # client = AluviaClient(
    #     api_key="your-api-key",
    #     start_playwright=True,
    #     block_detection=block_config,
    # )
    # connection = await client.start()
    # await client.stop()
    
    print("✓ Auto-unblock configuration created")


async def example_with_custom_detection_rules():
    """Example with custom detection rules"""
    print("\nExample 3: Custom Detection Rules\n")
    
    # Configure with custom selectors and keywords
    block_config = BlockDetectionConfig(
        enabled=True,
        auto_unblock=True,
        # Add custom challenge selectors to detect
        challenge_selectors=[
            "#challenge-form",
            ".custom-captcha",
            "#my-security-check",
        ],
        # Add custom keywords to detect in title/text
        extra_keywords=[
            "security verification",
            "access restricted",
        ],
        # Add custom HTTP status codes to treat as blocks
        extra_status_codes=[
            401,  # Unauthorized
            418,  # I'm a teapot (example custom code)
        ],
        # Adjust network idle timeout (default 3000ms)
        network_idle_timeout_ms=5000,
    )
    
    print("✓ Custom detection rules configured")


async def example_detection_only_mode():
    """Example of detection-only mode (no auto-unblock)"""
    print("\nExample 4: Detection-Only Mode\n")
    
    # Track detected blocks
    detected_blocks = []
    
    async def log_detection(result, page):
        detected_blocks.append({
            "url": result.url,
            "hostname": result.hostname,
            "status": result.block_status,
            "score": result.score,
        })
        print(f"Detected: {result.hostname} - {result.block_status} (score: {result.score:.2f})")
    
    # Configure detection without auto-unblock
    block_config = BlockDetectionConfig(
        enabled=True,
        auto_unblock=False,  # Only detect, don't auto-retry
        on_detection=log_detection,
    )
    
    # This is useful for:
    # - Monitoring which sites are blocking you
    # - Testing block detection accuracy
    # - Building custom unblock strategies
    
    print("✓ Detection-only mode configured")


async def example_cli_usage():
    """Example of CLI usage with block detection"""
    print("\nExample 5: CLI Usage\n")
    
    print("Start a session with block detection:")
    print("  python -m aluvia_sdk.bin.cli session start https://example.com")
    print()
    print("Start with auto-unblock:")
    print("  python -m aluvia_sdk.bin.cli session start https://example.com --auto-unblock")
    print()
    print("Start with block detection disabled:")
    print("  python -m aluvia_sdk.bin.cli session start https://example.com --disable-block-detection")
    print()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Block Detection Feature Examples")
    print("=" * 60)
    print()
    
    await example_with_detection_callback()
    await example_with_auto_unblock()
    await example_with_custom_detection_rules()
    await example_detection_only_mode()
    await example_cli_usage()
    
    print()
    print("=" * 60)
    print("📚 Key Features:")
    print("  • Fast pass (HTTP status/headers at domcontentloaded)")
    print("  • Full pass (content analysis after networkidle)")
    print("  • SPA detection (for client-side navigation)")
    print("  • Weighted scoring system (0.0-1.0)")
    print("  • Auto-unblock (adds rules + reloads page)")
    print("  • Persistent block tracking (avoids retry loops)")
    print("  • Custom callbacks for detection events")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
