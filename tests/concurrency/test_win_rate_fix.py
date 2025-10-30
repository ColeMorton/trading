#!/usr/bin/env python3
"""
Comprehensive test suite for win rate calculation fixes.

Tests the standardized win rate calculator to ensure:
1. Signal-based vs trade-based calculations are consistent
2. Zero return handling is correct
3. Edge cases are handled properly
4. Legacy compatibility is maintained
"""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pytest

from app.concurrency.tools.win_rate_calculator import (
    WinRateCalculator,
    WinRateComponents,
    WinRateType,
    calculate_win_rate_standardized,
)


class TestWinRateCalculator(unittest.TestCase):
    """Test cases for the WinRateCalculator class."""

    def setUp(self):
        """Set up test data."""
        self.calc = WinRateCalculator(use_fixed=True)

        # Test data: 60% win rate scenario
        self.test_returns = np.array(
            [0.02, -0.01, 0.015, 0.025, -0.005, 0.01, -0.02, 0.03, 0.005, -0.01],
        )
        self.test_signals = np.array([1, 1, -1, 1, -1, 1, 1, -1, 1, -1])

        # Zero returns scenario
        self.returns_with_zeros = np.array(
            [0.02, 0.0, 0.015, 0.0, -0.005, 0.01, -0.02, 0.0, 0.005, -0.01],
        )
        self.signals_with_zeros = np.array([1, 0, -1, 0, -1, 1, 1, 0, 1, -1])

    def test_trade_win_rate_basic(self):
        """Test basic trade win rate calculation."""
        result = self.calc.calculate_trade_win_rate(self.test_returns)

        # Expected: 6 wins out of 10 trades = 60%
        self.assertEqual(result.wins, 6)
        self.assertEqual(result.losses, 4)
        self.assertEqual(result.total, 10)
        self.assertAlmostEqual(result.win_rate, 0.6, places=3)
        self.assertEqual(result.calculation_type, "trade")

    def test_signal_win_rate_basic(self):
        """Test basic signal win rate calculation."""
        result = self.calc.calculate_signal_win_rate(
            self.test_returns,
            self.test_signals,
        )

        # All signals are active (no zeros), so should match trade calculation
        self.assertEqual(result.wins, 6)
        self.assertEqual(result.losses, 4)
        self.assertEqual(result.total, 10)
        self.assertAlmostEqual(result.win_rate, 0.6, places=3)
        self.assertEqual(result.calculation_type, "signal")

    def test_zero_returns_excluded(self):
        """Test zero returns are properly excluded."""
        result = self.calc.calculate_trade_win_rate(
            self.returns_with_zeros,
            include_zeros=False,
        )

        # 3 zeros should be excluded, leaving 7 non-zero returns (4 wins, 3 losses)
        self.assertEqual(result.wins, 4)
        self.assertEqual(result.losses, 3)
        self.assertEqual(result.total, 7)
        self.assertEqual(result.zero_returns, 3)
        self.assertAlmostEqual(result.win_rate, 4 / 7, places=3)

    def test_zero_returns_included(self):
        """Test zero returns are properly included."""
        result = self.calc.calculate_trade_win_rate(
            self.returns_with_zeros,
            include_zeros=True,
        )

        # When including zeros: zeros don't count as wins or losses for win rate calculation
        # but they're tracked separately. Win rate = wins / (wins + losses)
        # Returns: [0.02, 0.0, 0.015, 0.0, -0.005, 0.01, -0.02, 0.0, 0.005, -0.01]
        # Wins: 4 (positive returns)
        # Losses: 3 (negative returns)
        # Zeros: 3 (zero returns - tracked but not included in win rate denominator)
        self.assertEqual(result.wins, 4)
        self.assertEqual(result.losses, 3)  # Only negative returns
        self.assertEqual(
            result.total,
            7,
        )  # wins + losses (zeros excluded from denominator)
        self.assertEqual(result.zero_returns, 3)
        self.assertAlmostEqual(result.win_rate, 4 / 7, places=3)

    def test_signal_filtering(self):
        """Test signal-based calculation filters inactive periods."""
        result = self.calc.calculate_signal_win_rate(
            self.returns_with_zeros,
            self.signals_with_zeros,
            include_zeros=False,
        )

        # Only periods with signals ±1: indices 0,2,4,5,6,8,9 = 7 periods
        # Returns: [0.02, 0.015, -0.005, 0.01, -0.02, 0.005, -0.01]
        # Wins: [0.02, 0.015, 0.01, 0.005] = 4 wins
        # Losses: [-0.005, -0.02, -0.01] = 3 losses
        self.assertEqual(result.wins, 4)
        self.assertEqual(result.losses, 3)
        self.assertEqual(result.total, 7)
        self.assertAlmostEqual(result.win_rate, 4 / 7, places=3)

    def test_all_wins_scenario(self):
        """Test scenario with all winning trades."""
        all_wins = np.array([0.01, 0.02, 0.015, 0.03, 0.005])
        result = self.calc.calculate_trade_win_rate(all_wins)

        self.assertEqual(result.wins, 5)
        self.assertEqual(result.losses, 0)
        self.assertEqual(result.total, 5)
        self.assertEqual(result.win_rate, 1.0)

    def test_all_losses_scenario(self):
        """Test scenario with all losing trades."""
        all_losses = np.array([-0.01, -0.02, -0.015, -0.03, -0.005])
        result = self.calc.calculate_trade_win_rate(all_losses)

        self.assertEqual(result.wins, 0)
        self.assertEqual(result.losses, 5)
        self.assertEqual(result.total, 5)
        self.assertEqual(result.win_rate, 0.0)

    def test_empty_array(self):
        """Test handling of empty arrays."""
        empty_returns = np.array([])
        result = self.calc.calculate_trade_win_rate(empty_returns)

        self.assertEqual(result.wins, 0)
        self.assertEqual(result.losses, 0)
        self.assertEqual(result.total, 0)
        self.assertEqual(result.win_rate, 0.0)

    def test_weighted_win_rate(self):
        """Test weighted win rate calculation."""
        weights = np.array([0.1, 0.2, 0.15, 0.25, 0.05, 0.1, 0.2, 0.3, 0.05, 0.1])
        result = self.calc.calculate_weighted_win_rate(self.test_returns, weights)

        # Should calculate win rate based on weighted returns
        self.assertEqual(result.calculation_type, "weighted")
        self.assertIsInstance(result.win_rate, float)
        self.assertTrue(0.0 <= result.win_rate <= 1.0)

    def test_compare_calculations(self):
        """Test comparison of different calculation methods."""
        comparisons = self.calc.compare_calculations(
            self.test_returns,
            self.test_signals,
        )

        # Should have multiple calculation types
        self.assertIn("trade_standard", comparisons)
        self.assertIn("trade_with_zeros", comparisons)
        self.assertIn("signal_standard", comparisons)
        self.assertIn("signal_with_zeros", comparisons)
        self.assertIn("legacy", comparisons)

        # All should be WinRateComponents
        for result in comparisons.values():
            self.assertIsInstance(result, WinRateComponents)

    def test_legacy_compatibility(self):
        """Test legacy calculation for backward compatibility."""
        legacy_rate = self.calc.calculate_legacy_win_rate(self.test_returns)

        # Legacy includes all returns, including zeros as losses
        expected = 6 / 10  # 6 positive out of 10 total
        self.assertAlmostEqual(legacy_rate, expected, places=3)

    def test_validation(self):
        """Test win rate validation."""
        self.assertTrue(self.calc.validate_win_rate(0.0))
        self.assertTrue(self.calc.validate_win_rate(0.5))
        self.assertTrue(self.calc.validate_win_rate(1.0))
        self.assertFalse(self.calc.validate_win_rate(-0.1))
        self.assertFalse(self.calc.validate_win_rate(1.1))

    def test_array_length_mismatch(self):
        """Test error handling for mismatched array lengths."""
        short_signals = np.array([1, -1, 1])

        with pytest.raises(ValueError):
            self.calc.calculate_signal_win_rate(self.test_returns, short_signals)

        with pytest.raises(ValueError):
            self.calc.calculate_weighted_win_rate(self.test_returns, short_signals)

    def test_dataframe_integration(self):
        """Test DataFrame integration."""
        df = pd.DataFrame(
            {
                "returns": self.test_returns,
                "signal": self.test_signals,
                "weight": np.ones(len(self.test_returns)) * 0.1,
            },
        )

        # Test trade method
        result_trade = self.calc.calculate_from_dataframe(df, method=WinRateType.TRADE)
        self.assertEqual(result_trade.calculation_type, "trade")

        # Test signal method
        result_signal = self.calc.calculate_from_dataframe(
            df,
            method=WinRateType.SIGNAL,
        )
        self.assertEqual(result_signal.calculation_type, "signal")

        # Test weighted method
        result_weighted = self.calc.calculate_from_dataframe(
            df,
            method=WinRateType.WEIGHTED,
            weight_col="weight",
        )
        self.assertEqual(result_weighted.calculation_type, "weighted")

    def test_convenience_function(self):
        """Test the convenience function."""
        # Trade method
        win_rate_trade = calculate_win_rate_standardized(
            self.test_returns,
            method="trade",
        )
        self.assertAlmostEqual(win_rate_trade, 0.6, places=3)

        # Signal method
        win_rate_signal = calculate_win_rate_standardized(
            self.test_returns,
            method="signal",
            signals=self.test_signals,
        )
        self.assertAlmostEqual(win_rate_signal, 0.6, places=3)

        # Legacy method
        win_rate_legacy = calculate_win_rate_standardized(
            self.test_returns,
            method="legacy",
        )
        self.assertAlmostEqual(win_rate_legacy, 0.6, places=3)


