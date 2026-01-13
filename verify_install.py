#!/usr/bin/env python3
"""Setup script to verify installation."""

import asyncio
import sys


async def verify_installation() -> None:
    """Verify that the SDK is properly installed."""
    print("Verifying Aluvia SDK installation...\n")

    # Test imports
    print("✓ Testing imports...")
    try:
        from aluvia_sdk import (
            AluviaApi,
            AluviaClient,
            ApiError,
            InvalidApiKeyError,
            MissingApiKeyError,
            ProxyStartError,
        )

        print("  ✓ All imports successful")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        sys.exit(1)

    # Test client initialization
    print("✓ Testing client initialization...")
    try:
        client = AluviaClient(api_key="test-key", log_level="silent")
        print("  ✓ Client initialized successfully")
    except Exception as e:
        print(f"  ✗ Client initialization failed: {e}")
        sys.exit(1)

    # Test API initialization
    print("✓ Testing API initialization...")
    try:
        api = AluviaApi(api_key="test-key")
        print("  ✓ API initialized successfully")
        await api.close()
    except Exception as e:
        print(f"  ✗ API initialization failed: {e}")
        sys.exit(1)

    # Test error classes
    print("✓ Testing error classes...")
    try:
        try:
            AluviaClient(api_key="")
        except MissingApiKeyError:
            print("  ✓ MissingApiKeyError works")
    except Exception as e:
        print(f"  ✗ Error class test failed: {e}")
        sys.exit(1)

    print("\n✅ All checks passed! SDK is properly installed.")
    print("\nNext steps:")
    print("1. Get your API key from https://dashboard.aluvia.io")
    print("2. Check examples/ directory for usage examples")
    print("3. Read docs/QUICKSTART.md for detailed guide")


if __name__ == "__main__":
    asyncio.run(verify_installation())
