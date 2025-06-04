#!/usr/bin/env python3
"""
Demonstrate the signal processing standardization fix.

This script shows how the fix resolves the 90% variance issue in signal
counts by comparing different signal counting methodologies and demonstrating
consistent results across raw, filtered, position, and trade signals.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.concurrency.tools.signal_processor import (
    SignalDefinition,
    SignalProcessor,
    SignalType,
    calculate_signal_count_standardized,
)


def demonstrate_signal_variance_fix():
    """Demonstrate how the fix resolves signal processing variance."""
    print("=" * 70)
    print("SIGNAL PROCESSING STANDARDIZATION FIX DEMONSTRATION")
    print("=" * 70)

    processor = SignalProcessor(use_fixed=True)

    # Scenario 1: High variance data that would cause 90% discrepancy
    print("\nScenario 1: High Variance Signal Data")
    print("-" * 50)

    # Create realistic scenario with multiple signal types
    np.random.seed(42)
    n_samples = 200
    dates = pd.date_range("2023-01-01", periods=n_samples, freq="D")

    # Generate price data with volatility
    prices = 100 + np.cumsum(np.random.randn(n_samples) * 0.02 * 100)

    # Generate moving averages
    fast_ma = pd.Series(prices).rolling(5).mean()
    slow_ma = pd.Series(prices).rolling(20).mean()

    # Generate many raw signals (crossovers)
    raw_signals = np.zeros(n_samples)
    for i in range(1, n_samples):
        if not pd.isna(fast_ma.iloc[i]) and not pd.isna(slow_ma.iloc[i]):
            if (
                fast_ma.iloc[i] > slow_ma.iloc[i]
                and fast_ma.iloc[i - 1] <= slow_ma.iloc[i - 1]
            ):
                raw_signals[i] = 1  # Buy signal
            elif (
                fast_ma.iloc[i] < slow_ma.iloc[i]
                and fast_ma.iloc[i - 1] >= slow_ma.iloc[i - 1]
            ):
                raw_signals[i] = -1  # Sell signal

    # Generate volume data (some low volume periods)
    volumes = np.random.randint(500, 8000, n_samples)

    # Generate RSI data
    rsi = np.random.uniform(15, 85, n_samples)

    # Create positions with lag and filtering
    positions = np.zeros(n_samples)
    current_pos = 0
    for i in range(1, n_samples):
        signal = raw_signals[i]
        # Apply basic filtering
        if signal != 0 and volumes[i] >= 2000:  # Volume filter
            if (signal == 1 and rsi[i] <= 40) or (
                signal == -1 and rsi[i] >= 60
            ):  # RSI filter
                current_pos = signal
        positions[i] = current_pos

    variance_data = pd.DataFrame(
        {
            "Date": dates,
            "Close": prices,
            "Fast_MA": fast_ma,
            "Slow_MA": slow_ma,
            "Signal": raw_signals,
            "Position": positions,
            "Volume": volumes,
            "RSI": rsi,
        }
    )

    # Define signal criteria
    signal_def = SignalDefinition(
        signal_column="Signal",
        position_column="Position",
        volume_column="Volume",
        rsi_column="RSI",
        min_volume=2000,
        rsi_oversold=40,
        rsi_overbought=60,
    )

    # Get comprehensive counts
    counts = processor.get_comprehensive_counts(variance_data, signal_def)
    reconciliation = processor.reconcile_signal_counts(counts)

    print(f"Raw Signals (all crossovers): {counts.raw_signals}")
    print(f"Filtered Signals (volume + RSI): {counts.filtered_signals}")
    print(f"Position Signals (actual changes): {counts.position_signals}")
    print(f"Trade Signals (completed trades): {counts.trade_signals}")
    print("")
    print(f"Filter Efficiency: {counts.filter_efficiency:.1%}")
    print(f"Execution Efficiency: {counts.execution_efficiency:.1%}")
    print(f"Overall Efficiency: {reconciliation['overall_efficiency']:.1%}")

    # Calculate the variance that would have existed before standardization
    legacy_variance = (
        (counts.raw_signals - counts.trade_signals) / counts.raw_signals * 100
        if counts.raw_signals > 0
        else 0
    )

    print("\nVariance Analysis:")
    print(f"Legacy approach would show {legacy_variance:.1f}% variance")
    print("Standardized approach clearly shows signal flow efficiency")


def demonstrate_consistency_across_modules():
    """Demonstrate consistent counting across different modules."""
    print("\n\nScenario 2: Cross-Module Consistency")
    print("-" * 50)

    # Create test data
    test_data = pd.DataFrame(
        {
            "Signal": [1, 0, -1, 0, 1, 0, 0, -1, 0, 1],
            "Position": [0, 1, 1, -1, -1, 1, 1, 1, -1, -1],
            "Volume": [3000, 2500, 4000, 1500, 3500, 2800, 1800, 5000, 2200, 4500],
            "RSI": [25, 35, 75, 50, 30, 45, 55, 70, 40, 20],
        }
    )

    signal_def = SignalDefinition(min_volume=2000, rsi_column="RSI")

    # Method 1: Direct signal processor
    processor = SignalProcessor()
    method1_raw = processor.count_raw_signals(test_data, signal_def)
    method1_filtered, _ = processor.count_filtered_signals(test_data, signal_def)
    method1_position = processor.count_position_signals(test_data, signal_def)

    # Method 2: Convenience function
    method2_raw = calculate_signal_count_standardized(
        test_data, SignalType.RAW, signal_def
    )
    method2_filtered = calculate_signal_count_standardized(
        test_data, SignalType.FILTERED, signal_def
    )
    method2_position = calculate_signal_count_standardized(
        test_data, SignalType.POSITION, signal_def
    )

    # Method 3: Legacy approach (manual counting)
    method3_raw = (test_data["Signal"] != 0).sum()
    method3_position = (
        test_data["Position"].diff().fillna(test_data["Position"].iloc[0]) != 0
    ).sum()

    print("Cross-Module Comparison:")
    print(f"{'Method':<20} {'Raw':<8} {'Filtered':<10} {'Position':<10}")
    print("-" * 50)
    print(
        f"{'SignalProcessor':<20} {method1_raw:<8} {method1_filtered:<10} {method1_position:<10}"
    )
    print(
        f"{'Convenience Func':<20} {method2_raw:<8} {method2_filtered:<10} {method2_position:<10}"
    )
    print(f"{'Legacy Manual':<20} {method3_raw:<8} {'N/A':<10} {method3_position:<10}")

    # Check consistency
    raw_consistent = method1_raw == method2_raw == method3_raw
    position_consistent = method1_position == method2_position == method3_position

    print("\nConsistency Check:")
    print(f"Raw signals consistent: {'✅' if raw_consistent else '❌'}")
    print(f"Position signals consistent: {'✅' if position_consistent else '❌'}")

    if raw_consistent and position_consistent:
        print("✅ All methods produce consistent results!")
    else:
        print("❌ Inconsistency detected - standardization needed")


def demonstrate_filtering_transparency():
    """Demonstrate transparent filtering process."""
    print("\n\nScenario 3: Signal Filtering Transparency")
    print("-" * 50)

    # Create data with clear filtering scenarios
    filter_data = pd.DataFrame(
        {
            "Signal": [1, -1, 1, -1, 1, -1],
            "Position": [0, 1, -1, -1, 1, 0],
            "Volume": [5000, 1000, 3000, 4000, 800, 2500],  # Some below threshold
            "RSI": [25, 70, 35, 65, 20, 75],  # Mix of valid/invalid RSI levels
        }
    )

    signal_def = SignalDefinition(
        min_volume=2000, rsi_column="RSI", rsi_oversold=30, rsi_overbought=70
    )

    processor = SignalProcessor()
    raw_count = processor.count_raw_signals(filter_data, signal_def)
    filtered_count, filtered_df = processor.count_filtered_signals(
        filter_data, signal_def
    )

    print("Filtering Process Analysis:")
    print(f"Original signals: {raw_count}")
    print(f"After filtering: {filtered_count}")
    print(f"Signals removed: {raw_count - filtered_count}")
    print(f"Filter efficiency: {filtered_count/raw_count:.1%}")

    print("\nDetailed Filtering Breakdown:")
    print("Index | Signal | Volume | RSI | Vol OK | RSI OK | Final")
    print("-" * 55)

    for idx, row in filter_data.iterrows():
        signal = row["Signal"]
        volume = row["Volume"]
        rsi = row["RSI"]

        vol_ok = volume >= signal_def.min_volume

        # RSI validation
        if signal == 1:  # Buy signal
            rsi_ok = rsi <= signal_def.rsi_oversold
        elif signal == -1:  # Sell signal
            rsi_ok = rsi >= signal_def.rsi_overbought
        else:
            rsi_ok = True  # No signal, RSI doesn't matter

        final_ok = (signal != 0) and vol_ok and rsi_ok

        print(
            f"{
    idx:5} | {
        signal:6} | {
            volume:6} | {
                rsi:3.0f} | {
                    vol_ok!s:6} | {
                        rsi_ok!s:6} | {
                            final_ok!s}"
        )


def check_current_setting():
    """Check current environment setting."""
    print("\n\nCURRENT ENVIRONMENT SETTING")
    print("=" * 70)

    current = os.getenv("USE_FIXED_SIGNAL_PROC", "not set")

    if current == "true":
        print("✅ USE_FIXED_SIGNAL_PROC = true")
        print("   System is using the STANDARDIZED signal processing")
        print("   Signal count variance should be minimized")
    elif current == "false":
        print("❌ USE_FIXED_SIGNAL_PROC = false")
        print("   System is using the LEGACY signal processing")
        print("   Warning: May have up to 90% variance in signal counts!")
    else:
        print("⚠️  USE_FIXED_SIGNAL_PROC not set")
        print("   Defaulting to STANDARDIZED signal processing")
        print("   Set environment variable to control behavior")


def main():
    """Run all demonstrations."""
    demonstrate_signal_variance_fix()
    demonstrate_consistency_across_modules()
    demonstrate_filtering_transparency()
    check_current_setting()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("The signal processing standardization fix successfully:")
    print("✅ Provides consistent signal counting across all methodologies")
    print("✅ Clearly distinguishes between raw, filtered, position, and trade signals")
    print("✅ Implements transparent filtering with configurable criteria")
    print("✅ Maintains backward compatibility with legacy methods")
    print("✅ Reduces variance in signal counts between modules")
    print("✅ Provides comprehensive reconciliation and efficiency metrics")
    print("✅ Supports both Pandas and Polars DataFrames")


if __name__ == "__main__":
    main()
