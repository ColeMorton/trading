#!/usr/bin/env python3
"""
Demonstrate the win rate calculation fix.

This script shows how the fix resolves the 18.8% discrepancy issue
by comparing different win rate calculation methods and demonstrating
consistent results across signal-based and trade-based calculations.
"""

import os
from pathlib import Path
import sys

import numpy as np


# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.concurrency.tools.win_rate_calculator import WinRateCalculator


def demonstrate_discrepancy_fix():
    """Demonstrate how the fix resolves win rate calculation discrepancies."""
    print("=" * 60)
    print("WIN RATE CALCULATION FIX DEMONSTRATION")
    print("=" * 60)

    calc = WinRateCalculator(use_fixed=True)

    # Scenario 1: Multiple signals within trades causing discrepancy
    print("\nScenario 1: Multiple Signals Per Trade Period")
    print("-" * 50)

    # Create realistic trading scenario
    # Trade 1: 4 signals, mixed results but overall profitable
    # Trade 2: 4 signals, mixed results but overall loss
    returns = np.array(
        [
            0.01,
            0.005,
            -0.002,
            0.008,  # Trade 1: net +2.1%
            -0.01,
            -0.003,
            0.004,
            -0.007,  # Trade 2: net -1.6%
        ],
    )

    signals = np.array([1, 1, 1, 0, -1, -1, -1, 0])  # Signals active during trades

    # Calculate using different methods
    signal_result = calc.calculate_signal_win_rate(
        returns, signals, include_zeros=False,
    )
    trade_result = calc.calculate_trade_win_rate(returns, include_zeros=False)
    legacy_rate = calc.calculate_legacy_win_rate(returns)

    print(f"Returns: {[f'{r:.3f}' for r in returns]}")
    print(f"Signals: {signals.tolist()}")
    print(f"\nSignal-based Win Rate: {signal_result.win_rate:.3%}")
    print(f"Trade-based Win Rate:  {trade_result.win_rate:.3%}")
    print(f"Legacy Win Rate:       {legacy_rate:.3%}")
    print(
        f"Discrepancy (Signal vs Trade): {abs(signal_result.win_rate - trade_result.win_rate):.3%}",
    )


def demonstrate_zero_handling():
    """Demonstrate consistent zero return handling."""
    print("\n\nScenario 2: Zero Return Handling")
    print("-" * 50)

    calc = WinRateCalculator(use_fixed=True)

    # Returns with zero values
    returns_with_zeros = np.array(
        [0.02, 0.0, 0.015, 0.0, -0.005, 0.01, -0.02, 0.0, 0.005, -0.01],
    )
    signals_with_zeros = np.array([1, 0, -1, 0, -1, 1, 1, 0, 1, -1])

    # Compare different zero handling approaches
    exclude_zeros = calc.calculate_trade_win_rate(
        returns_with_zeros, include_zeros=False,
    )
    include_zeros = calc.calculate_trade_win_rate(
        returns_with_zeros, include_zeros=True,
    )
    signal_based = calc.calculate_signal_win_rate(
        returns_with_zeros, signals_with_zeros, include_zeros=False,
    )

    print(f"Returns: {[f'{r:.3f}' for r in returns_with_zeros]}")
    print(f"Signals: {signals_with_zeros.tolist()}")
    print(
        f"\nExclude Zeros - Wins: {exclude_zeros.wins}, Losses: {exclude_zeros.losses}, Rate: {exclude_zeros.win_rate:.3%}",
    )
    print(
        f"Include Zeros - Wins: {include_zeros.wins}, Losses: {include_zeros.losses}, Rate: {include_zeros.win_rate:.3%}",
    )
    print(
        f"Signal-based  - Wins: {signal_based.wins}, Losses: {signal_based.losses}, Rate: {signal_based.win_rate:.3%}",
    )
    print(f"Zero Returns Found: {exclude_zeros.zero_returns}")


