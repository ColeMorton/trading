"""
Tests for the expectancy calculation module.
"""

import unittest

import numpy as np
import pandas as pd

from app.tools.expectancy import (
    calculate_expectancy,
    calculate_expectancy_from_returns,
    calculate_expectancy_metrics,
    calculate_expectancy_per_month,
    calculate_expectancy_with_stop_loss,
)


class TestExpectancy(unittest.TestCase):
    """Test cases for expectancy calculation functions."""

    def test_calculate_expectancy(self):
        """Test the basic expectancy calculation formula."""
        # Test case 1: Positive expectancy
        win_rate = 0.6
        avg_win = 0.05
        avg_loss = 0.03
        expected = 0.6 * 0.05 - 0.4 * 0.03
        result = calculate_expectancy(win_rate, avg_win, avg_loss)
        self.assertAlmostEqual(result, expected, places=6)

        # Test case 2: Negative expectancy
        win_rate = 0.4
        avg_win = 0.05
        avg_loss = 0.08
        expected = 0.4 * 0.05 - 0.6 * 0.08
        result = calculate_expectancy(win_rate, avg_win, avg_loss)
        self.assertAlmostEqual(result, expected, places=6)

        # Test case 3: Zero expectancy
        win_rate = 0.5
        avg_win = 0.04
        avg_loss = 0.04
        expected = 0.5 * 0.04 - 0.5 * 0.04
        result = calculate_expectancy(win_rate, avg_win, avg_loss)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_expectancy_from_returns(self):
        """Test expectancy calculation from a series of returns."""
        # Test case 1: Mixed returns
        returns = [0.05, -0.03, 0.04, -0.02, 0.06, -0.04, 0.03]
        expectancy, components = calculate_expectancy_from_returns(returns)

        # Verify components
        self.assertAlmostEqual(components["win_rate"], 4 / 7, places=6)
        self.assertAlmostEqual(components["avg_win"], 0.045, places=6)
        self.assertAlmostEqual(components["avg_loss"], -0.03, places=6)

        # Verify expectancy
        expected = (4 / 7) * 0.045 - (3 / 7) * 0.03
        self.assertAlmostEqual(expectancy, expected, places=6)

        # Test case 2: Empty returns
        returns = []
        expectancy, components = calculate_expectancy_from_returns(returns)
        self.assertEqual(expectancy, 0.0)
        self.assertEqual(components["win_rate"], 0.0)

        # Test case 3: All positive returns
        returns = [0.01, 0.02, 0.03, 0.04]
        expectancy, components = calculate_expectancy_from_returns(returns)
        self.assertAlmostEqual(components["win_rate"], 1.0, places=6)
        self.assertAlmostEqual(components["avg_win"], 0.025, places=6)
        self.assertAlmostEqual(expectancy, 0.025, places=6)

        # Test case 4: All negative returns
        returns = [-0.01, -0.02, -0.03, -0.04]
        expectancy, components = calculate_expectancy_from_returns(returns)
        self.assertAlmostEqual(components["win_rate"], 0.0, places=6)
        self.assertAlmostEqual(components["avg_loss"], -0.025, places=6)
        self.assertAlmostEqual(expectancy, -0.025, places=6)

        # Test case 5: With pandas Series
        returns = pd.Series([0.05, -0.03, 0.04, -0.02])
        expectancy, components = calculate_expectancy_from_returns(returns)
        self.assertAlmostEqual(components["win_rate"], 0.5, places=6)

    def test_calculate_expectancy_with_stop_loss(self):
        """Test expectancy calculation with stop loss applied."""
        # Test case 1: Long position with stop loss
        returns = [0.05, -0.08, 0.04, -0.06, 0.07, -0.03]
        stop_loss = 0.05

        expectancy, components = calculate_expectancy_with_stop_loss(
            returns, stop_loss, "Long"
        )

        # Verify stop loss is applied to large losses
        self.assertEqual(components["loss_count"], 3)
        # Two losses should be capped at -0.05 instead of -0.08 and -0.06
        expected_avg_loss = (-0.05 - 0.05 - 0.03) / 3
        self.assertAlmostEqual(components["avg_loss"], expected_avg_loss, places=6)

        # Test case 2: Short position with stop loss
        returns = [-0.05, 0.08, -0.04, 0.06, -0.07, 0.03]
        stop_loss = 0.05

        expectancy, components = calculate_expectancy_with_stop_loss(
            returns, stop_loss, "Short"
        )

        # Verify stop loss is applied to large losses (positive returns for shorts)
        self.assertEqual(components["loss_count"], 3)
        # Two losses should be capped at -0.05 instead of 0.08 and 0.06
        expected_avg_loss = (-0.05 - 0.05 - 0.03) / 3
        self.assertAlmostEqual(components["avg_loss"], expected_avg_loss, places=6)

    def test_calculate_expectancy_per_month(self):
        """Test monthly expectancy calculation."""
        # Test case 1: Normal calculation
        expectancy_per_trade = 0.02
        trades_per_month = 10
        expected = 0.2
        result = calculate_expectancy_per_month(expectancy_per_trade, trades_per_month)
        self.assertAlmostEqual(result, expected, places=6)

        # Test case 2: Zero trades
        expectancy_per_trade = 0.02
        trades_per_month = 0
        expected = 0.0
        result = calculate_expectancy_per_month(expectancy_per_trade, trades_per_month)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_expectancy_metrics(self):
        """Test comprehensive expectancy metrics calculation."""
        # Test case 1: Basic metrics without stop loss
        returns = [0.05, -0.03, 0.04, -0.02, 0.06, -0.04, 0.03]
        config = {"TRADES_PER_MONTH": 20}

        metrics = calculate_expectancy_metrics(returns, config)

        # Verify basic metrics
        self.assertIn("Expectancy", metrics)
        self.assertIn("Win Rate [%]", metrics)
        self.assertIn("Expectancy per Trade", metrics)
        self.assertIn("Expectancy per Month", metrics)

        # Verify monthly expectancy
        expected_monthly = metrics["Expectancy per Trade"] * 20
        self.assertAlmostEqual(
            metrics["Expectancy per Month"], expected_monthly, places=6
        )

        # Test case 2: With stop loss
        returns = [0.05, -0.08, 0.04, -0.06, 0.07, -0.03]
        config = {"STOP_LOSS": 0.05, "DIRECTION": "Long", "TRADES_PER_MONTH": 15}

        metrics = calculate_expectancy_metrics(returns, config)

        # Verify stop loss metrics
        self.assertIn("Expectancy with Stop Loss", metrics)
        self.assertIn("Win Rate with Stop Loss [%]", metrics)

        # Verify expectancy per trade uses stop loss adjusted value
        self.assertEqual(
            metrics["Expectancy per Trade"], metrics["Expectancy with Stop Loss"]
        )


if __name__ == "__main__":
    unittest.main()
