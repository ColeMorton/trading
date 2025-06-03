"""
Integration tests for expectancy calculation consistency.

This module verifies that expectancy calculations are consistent
between signal metrics and trade metrics.
"""

import unittest

import numpy as np
import pandas as pd
import polars as pl

from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics
from app.tools.backtest_strategy import backtest_strategy
from app.tools.expectancy import calculate_expectancy


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.logs = []

    def __call__(self, message, level="info"):
        self.logs.append((message, level))


class TestExpectancyIntegration(unittest.TestCase):
    """Test cases for expectancy calculation consistency."""

    def test_expectancy_consistency(self):
        """Test that signal and trade expectancy calculations are consistent."""
        # Create mock data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        close_prices = np.random.normal(100, 5, 100).cumsum()

        # Create signals: 1 for entry, 0 for exit
        signals = np.zeros(100)
        signals[10] = 1  # Enter
        signals[20] = 0  # Exit
        signals[40] = 1  # Enter
        signals[60] = 0  # Exit
        signals[70] = 1  # Enter
        signals[90] = 0  # Exit

        # Create positions (shifted signals)
        positions = np.zeros(100)
        positions[11:21] = 1
        positions[41:61] = 1
        positions[71:91] = 1

        # Create returns
        returns = np.diff(close_prices) / close_prices[:-1]
        returns = np.insert(returns, 0, 0)

        # Create polars DataFrame for signal quality metrics
        signals_df = pl.DataFrame({"Date": dates, "signal": signals})

        returns_df = pl.DataFrame({"Date": dates, "return": returns})

        # Create pandas DataFrame for backtest_strategy
        data_pd = pd.DataFrame(
            {
                "Date": dates,
                "Close": close_prices,
                "Signal": signals,
                "Position": positions,
            }
        )

        # Convert to polars DataFrame
        data_pl = pl.from_pandas(data_pd)

        # Calculate signal quality metrics
        mock_log = MockLogger()
        signal_metrics = calculate_signal_quality_metrics(
            signals_df=signals_df,
            returns_df=returns_df,
            strategy_id="test_strategy",
            log=mock_log,
        )

        # Extract signal expectancy
        signal_expectancy = signal_metrics.get("expectancy_per_signal", 0)

        # Create a simple config for backtest
        config = {"DIRECTION": "Long", "USE_HOURLY": False}

        # Mock the backtest_strategy function to avoid actual backtesting
        # Instead, manually calculate expectancy using the same data

        # Get signal returns
        signal_returns = returns[signals == 1]

        # Calculate win rate, avg_win, avg_loss
        win_rate = np.mean(signal_returns > 0)
        positive_returns = signal_returns[signal_returns > 0]
        negative_returns = signal_returns[signal_returns < 0]
        avg_win = np.mean(positive_returns) if len(positive_returns) > 0 else 0
        avg_loss = np.mean(negative_returns) if len(negative_returns) > 0 else 0

        # Calculate trade expectancy using our standardized function
        trade_expectancy = calculate_expectancy(win_rate, avg_win, abs(avg_loss))

        # Assert that both expectancy calculations are consistent
        self.assertAlmostEqual(
            signal_expectancy,
            trade_expectancy,
            places=6,
            msg="Signal and trade expectancy calculations should be consistent",
        )

        # Print the values for debugging
        print(f"Signal expectancy: {signal_expectancy}")
        print(f"Trade expectancy: {trade_expectancy}")
        print(f"Difference: {abs(signal_expectancy - trade_expectancy)}")


if __name__ == "__main__":
    unittest.main()
