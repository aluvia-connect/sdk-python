"""
Simple test to verify BlockDetection implementation.
"""

import asyncio
from aluvia_sdk import BlockDetectionConfig, BlockDetection
from aluvia_sdk.client.logger import Logger


async def test_basic_initialization():
    """Test that BlockDetection can be initialized"""
    logger = Logger("info")

    # Test default config
    config = BlockDetectionConfig(enabled=True)
    detector = BlockDetection(config, logger)

    assert detector.is_enabled()
    assert not detector.is_auto_unblock()
    assert detector.get_network_idle_timeout_ms() == 3000

    print("✓ Basic initialization works")


async def test_with_auto_unblock():
    """Test BlockDetection with auto-unblock enabled"""
    logger = Logger("info")

    config = BlockDetectionConfig(
        enabled=True,
        auto_unblock=True,
        auto_unblock_on_suspected=True,
    )
    detector = BlockDetection(config, logger)

    assert detector.is_auto_unblock()
    assert detector.is_auto_unblock_on_suspected()

    print("✓ Auto-unblock configuration works")


async def test_scoring():
    """Test the scoring engine"""
    from aluvia_sdk.client.block_detection import DetectionSignal

    logger = Logger("info")
    config = BlockDetectionConfig(enabled=True)
    detector = BlockDetection(config, logger)

    # Test empty signals
    score, status = detector._compute_score([])
    assert score == 0.0
    assert status == "clear"

    # Test single high-weight signal
    signals = [
        DetectionSignal(name="http_status_403", weight=0.85, details="HTTP 403", source="fast")
    ]
    score, status = detector._compute_score(signals)
    assert score == 0.85
    assert status == "blocked"

    # Test multiple signals (probabilistic combination)
    signals = [
        DetectionSignal(name="test1", weight=0.5, details="", source="fast"),
        DetectionSignal(name="test2", weight=0.5, details="", source="fast"),
    ]
    score, status = detector._compute_score(signals)
    # 1 - (1-0.5) * (1-0.5) = 1 - 0.25 = 0.75
    assert abs(score - 0.75) < 0.001
    assert status == "blocked"

    print("✓ Scoring engine works correctly")


async def test_callback():
    """Test that callbacks can be set"""
    logger = Logger("info")

    callback_called = False

    async def on_detection(result, page):
        nonlocal callback_called
        callback_called = True

    config = BlockDetectionConfig(enabled=True, on_detection=on_detection)
    detector = BlockDetection(config, logger)

    assert detector.get_on_detection() is not None

    print("✓ Callback configuration works")


async def main():
    """Run all tests"""
    print("Testing BlockDetection implementation...\n")

    try:
        await test_basic_initialization()
        await test_with_auto_unblock()
        await test_scoring()
        await test_callback()

        print("\n✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