class TestWinRateDiscrepancyFix(unittest.TestCase):
    """Test cases specifically for the 18.8% discrepancy fix."""

    def setUp(self):
        """Set up test data that demonstrates the discrepancy."""
        self.calc = WinRateCalculator(use_fixed=True)

        # Scenario that would cause discrepancy:
        # Multiple signals within a single trade period
        self.returns_with_multi_signals = np.array(
            [
                0.01,
                0.005,
                -0.002,
                0.003,  # Trade 1: overall win, but some negative signals
                -0.01,
                -0.005,
                0.002,
                -0.003,  # Trade 2: overall loss, but some positive signals
            ],
        )

        # Signals that don't align perfectly with trade boundaries
        self.multi_signals = np.array([1, 1, 1, 0, -1, -1, -1, 0])

    def test_signal_vs_trade_discrepancy(self):
        """Test the discrepancy between signal and trade calculations."""
        # Signal-based calculation (counts individual signal returns)
        signal_result = self.calc.calculate_signal_win_rate(
            self.returns_with_multi_signals,
            self.multi_signals,
            include_zeros=False,
        )

        # Trade-based calculation (counts overall trade returns)
        trade_result = self.calc.calculate_trade_win_rate(
            self.returns_with_multi_signals,
            include_zeros=False,
        )

        # The discrepancy should be minimal with standardized calculation
        discrepancy = abs(signal_result.win_rate - trade_result.win_rate)

        # With proper standardization, discrepancy should be reasonable
        self.assertLess(
            discrepancy,
            0.2,
            f"Win rate discrepancy too high: {discrepancy:.3f}",
        )

    def test_zero_handling_consistency(self):
        """Test that zero handling is consistent across methods."""
        returns_with_zeros = np.array([0.01, 0.0, -0.01, 0.0, 0.02])
        signals = np.array([1, 0, -1, 0, 1])

        # Signal method (should exclude zero-signal periods automatically)
        signal_result = self.calc.calculate_signal_win_rate(returns_with_zeros, signals)

        # Trade method excluding zeros
        trade_result = self.calc.calculate_trade_win_rate(
            returns_with_zeros[signals != 0],
            include_zeros=False,
        )

        # Should be identical when applied to same data
        self.assertEqual(signal_result.wins, trade_result.wins)
        self.assertEqual(signal_result.losses, trade_result.losses)
        self.assertAlmostEqual(signal_result.win_rate, trade_result.win_rate, places=6)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
