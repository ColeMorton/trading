#!/usr/bin/env python3
"""
Test fresh analysis dispatcher for equity export.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.strategies.tools.fresh_analysis_dispatcher import (
    dispatch_fresh_analysis,
    should_trigger_fresh_analysis,
)


def test_fresh_analysis():
    """Test the fresh analysis dispatcher directly."""

    def log_func(msg, level="info"):
        print(f"{level.upper()}: {msg}")

    # Test configuration that should trigger fresh analysis
    config = {
        "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean", "FORCE_FRESH_ANALYSIS": True},
        "REFRESH": True,
        "USE_CURRENT": True,
        "BASE_DIR": project_root,
    }

    print("=" * 60)
    print("Testing Fresh Analysis Dispatcher")
    print("=" * 60)

    # Test 1: Check if fresh analysis should be triggered
    has_portfolio = False  # Simulate pre-computed data scenario
    should_trigger = should_trigger_fresh_analysis(config, has_portfolio)
    print(f"Should trigger fresh analysis: {should_trigger}")

    if should_trigger:
        print("\n🚀 Triggering fresh SMA analysis for MA...")

        # Test 2: Dispatch fresh SMA analysis
        fresh_portfolio = dispatch_fresh_analysis(
            ticker="MA",
            strategy_type="SMA",
            short_window=78,
            long_window=82,
            signal_window=None,
            config=config,
            log=log_func,
        )

        if fresh_portfolio is not None:
            print(f"✅ Fresh analysis successful!")
            print(f"Portfolio type: {type(fresh_portfolio)}")
            print(f"Has .value() method: {hasattr(fresh_portfolio, 'value')}")
            print(f"Has .stats() method: {hasattr(fresh_portfolio, 'stats')}")

            # Test equity data extraction
            if hasattr(fresh_portfolio, "value") and hasattr(fresh_portfolio, "stats"):
                print("\n🎯 Testing equity data extraction...")

                from app.tools.equity_data_extractor import (
                    MetricType,
                    extract_equity_data_from_portfolio,
                )

                try:
                    equity_data = extract_equity_data_from_portfolio(
                        portfolio=fresh_portfolio,
                        metric_type=MetricType.MEAN,
                        config=config,
                        log=log_func,
                    )

                    if equity_data:
                        print(f"✅ Equity data extracted successfully!")
                        print(f"Equity data type: {type(equity_data)}")
                        print(f"Data points: {len(equity_data.equity)}")
                        print(
                            "\n🎉 COMPLETE SUCCESS: Fresh analysis + equity export working!"
                        )
                    else:
                        print("❌ Equity data extraction failed")

                except Exception as e:
                    print(f"❌ Equity extraction error: {str(e)}")

        else:
            print("❌ Fresh analysis failed")
    else:
        print("❌ Fresh analysis not triggered - check configuration")


if __name__ == "__main__":
    test_fresh_analysis()
