#!/usr/bin/env python3
"""
Test script for Aluvia CLI
"""
import subprocess
import sys
import os


def test_cli():
    """Test the CLI commands."""
    print("Testing Aluvia CLI...")
    print("=" * 50)

    # Test 1: Help command
    print("\n1. Testing help command...")
    result = subprocess.run(
        [sys.executable, "-m", "aluvia_sdk.bin.cli", "help"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✓ Help command works")
    else:
        print("✗ Help command failed")
        print(result.stderr)

    # Test 2: Help JSON command
    print("\n2. Testing help --json command...")
    result = subprocess.run(
        [sys.executable, "-m", "aluvia_sdk.bin.cli", "help", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.startswith("{"):
        print("✓ Help JSON command works")
    else:
        print("✗ Help JSON command failed")

    # Test 3: Session list command
    print("\n3. Testing session list command...")
    result = subprocess.run(
        [sys.executable, "-m", "aluvia_sdk.bin.cli", "session", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "sessions" in result.stdout:
        print("✓ Session list command works")
        print(f"   Output: {result.stdout.strip()}")
    else:
        print("✗ Session list command failed")
        print(result.stderr)

    # Test 4: Check if API key is set
    print("\n4. Checking environment...")
    api_key = os.environ.get("ALUVIA_API_KEY")
    if api_key:
        print(f"✓ ALUVIA_API_KEY is set")
    else:
        print("⚠ ALUVIA_API_KEY is not set")
        print("   To test session start, set: export ALUVIA_API_KEY=your_key")

    print("\n" + "=" * 50)
    print("CLI tests complete!")
    print("\nTo start a session, run:")
    print("  python -m aluvia_sdk.bin.cli session start https://example.com")
    print("  python -m aluvia_sdk.bin.cli session start https://example.com --headful")


if __name__ == "__main__":
    test_cli()
