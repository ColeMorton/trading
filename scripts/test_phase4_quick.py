"""
Quick Phase 4 test to validate basic functionality.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.processing import (
    get_cache_manager,
    get_memory_optimizer,
    get_performance_monitor,
)


def test_basic_functionality():
    """Test basic functionality of Phase 4 components."""
    print("Testing Phase 4 basic functionality...")

    # Ensure directories exist
    Path("cache").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # Test cache manager
    print("Testing cache manager...")
    cache_manager = get_cache_manager()
    cache_manager.put("test", "key1", {"data": "value1"})
    result = cache_manager.get("test", "key1")
    assert result is not None
    print("✅ Cache manager working")

    # Test memory optimizer
    print("Testing memory optimizer...")
    import pandas as pd

    memory_optimizer = get_memory_optimizer()
    df = pd.DataFrame({"x": range(1000), "y": ["A", "B"] * 500})
    optimized_df = memory_optimizer.optimize_dataframe(df)
    assert len(optimized_df) == len(df)
    print("✅ Memory optimizer working")

    # Test performance monitor
    print("Testing performance monitor...")
    perf_monitor = get_performance_monitor()
    with perf_monitor.monitor_operation("test_operation"):
        time.sleep(0.1)
    print("✅ Performance monitor working")

    print("\n🎉 All Phase 4 components working correctly!")

    # Simple performance test
    start_time = time.time()

    # Simulate portfolio analysis
    for i in range(5):
        df = pd.DataFrame({"price": range(1000), "volume": range(1000, 2000)})
        optimized_df = memory_optimizer.optimize_dataframe(df)
        optimized_df["sma"] = optimized_df["price"].rolling(10).mean()

        cache_key = f"test_{i}"
        cache_manager.put("test", cache_key, optimized_df.to_dict())

    total_time = (time.time() - start_time) * 1000  # ms
    print(f"\nSimple portfolio analysis test: {total_time:.1f}ms for 5 iterations")
    print(f"Average per iteration: {total_time/5:.1f}ms")

    return True


if __name__ == "__main__":
    try:
        test_basic_functionality()
        print("\n✅ Phase 4 basic test PASSED")
    except Exception as e:
        print(f"\n❌ Phase 4 basic test FAILED: {e}")
        sys.exit(1)
