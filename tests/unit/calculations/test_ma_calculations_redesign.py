#!/usr/bin/env python3
"""
Redesigned MA Calculations Unit Tests

Focus: Test pure calculation logic with realistic data
Principles: Behavior-driven, fast execution, isolated
"""

import unittest
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd
import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from tests.fixtures.market_data import create_realistic_price_data
from tests.utils.assertions import assert_ma_calculations_accurate, assert_signals_valid


class TestMACalculationsBehavior(unittest.TestCase):
    """Test MA calculation behavior with realistic market data."""

    def setUp(self):
        """Set up realistic test data that passes validation."""
        self.price_data = create_realistic_price_data(
            ticker="AAPL", days=100, start_price=150.0, volatility=0.02
        )

        self.config = {
            "TICKER": "AAPL",
            "STRATEGY_TYPE": "SMA",
            "BASE_DIR": "/tmp/test",
            "USE_CURRENT": False,
        }

        # Mock logger for testing
        self.log_messages = []
        self.log = lambda msg, level="info": self.log_messages.append(f"{level}: {msg}")

    def test_sma_calculation_accuracy(self):
        """Test SMA calculation produces mathematically correct results."""
        short_window, long_window = 10, 20

        result = calculate_ma_and_signals(
            self.price_data, short_window, long_window, self.config, self.log
        )

        # Verify SMA calculations are mathematically correct
        assert_ma_calculations_accurate(
            result, self.price_data, short_window, long_window, "SMA"
        )

        # Verify required columns exist
        required_columns = [
            "Date",
            "Close",
            "SMA_Short",
            "SMA_Long",
            "Signal",
            "Position",
        ]
        for col in required_columns:
            self.assertIn(col, result.columns, f"Missing required column: {col}")

    def test_ema_calculation_accuracy(self):
        """Test EMA calculation produces mathematically correct results."""
        self.config["STRATEGY_TYPE"] = "EMA"
        short_window, long_window = 12, 26

        result = calculate_ma_and_signals(
            self.price_data, short_window, long_window, self.config, self.log
        )

        # Verify EMA calculations use correct smoothing
        assert_ma_calculations_accurate(
            result, self.price_data, short_window, long_window, "EMA"
        )

    def test_signal_generation_logic(self):
        """Test buy/sell signal generation at crossover points."""
        short_window, long_window = 5, 15

        result = calculate_ma_and_signals(
            self.price_data, short_window, long_window, self.config, self.log
        )

        # Verify signal logic is correct
        assert_signals_valid(result)

        # Test specific signal conditions
        for i in range(1, len(result)):
            prev_row = result.iloc[i - 1]
            curr_row = result.iloc[i]

            # Buy signal: short MA crosses above long MA
            if curr_row["Signal"] == 1:  # Buy signal
                self.assertGreater(
                    curr_row["SMA_Short"],
                    curr_row["SMA_Long"],
                    "Buy signal should occur when short MA > long MA",
                )
                self.assertLessEqual(
                    prev_row["SMA_Short"],
                    prev_row["SMA_Long"],
                    "Buy signal should occur at crossover point",
                )

    def test_edge_cases(self):
        """Test handling of edge cases and invalid inputs."""
        # Test with insufficient data
        short_data = self.price_data.head(5)

        with self.assertRaises(ValueError, msg="Should reject insufficient data"):
            calculate_ma_and_signals(short_data, 10, 20, self.config, self.log)

        # Test with invalid windows
        with self.assertRaises(ValueError, msg="Should reject invalid window sizes"):
            calculate_ma_and_signals(
                self.price_data, 20, 10, self.config, self.log
            )  # short > long

    def test_current_signal_detection(self):
        """Test USE_CURRENT flag correctly identifies current signals."""
        self.config["USE_CURRENT"] = True

        result = calculate_ma_and_signals(
            self.price_data, 10, 20, self.config, self.log
        )

        # Verify last row has current signal information
        last_row = result.iloc[-1]
        self.assertIn("Signal Entry", result.columns)
        self.assertIn("Signal Exit", result.columns)

        # Signal Entry should be boolean
        self.assertIsInstance(last_row["Signal Entry"], (bool, int))


class TestMACalculationsIntegration(unittest.TestCase):
    """Integration tests for MA calculations with real data patterns."""

    def test_trending_market_signals(self):
        """Test signal accuracy in trending market conditions."""
        # Create uptrending market data
        trending_data = create_realistic_price_data(
            ticker="TSLA", days=50, start_price=100.0, trend=0.001  # Slight uptrend
        )

        config = {"TICKER": "TSLA", "STRATEGY_TYPE": "SMA", "USE_CURRENT": False}
        log = lambda msg, level="info": None

        result = calculate_ma_and_signals(trending_data, 10, 20, config, log)

        # In trending market, should have clear signals
        signals = result[result["Signal"] != 0]
        self.assertGreater(
            len(signals), 0, "Should generate signals in trending market"
        )

    def test_sideways_market_signals(self):
        """Test signal behavior in sideways/choppy market conditions."""
        # Create sideways market data
        sideways_data = create_realistic_price_data(
            ticker="SPY",
            days=50,
            start_price=400.0,
            trend=0.0,  # No trend
            volatility=0.015,
        )

        config = {"TICKER": "SPY", "STRATEGY_TYPE": "EMA", "USE_CURRENT": False}
        log = lambda msg, level="info": None

        result = calculate_ma_and_signals(sideways_data, 12, 26, config, log)

        # Should handle sideways market without errors
        self.assertGreater(len(result), 0)
        assert_signals_valid(result)


if __name__ == "__main__":
    unittest.main()
