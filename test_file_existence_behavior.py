#!/usr/bin/env python3
"""
Test equity file existence checking behavior for FORCE_FRESH_ANALYSIS setting.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.strategies.tools.fresh_analysis_dispatcher import should_trigger_fresh_analysis
from app.tools.equity_export import (
    equity_file_exists,
    generate_equity_filename,
    get_equity_export_directory,
    get_equity_file_path,
)


def test_file_existence_behavior():
    """Test the equity file existence checking logic."""

    print("=" * 80)
    print("Testing Equity File Existence Checking Behavior")
    print("=" * 80)

    # Test strategy parameters
    ticker = "MA"
    strategy_type = "SMA"
    short_window = 78
    long_window = 82
    signal_window = None

    # Test 1: Check file path generation
    print("\n🔍 Testing file path generation...")
    filename = generate_equity_filename(
        ticker, strategy_type, short_window, long_window, signal_window
    )
    print(f"Generated filename: {filename}")

    export_dir = get_equity_export_directory(strategy_type)
    print(f"Export directory: {export_dir}")

    file_path = get_equity_file_path(
        ticker, strategy_type, short_window, long_window, signal_window
    )
    print(f"Full file path: {file_path}")

    # Test 2: Check if file exists
    print(
        f"\n📁 File exists: {equity_file_exists(ticker, strategy_type, short_window, long_window, signal_window)}"
    )

    # Test 3: Test FORCE_FRESH_ANALYSIS=True behavior
    print(f"\n🚀 Testing FORCE_FRESH_ANALYSIS=True...")
    config_force_true = {
        "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean", "FORCE_FRESH_ANALYSIS": True}
    }

    should_trigger_true = should_trigger_fresh_analysis(
        config=config_force_true,
        has_vectorbt_portfolio=False,
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
    )
    print(f"Should trigger fresh analysis (FORCE=True): {should_trigger_true}")
    print("✅ Expected: True (always trigger when FORCE_FRESH_ANALYSIS=True)")

    # Test 4: Test FORCE_FRESH_ANALYSIS=False behavior
    print(f"\n🎯 Testing FORCE_FRESH_ANALYSIS=False...")
    config_force_false = {
        "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean", "FORCE_FRESH_ANALYSIS": False}
    }

    should_trigger_false = should_trigger_fresh_analysis(
        config=config_force_false,
        has_vectorbt_portfolio=False,
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
    )
    print(f"Should trigger fresh analysis (FORCE=False): {should_trigger_false}")

    file_exists = equity_file_exists(
        ticker, strategy_type, short_window, long_window, signal_window
    )
    if file_exists:
        print("✅ Expected: False (skip because file exists)")
        print("🎉 BEHAVIOR: Only generating missing equity data files")
    else:
        print("✅ Expected: True (trigger because file doesn't exist)")
        print("🎉 BEHAVIOR: Will generate equity data for missing file")

    # Test 5: Summary
    print(f"\n📋 SUMMARY:")
    print(f"Strategy: {ticker} {strategy_type} {short_window}/{long_window}")
    print(f"Expected file: {file_path}")
    print(f"File exists: {file_exists}")
    print(f"FORCE_FRESH_ANALYSIS=True → Trigger: {should_trigger_true}")
    print(f"FORCE_FRESH_ANALYSIS=False → Trigger: {should_trigger_false}")

    print(f"\n✨ CONFIGURATION BEHAVIOR:")
    print(
        f"- FORCE_FRESH_ANALYSIS=True: Always regenerate equity files (ignore existing)"
    )
    print(
        f"- FORCE_FRESH_ANALYSIS=False: Only generate missing equity files (skip existing)"
    )


if __name__ == "__main__":
    test_file_existence_behavior()
