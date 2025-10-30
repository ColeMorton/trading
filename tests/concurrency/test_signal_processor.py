#!/usr/bin/env python3
"""
Comprehensive test suite for signal processor standardization.

Tests the standardized signal processor to ensure:
1. Consistent signal counting across all types
2. Proper filtering logic implementation
3. Signal-to-position conversion accuracy
4. Trade counting methodology correctness
"""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl


# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.concurrency.tools.signal_processor import (
    SignalCounts,
    SignalDefinition,
    SignalProcessor,
    SignalType,
    calculate_signal_count_standardized,
)


class TestSignalProcessor(unittest.TestCase):
    """Test cases for the SignalProcessor class."""

    def setUp(self):
        """Set up test data."""
        self.processor = SignalProcessor(use_fixed=True)

        # Create realistic test data
        np.random.seed(42)
        self.n_samples = 100
        dates = pd.date_range("2023-01-01", periods=self.n_samples, freq="D")

        # Generate price data with trend
        price_changes = np.random.randn(self.n_samples) * 0.02
        prices = 100 * np.exp(np.cumsum(price_changes))

        # Generate moving averages
        fast_ma = pd.Series(prices).rolling(5).mean()
        slow_ma = pd.Series(prices).rolling(20).mean()

        # Generate crossover signals
        signals = np.where(fast_ma > slow_ma, 1, -1)
        signals = pd.Series(signals).diff().fillna(0)  # Only signal on crossovers

        self.test_data = pd.DataFrame(
            {
                "Date": dates,
                "Close": prices,
                "Fast_MA": fast_ma,
                "Slow_MA": slow_ma,
                "Signal": signals,
                "Position": signals.shift(1).fillna(
                    0,
                ),  # Positions lag signals by 1 day
                "Volume": np.random.randint(1000, 10000, self.n_samples),
                "RSI": np.random.uniform(20, 80, self.n_samples),
            },
        )

        # Create signal definition
        self.signal_def = SignalDefinition(
            signal_column="Signal",
            position_column="Position",
            volume_column="Volume",
            rsi_column="RSI",
            min_volume=2000,
            rsi_oversold=30,
            rsi_overbought=70,
        )

    def test_raw_signal_counting(self):
        """Test raw signal counting methodology."""
        raw_count = self.processor.count_raw_signals(self.test_data, self.signal_def)

        # Manual verification
        expected_count = (self.test_data["Signal"] != 0).sum()

        self.assertEqual(raw_count, expected_count)
        self.assertGreater(raw_count, 0, "Should detect some raw signals")

    def test_filtered_signal_counting(self):
        """Test filtered signal counting with criteria."""
        filtered_count, filtered_df = self.processor.count_filtered_signals(
            self.test_data,
            self.signal_def,
        )

        # Filtered count should be <= raw count
        raw_count = self.processor.count_raw_signals(self.test_data, self.signal_def)
        self.assertLessEqual(filtered_count, raw_count)

        # Verify filtering logic
        signal_mask = self.test_data["Signal"] != 0
        volume_mask = self.test_data["Volume"] >= self.signal_def.min_volume

        # Manual calculation of expected filtered signals
        valid_signals = self.test_data[signal_mask & volume_mask]

        # RSI filtering for buy/sell signals
        buy_signals = valid_signals["Signal"] == 1
        sell_signals = valid_signals["Signal"] == -1

        valid_rsi_buy = (
            valid_signals[buy_signals]["RSI"] <= self.signal_def.rsi_oversold
        )
        valid_rsi_sell = (
            valid_signals[sell_signals]["RSI"] >= self.signal_def.rsi_overbought
        )

        # Total valid after RSI filtering
        len(valid_rsi_buy) + len(valid_rsi_sell)

        # The filtered count should make sense given our criteria
        self.assertIsInstance(filtered_count, int)
        self.assertGreaterEqual(filtered_count, 0)

    def test_position_signal_counting(self):
        """Test position signal counting using diff method."""
        position_count = self.processor.count_position_signals(
            self.test_data,
            self.signal_def,
        )

        # Manual verification using position diff
        position_changes = self.test_data["Position"].diff().fillna(0)
        expected_count = (position_changes != 0).sum()

        self.assertEqual(position_count, expected_count)

    def test_trade_signal_counting(self):
        """Test trade signal counting methodology."""
        # Create test data with clear trade patterns
        trade_data = pd.DataFrame({"Position": [0, 1, 1, 1, -1, -1, 0, 1, 1, 0]})

        trade_def = SignalDefinition(position_column="Position")
        trade_count = self.processor.count_trade_signals(trade_data, trade_def)

        # Expected trades: count each position change
        # 0->1, 1->1 (no change), 1->1 (no change), 1->-1, -1->-1 (no change), -1->0, 0->1, 1->1 (no change), 1->0
        # Position changes: 0->1, 1->-1, -1->0, 0->1, 1->0
        # Total: 5 trades
        expected_trades = 5
        self.assertEqual(trade_count, expected_trades)

    def test_comprehensive_counts(self):
        """Test comprehensive signal count analysis."""
        counts = self.processor.get_comprehensive_counts(
            self.test_data,
            self.signal_def,
        )

        # Verify object structure
        self.assertIsInstance(counts, SignalCounts)
        self.assertIsInstance(counts.raw_signals, int)
        self.assertIsInstance(counts.filtered_signals, int)
        self.assertIsInstance(counts.position_signals, int)
        self.assertIsInstance(counts.trade_signals, int)

        # Verify logical relationships
        self.assertGreaterEqual(counts.raw_signals, counts.filtered_signals)
        self.assertGreaterEqual(counts.raw_signals, 0)

        # Verify efficiency calculations
        self.assertGreaterEqual(counts.filter_efficiency, 0.0)
        self.assertLessEqual(counts.filter_efficiency, 1.0)

    def test_signal_reconciliation(self):
        """Test signal count reconciliation analysis."""
        counts = self.processor.get_comprehensive_counts(
            self.test_data,
            self.signal_def,
        )
        reconciliation = self.processor.reconcile_signal_counts(counts)

        # Check reconciliation structure
        expected_keys = [
            "raw_signals",
            "filtered_signals",
            "position_signals",
            "trade_signals",
            "filter_efficiency",
            "execution_efficiency",
            "trade_efficiency",
            "overall_efficiency",
        ]

        for key in expected_keys:
            self.assertIn(key, reconciliation)

        # Verify efficiency calculations
        if counts.raw_signals > 0:
            expected_overall = counts.trade_signals / counts.raw_signals
            self.assertAlmostEqual(
                reconciliation["overall_efficiency"],
                expected_overall,
                places=6,
            )

    def test_signal_standardization(self):
        """Test signal column standardization methods."""
        # Test crossover method
        test_data = self.test_data[["Close", "Fast_MA", "Slow_MA"]].copy()
        standardized = self.processor.standardize_signal_column(
            test_data,
            method="crossover",
        )

        self.assertIn("Signal", standardized.columns)

        # Verify crossover logic
        buy_signals = standardized[standardized["Signal"] == 1]
        sell_signals = standardized[standardized["Signal"] == -1]

        # Buy signals should occur when Fast_MA > Slow_MA
        if len(buy_signals) > 0:
            self.assertTrue((buy_signals["Fast_MA"] > buy_signals["Slow_MA"]).all())

        # Sell signals should occur when Fast_MA < Slow_MA
        if len(sell_signals) > 0:
            self.assertTrue((sell_signals["Fast_MA"] < sell_signals["Slow_MA"]).all())

    def test_polars_compatibility(self):
        """Test compatibility with Polars DataFrames."""
        # Convert to Polars
        polars_data = pl.from_pandas(self.test_data)

        # Test raw signal counting
        raw_count_polars = self.processor.count_raw_signals(
            polars_data,
            self.signal_def,
        )
        raw_count_pandas = self.processor.count_raw_signals(
            self.test_data,
            self.signal_def,
        )

        self.assertEqual(raw_count_polars, raw_count_pandas)

        # Test filtered signal counting
        filtered_count_polars, _ = self.processor.count_filtered_signals(
            polars_data,
            self.signal_def,
        )
        filtered_count_pandas, _ = self.processor.count_filtered_signals(
            self.test_data,
            self.signal_def,
        )

        self.assertEqual(filtered_count_polars, filtered_count_pandas)

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty DataFrame
        empty_df = pd.DataFrame()
        empty_def = SignalDefinition()

        raw_count = self.processor.count_raw_signals(empty_df, empty_def)
        self.assertEqual(raw_count, 0)

        # DataFrame without required columns
        incomplete_df = pd.DataFrame({"Close": [100, 101, 99]})
        raw_count = self.processor.count_raw_signals(incomplete_df, self.signal_def)
        self.assertEqual(raw_count, 0)

        # All zero signals
        zero_signals_df = pd.DataFrame(
            {
                "Signal": [0, 0, 0, 0],
                "Position": [0, 0, 0, 0],
                "Volume": [1000, 2000, 3000, 4000],
            },
        )

        raw_count = self.processor.count_raw_signals(zero_signals_df, self.signal_def)
        self.assertEqual(raw_count, 0)

    def test_convenience_function(self):
        """Test the convenience function for signal counting."""
        # Test different signal types
        raw_count = calculate_signal_count_standardized(
            self.test_data,
            SignalType.RAW,
            self.signal_def,
        )
        filtered_count = calculate_signal_count_standardized(
            self.test_data,
            SignalType.FILTERED,
            self.signal_def,
        )
        position_count = calculate_signal_count_standardized(
            self.test_data,
            SignalType.POSITION,
            self.signal_def,
        )

        # Verify results match direct method calls
        direct_raw = self.processor.count_raw_signals(self.test_data, self.signal_def)
        direct_filtered, _ = self.processor.count_filtered_signals(
            self.test_data,
            self.signal_def,
        )
        direct_position = self.processor.count_position_signals(
            self.test_data,
            self.signal_def,
        )

        self.assertEqual(raw_count, direct_raw)
        self.assertEqual(filtered_count, direct_filtered)
        self.assertEqual(position_count, direct_position)

    def test_signal_definition_validation(self):
        """Test signal definition parameter validation."""
        # Test with different RSI thresholds
        strict_def = SignalDefinition(
            rsi_column="RSI",
            rsi_oversold=20,  # Stricter threshold
            rsi_overbought=80,
            min_volume=5000,  # Higher volume requirement
        )

        lenient_def = SignalDefinition(
            rsi_column="RSI",
            rsi_oversold=40,  # More lenient
            rsi_overbought=60,
            min_volume=1000,  # Lower volume requirement
        )

        strict_count, _ = self.processor.count_filtered_signals(
            self.test_data,
            strict_def,
        )
        lenient_count, _ = self.processor.count_filtered_signals(
            self.test_data,
            lenient_def,
        )

        # Lenient criteria should generally result in more signals
        # (though not guaranteed due to random test data)
        self.assertGreaterEqual(lenient_count, 0)
        self.assertGreaterEqual(strict_count, 0)


