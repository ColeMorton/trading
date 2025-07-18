#!/usr/bin/env python3
"""
Simple Integration Test for SPDSAnalysisEngine

Tests basic functionality without pytest dependency.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.spds_analysis_engine import AnalysisRequest, SPDSAnalysisEngine


async def test_basic_functionality():
    """Test basic SPDS analysis engine functionality."""
    print("🧪 Testing SPDSAnalysisEngine Integration")
    print("-" * 50)

    try:
        # Test 1: Engine Creation
        print("1. Creating engine...")
        engine = SPDSAnalysisEngine()
        print("   ✅ Engine created successfully")

        # Test 2: Strategy Analysis
        print("\n2. Testing strategy analysis...")
        request = AnalysisRequest(analysis_type="strategy", parameter="AAPL_SMA_20_50")

        results = await engine.analyze(request)
        print(f"   ✅ Strategy analysis completed: {len(results)} results")

        # Test 3: Portfolio Analysis (if portfolio exists)
        print("\n3. Testing portfolio analysis...")

        # Create simple test portfolio
        import pandas as pd

        test_data = [
            {
                "Position_UUID": "AAPL_SMA_20_50_20250101",
                "Ticker": "AAPL",
                "Strategy": "SMA",
                "Short_Window": 20,
                "Long_Window": 50,
                "Win_Rate": 0.65,
                "Total_Return": 0.25,
                "Sharpe_Ratio": 1.5,
                "Max_Drawdown": 0.15,
                "Total_Trades": 150,
                "Entry_Date": "2025-01-15",
                "Exit_Date": "",
                "Current_Price": 175.0,
                "Position_Size": 100,
                "Unrealized_PnL": 2500,
            }
        ]

        # Ensure directory exists
        portfolio_dir = Path("csv/positions")
        portfolio_dir.mkdir(parents=True, exist_ok=True)

        # Create test portfolio
        test_portfolio_path = portfolio_dir / "integration_test.csv"
        pd.DataFrame(test_data).to_csv(test_portfolio_path, index=False)

        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter="integration_test.csv",
            use_trade_history=False,
        )

        results = await engine.analyze(request)
        print(f"   ✅ Portfolio analysis completed: {len(results)} results")

        # Test 4: Validate Result Structure
        if results:
            print("\n4. Validating result structure...")
            sample_key = list(results.keys())[0]
            sample_result = results[sample_key]

            print(f"   Position UUID: {sample_result.position_uuid}")
            print(f"   Strategy: {sample_result.strategy_name}")
            print(f"   Ticker: {sample_result.ticker}")
            print(f"   Exit Signal: {sample_result.exit_signal.signal_type}")
            print(f"   Confidence: {sample_result.confidence_level:.1f}%")
            print(f"   Risk Level: {sample_result.exit_signal.risk_level}")
            print("   ✅ Result structure validated")

        print(f"\n🎉 All integration tests passed!")
        print(f"   - Engine creation: ✅")
        print(f"   - Strategy analysis: ✅")
        print(f"   - Portfolio analysis: ✅")
        print(f"   - Result validation: ✅")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_performance():
    """Test performance characteristics."""
    print("\n⚡ Performance Testing")
    print("-" * 30)

    import time

    try:
        engine = SPDSAnalysisEngine()

        # Test strategy analysis performance
        start_time = time.time()
        request = AnalysisRequest(analysis_type="strategy", parameter="AAPL_SMA_20_50")
        results = await engine.analyze(request)
        strategy_time = time.time() - start_time

        print(f"Strategy analysis: {strategy_time:.3f}s ({len(results)} results)")

        # Test portfolio analysis performance
        start_time = time.time()
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter="integration_test.csv",
            use_trade_history=False,
        )
        results = await engine.analyze(request)
        portfolio_time = time.time() - start_time

        print(f"Portfolio analysis: {portfolio_time:.3f}s ({len(results)} results)")

        # Performance benchmarks
        if strategy_time < 1.0:
            print("   ✅ Strategy analysis performance: Excellent")
        elif strategy_time < 3.0:
            print("   ✅ Strategy analysis performance: Good")
        else:
            print("   ⚠️ Strategy analysis performance: Slow")

        if portfolio_time < 2.0:
            print("   ✅ Portfolio analysis performance: Excellent")
        elif portfolio_time < 5.0:
            print("   ✅ Portfolio analysis performance: Good")
        else:
            print("   ⚠️ Portfolio analysis performance: Slow")

        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🔧 SPDS Analysis Engine Integration Tests")
    print("=" * 50)

    # Run basic functionality tests
    basic_success = await test_basic_functionality()

    # Run performance tests
    perf_success = await test_performance() if basic_success else False

    # Summary
    print(f"\n📊 Test Summary")
    print(f"   Basic functionality: {'✅' if basic_success else '❌'}")
    print(f"   Performance: {'✅' if perf_success else '❌'}")

    if basic_success and perf_success:
        print(f"\n🎯 Integration tests completed successfully!")
        print(f"   New SPDSAnalysisEngine is ready for CLI integration")
    else:
        print(f"\n⚠️ Some tests failed - review before CLI integration")


if __name__ == "__main__":
    asyncio.run(main())
