#!/usr/bin/env python3
"""
Test script to verify equity data export with live strategy analysis.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.strategies.tools.summary_processing import process_ticker_portfolios


def test_equity_export():
    """Test equity export with a simple strategy."""

    # Test configuration that should trigger live backtesting
    test_strategy = {
        "Ticker": "AAPL",
        "Strategy Type": "SMA",
        "Short Window": 20,
        "Long Window": 50,
        "Signal Window": None,
    }

    config = {
        "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
        "REFRESH": True,  # Force fresh data
        "USE_CURRENT": True,
        "BASE_DIR": project_root,
    }

    def log_func(msg, level="info"):
        print(f"{level.upper()}: {msg}")

    print("=" * 60)
    print("Testing Equity Data Export with Live Strategy Analysis")
    print("=" * 60)

    try:
        # Process the strategy (this should create VectorBT Portfolio objects)
        result = process_ticker_portfolios("AAPL", test_strategy, config, log_func)

        if result and len(result) > 0:
            portfolio_stats = result[0]
            has_equity_data = "_equity_data" in portfolio_stats

            print(f"\n📊 RESULTS:")
            print(f"  - Strategy processed successfully: ✅")
            print(f"  - Portfolio stats generated: ✅")
            print(f"  - Equity data attached: {'✅' if has_equity_data else '❌'}")

            if has_equity_data:
                equity_data = portfolio_stats["_equity_data"]
                print(f"  - Equity data type: {type(equity_data)}")
                print(f"  - Equity data content: {str(equity_data)[:100]}...")

                # Check if it's an EquityData object
                if hasattr(equity_data, "equity"):
                    print(f"  - Equity data points: {len(equity_data.equity)}")
                    print("\n🎉 SUCCESS: Equity data export is working correctly!")
                else:
                    print(
                        f"  - Equity data is not an EquityData object, it's a {type(equity_data)}"
                    )
                    print(
                        "\n⚠️  PARTIAL SUCCESS: Equity data is attached but in wrong format"
                    )

                print(
                    "The issue with your CSV is that it contains pre-computed results."
                )
                print("For equity export, you need to run live strategy analysis.")
            else:
                print(
                    "\n❌ No equity data found - this shouldn't happen with live analysis"
                )
        else:
            print("\n❌ Strategy processing failed")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_equity_export()