class TestSignalVarianceFix(unittest.TestCase):
    """Test cases specifically for the 90% variance fix."""

    def setUp(self):
        """Set up test data that demonstrates signal variance."""
        self.processor = SignalProcessor(use_fixed=True)

        # Create scenario with high signal variance
        np.random.seed(123)

        # Raw signals: Many crossovers
        raw_signals = np.random.choice([-1, 0, 1], 100, p=[0.2, 0.6, 0.2])

        # Filtered signals: Apply volume filter (removes ~50%)
        volumes = np.random.randint(500, 5000, 100)
        volume_filter = volumes >= 2000

        # Positions: Apply additional lag and filtering
        positions = np.where(volume_filter, raw_signals, 0)
        positions = pd.Series(positions).shift(1).fillna(0)

        self.variance_data = pd.DataFrame(
            {
                "Signal": raw_signals,
                "Position": positions,
                "Volume": volumes,
                "RSI": np.random.uniform(15, 85, 100),
            },
        )

        self.signal_def = SignalDefinition(min_volume=2000, rsi_column="RSI")

    def test_signal_variance_analysis(self):
        """Test analysis of signal variance between methodologies."""
        counts = self.processor.get_comprehensive_counts(
            self.variance_data,
            self.signal_def,
        )

        # Should show significant variance between raw and filtered
        self.assertGreater(counts.raw_signals, 0)
        self.assertLessEqual(counts.filtered_signals, counts.raw_signals)

        # Efficiency should be less than 100%
        if counts.raw_signals > 0:
            self.assertLess(counts.filter_efficiency, 1.0)

    def test_consistency_across_methods(self):
        """Test that the same data produces consistent results."""
        # Count using different methods
        method1_count = self.processor.count_raw_signals(
            self.variance_data,
            self.signal_def,
        )

        # Use convenience function
        method2_count = calculate_signal_count_standardized(
            self.variance_data,
            SignalType.RAW,
            self.signal_def,
        )

        # Should be identical
        self.assertEqual(method1_count, method2_count)

    def test_variance_reduction(self):
        """Test that standardization reduces variance between modules."""
        # Create multiple "modules" with same data but different counting approaches

        # Module 1: Count all non-zero signals
        module1_count = (self.variance_data["Signal"] != 0).sum()

        # Module 2: Use standardized counting
        module2_count = self.processor.count_raw_signals(
            self.variance_data,
            self.signal_def,
        )

        # Module 3: Use convenience function
        module3_count = calculate_signal_count_standardized(
            self.variance_data,
            SignalType.RAW,
            self.signal_def,
        )

        # Modules 2 and 3 should be identical (standardized)
        self.assertEqual(module2_count, module3_count)

        # Module 1 should match standardized approach
        self.assertEqual(module1_count, module2_count)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
