#!/usr/bin/env python3
"""
Direct test of concurrency calculation fixes.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables BEFORE imports
os.environ["USE_FIXED_RISK_CALC"] = "true"
os.environ["USE_FIXED_EXPECTANCY_CALC"] = "true"
os.environ["USE_FIXED_WIN_RATE_CALC"] = "true"
os.environ["USE_FIXED_SIGNAL_PROC"] = "true"

from app.concurrency.tools.risk_metrics import calculate_risk_contributions


def test_risk_calc_fix():
    """Test risk calculation fix directly."""
    print("\nTesting Risk Calculation Fix")
    print("-" * 50)

    # Create simple test data
    n_periods = 100
    n_strategies = 3

    # Create position arrays (some overlapping positions)
    position_arrays = [
        np.array([1] * 50 + [0] * 50),  # Strategy 1: first half
        np.array([0] * 25 + [1] * 50 + [0] * 25),  # Strategy 2: middle
        np.array([0] * 50 + [1] * 50),  # Strategy 3: second half
    ]

    # Create data frames with returns
    data_list = []
    for i in range(n_strategies):
        # Generate random returns
        np.random.seed(42 + i)
        returns = np.random.normal(0.001, 0.02, n_periods)
        prices = 100 * np.cumprod(1 + returns)

        from datetime import timedelta

        start_date = datetime(2024, 1, 1)
        end_date = start_date + timedelta(days=n_periods - 1)

        df = pl.DataFrame(
            {
                "Date": pl.date_range(start_date, end_date, interval="1d", eager=True),
                "Close": prices,
                "Position": position_arrays[i],
            },
        )
        data_list.append(df)

    # Test allocations
    allocations = [0.4, 0.35, 0.25]  # Sum to 1.0

    # Set up logging
    def log(msg, level="info"):
        print(f"[{level.upper()}] {msg}")

    # Calculate risk contributions
    print("\nCalculating risk contributions...")
    risk_metrics = calculate_risk_contributions(
        position_arrays,
        data_list,
        allocations,
        log,
    )

    # Check results
    print("\nRisk Contribution Results:")
    total_risk = 0.0
    for i in range(n_strategies):
        risk_contrib = risk_metrics.get(f"strategy_{i+1}_risk_contrib", 0.0)
        print(f"Strategy {i+1}: {risk_contrib:.4f}")
        total_risk += risk_contrib

    print(f"\nTotal Risk Contribution: {total_risk:.6f}")
    print(f"Valid (sums to 1.0): {'✓' if abs(total_risk - 1.0) < 1e-6 else '✗'}")

    # Check if fixed implementation was used
    if total_risk == 0:
        print(
            "\n⚠️ Risk contributions are all zero - fixed implementation may not be active",
        )

    return abs(total_risk - 1.0) < 1e-6


def test_expectancy_fix():
    """Test expectancy calculation fix."""
    print("\n\nTesting Expectancy Calculation Fix")
    print("-" * 50)

    # Import expectancy calculator
    try:
        from app.concurrency.tools.expectancy_calculator import (
            calculate_expectancy_fixed,
        )

        # Test data
        win_rate = 0.6  # 60% win rate
        avg_win = 0.05  # 5% average win
        avg_loss = 0.02  # 2% average loss

        # Calculate expectancy
        expectancy = calculate_expectancy_fixed(win_rate, avg_win, avg_loss)
        expected = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        print(f"Win rate: {win_rate:.2%}")
        print(f"Avg win: {avg_win:.2%}")
        print(f"Avg loss: {avg_loss:.2%}")
        print(f"Calculated expectancy: {expectancy:.6f}")
        print(f"Expected expectancy: {expected:.6f}")
        print(f"Valid: {'✓' if abs(expectancy - expected) < 1e-6 else '✗'}")

        return abs(expectancy - expected) < 1e-6

    except ImportError:
        print("✗ Expectancy calculator not found")
        return False


def test_win_rate_fix():
    """Test win rate calculation fix."""
    print("\n\nTesting Win Rate Calculation Fix")
    print("-" * 50)

    # Import win rate calculator
    try:
        from app.concurrency.tools.win_rate_calculator import calculate_win_rate_fixed

        # Test data
        winning_trades = 45
        total_trades = 75

        # Calculate win rate
        win_rate = calculate_win_rate_fixed(winning_trades, total_trades)
        expected = winning_trades / total_trades if total_trades > 0 else 0

        print(f"Winning trades: {winning_trades}")
        print(f"Total trades: {total_trades}")
        print(f"Calculated win rate: {win_rate:.4f}")
        print(f"Expected win rate: {expected:.4f}")
        print(f"Valid: {'✓' if abs(win_rate - expected) < 1e-6 else '✗'}")

        return abs(win_rate - expected) < 1e-6

    except ImportError:
        print("✗ Win rate calculator not found")
        return False


def test_signal_processor_fix():
    """Test signal processor fix."""
    print("\n\nTesting Signal Processor Fix")
    print("-" * 50)

    # Import signal processor
    try:
        from app.concurrency.tools.signal_processor import StandardizedSignalProcessor

        # Create test data with signals
        positions = [0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0]

        # Count trades (position changes from 0 to 1)
        processor = StandardizedSignalProcessor()
        signal_counts = processor.count_signals(positions)

        # Manual count
        expected_trades = 0
        for i in range(1, len(positions)):
            if positions[i - 1] == 0 and positions[i] == 1:
                expected_trades += 1

        print(f"Position array: {positions}")
        print(f"Calculated trades: {signal_counts.trade_signals}")
        print(f"Expected trades: {expected_trades}")
        print(
            f"Valid: {'✓' if signal_counts.trade_signals == expected_trades else '✗'}",
        )

        return signal_counts.trade_signals == expected_trades

    except ImportError:
        print("✗ Signal processor not found")
        return False


def main():
    """Run all fix tests."""
    print("Direct Testing of Concurrency Calculation Fixes")
    print("=" * 60)

    # Verify environment variables
    print("\nEnvironment Variables:")
    print(f"USE_FIXED_RISK_CALC: {os.environ.get('USE_FIXED_RISK_CALC', 'not set')}")
    print(
        f"USE_FIXED_EXPECTANCY_CALC: {os.environ.get('USE_FIXED_EXPECTANCY_CALC', 'not set')}",
    )
    print(
        f"USE_FIXED_WIN_RATE_CALC: {os.environ.get('USE_FIXED_WIN_RATE_CALC', 'not set')}",
    )
    print(
        f"USE_FIXED_SIGNAL_PROC: {os.environ.get('USE_FIXED_SIGNAL_PROC', 'not set')}",
    )

    # Run tests
    tests = [
        ("Risk Calculation", test_risk_calc_fix),
        ("Expectancy Calculation", test_expectancy_fix),
        ("Win Rate Calculation", test_win_rate_fix),
        ("Signal Processing", test_signal_processor_fix),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} test failed with error: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 50)

    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
        all_passed &= passed

    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