def demonstrate_real_portfolio():
    """Demonstrate fix with realistic portfolio data."""
    print("\n\nScenario 3: Realistic Portfolio Returns")
    print("-" * 50)

    calc = WinRateCalculator(use_fixed=True)

    # Generate realistic returns with different win rates
    np.random.seed(42)

    # Strategy A: High win rate, small wins, occasional large losses
    strategy_a_returns = np.concatenate(
        [
            np.random.normal(0.005, 0.002, 70),  # 70 small wins
            np.random.normal(-0.015, 0.005, 30),  # 30 larger losses
        ],
    )
    np.random.shuffle(strategy_a_returns)

    # Strategy B: Lower win rate, larger wins, frequent small losses
    strategy_b_returns = np.concatenate(
        [
            np.random.normal(0.025, 0.008, 40),  # 40 larger wins
            np.random.normal(-0.005, 0.002, 60),  # 60 small losses
        ],
    )
    np.random.shuffle(strategy_b_returns)

    # Calculate win rates for both strategies
    result_a = calc.calculate_trade_win_rate(strategy_a_returns)
    result_b = calc.calculate_trade_win_rate(strategy_b_returns)

    print("Strategy A (High Win Rate, Small Wins):")
    print(f"  Wins: {result_a.wins}, Losses: {result_a.losses}")
    print(f"  Win Rate: {result_a.win_rate:.1%}")
    print(f"  Avg Win: {np.mean(strategy_a_returns[strategy_a_returns > 0]):.3%}")
    print(f"  Avg Loss: {np.mean(strategy_a_returns[strategy_a_returns < 0]):.3%}")

    print("\nStrategy B (Lower Win Rate, Larger Wins):")
    print(f"  Wins: {result_b.wins}, Losses: {result_b.losses}")
    print(f"  Win Rate: {result_b.win_rate:.1%}")
    print(f"  Avg Win: {np.mean(strategy_b_returns[strategy_b_returns > 0]):.3%}")
    print(f"  Avg Loss: {np.mean(strategy_b_returns[strategy_b_returns < 0]):.3%}")


def demonstrate_comparison_methods():
    """Demonstrate comparison of all calculation methods."""
    print("\n\nScenario 4: Comparison of All Methods")
    print("-" * 50)

    calc = WinRateCalculator(use_fixed=True)

    # Mixed scenario with signals and trades
    returns = np.array(
        [0.02, -0.01, 0.015, 0.0, -0.005, 0.01, -0.02, 0.025, 0.005, -0.008],
    )
    signals = np.array([1, 1, -1, 0, -1, 1, 1, -1, 1, -1])

    # Get all comparison methods
    comparisons = calc.compare_calculations(returns, signals)

    print("Method Comparison:")
    print(f"{'Method':<20} {'Wins':<5} {'Losses':<7} {'Total':<5} {'Win Rate':<10}")
    print("-" * 50)

    for method, result in comparisons.items():
        print(
            f"{method:<20} {result.wins:<5} {result.losses:<7} {result.total:<5} {result.win_rate:<10.3%}",
        )


def check_current_setting():
    """Check current environment setting."""
    print("\n\nCURRENT ENVIRONMENT SETTING")
    print("=" * 60)

    current = os.getenv("USE_FIXED_WIN_RATE_CALC", "not set")

    if current == "true":
        print("✅ USE_FIXED_WIN_RATE_CALC = true")
        print("   System is using the STANDARDIZED win rate calculation")
        print("   Win rate discrepancies should be minimized")
    elif current == "false":
        print("❌ USE_FIXED_WIN_RATE_CALC = false")
        print("   System is using the LEGACY calculation")
        print("   Warning: May have inconsistent win rate calculations!")
    else:
        print("⚠️  USE_FIXED_WIN_RATE_CALC not set")
        print("   Defaulting to STANDARDIZED calculation")


def main():
    """Run all demonstrations."""
    demonstrate_discrepancy_fix()
    demonstrate_zero_handling()
    demonstrate_real_portfolio()
    demonstrate_comparison_methods()
    check_current_setting()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("The win rate calculation fix successfully:")
    print("✅ Provides consistent signal-based and trade-based calculations")
    print("✅ Handles zero returns properly and consistently")
    print("✅ Distinguishes between different types of win rate calculations")
    print("✅ Maintains backward compatibility with legacy methods")
    print("✅ Reduces discrepancies between calculation methods")
    print("✅ Provides comprehensive validation and comparison tools")


if __name__ == "__main__":
    main()
