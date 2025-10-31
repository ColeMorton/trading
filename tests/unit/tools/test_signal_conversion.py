"""
Tests for the signal conversion module.
"""

import unittest

import pandas as pd
import polars as pl
import pytest

from app.tools.signal_conversion import convert_signals_to_positions


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.logs = []

    def __call__(self, message, level="info"):
        self.logs.append((message, level))


@pytest.mark.unit
class TestSignalConversion(unittest.TestCase):
    """Test cases for signal conversion functions."""

    def test_convert_signals_to_positions_pandas(self):
        """Test converting signals to positions with pandas DataFrame."""
        # Create test data
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "Date": dates,
                "Signal": [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
                "RSI": [50, 75, 50, 25, 50, 65, 50, 50, 35, 50],
            },
        )

        # Create config and logger
        config = {"STRATEGY_TYPE": "MA Cross", "DIRECTION": "Long", "USE_RSI": False}
        log = MockLogger()

        # Convert signals to positions
        result = convert_signals_to_positions(data, config, log)

        # Verify positions
        expected_positions = [0, 0, 1, 0, -1, 0, 1, 0, 0, -1]
        self.assertEqual(result["Position"].tolist(), expected_positions)

    def test_convert_signals_to_positions_polars(self):
        """Test converting signals to positions with polars DataFrame."""
        # Create test data
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        data_pd = pd.DataFrame(
            {
                "Date": dates,
                "Signal": [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
                "RSI": [50, 75, 50, 25, 50, 65, 50, 50, 35, 50],
            },
        )
        data = pl.from_pandas(data_pd)

        # Create config and logger
        config = {"STRATEGY_TYPE": "MA Cross", "DIRECTION": "Long", "USE_RSI": False}
        log = MockLogger()

        # Convert signals to positions
        result = convert_signals_to_positions(data, config, log)

        # Verify positions
        expected_positions = [0, 0, 1, 0, -1, 0, 1, 0, 0, -1]
        self.assertEqual(result["Position"].to_list(), expected_positions)

    def test_rsi_filter(self):
        """Test RSI filtering of signals."""
        # Create test data
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "Date": dates,
                "Signal": [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
                "RSI": [50, 65, 50, 25, 50, 65, 50, 50, 35, 50],
            },
        )

        # Create config with RSI filter
        config = {
            "STRATEGY_TYPE": "MA Cross",
            "DIRECTION": "Long",
            "USE_RSI": True,
            "RSI_THRESHOLD": 70,  # Should filter out all signals since all RSI values are below 70
        }
        log = MockLogger()

        # Convert signals to positions
        result = convert_signals_to_positions(data, config, log)

        # Verify positions (all signals should be filtered out)
        expected_positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(result["Position"].tolist(), expected_positions)


if __name__ == "__main__":
    unittest.main()
