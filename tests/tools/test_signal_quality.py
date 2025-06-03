"""
Tests for the signal quality metrics module.
"""

import unittest

import numpy as np
import polars as pl

from app.concurrency.tools.signal_quality import (
    _calculate_horizon_metrics,
    _calculate_quality_score,
    _calculate_signal_conviction,
    _calculate_signal_opportunity_cost,
    _calculate_signal_reliability_index,
    _calculate_signal_timing_efficiency,
    _calculate_signal_value_ratio,
    _find_best_horizon,
    calculate_signal_quality_metrics,
)


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.logs = []

    def __call__(self, message, level="info"):
        self.logs.append((message, level))


class TestSignalQualityMetrics(unittest.TestCase):
    """Test cases for the signal quality metrics module."""

    def test_calculate_signal_quality_metrics(self):
        """Test the main signal quality metrics calculation function."""
        # Create test data
        dates = [f"2023-01-{i+1:02d}" for i in range(10)]
        signals = [0, 1, 0, -1, 0, 1, 0, 0, -1, 0]
        returns = [0.01, 0.01, 0.02, -0.02, 0.01, 0.02, -0.02, 0.01, -0.01, 0.01]

        # Create DataFrames
        signals_df = pl.DataFrame({"Date": dates, "signal": signals})

        returns_df = pl.DataFrame({"Date": dates, "return": returns})

        # Calculate metrics
        log = MockLogger()
        metrics = calculate_signal_quality_metrics(
            signals_df, returns_df, "test_strategy", log
        )

        # Verify basic metrics
        self.assertIn("signal_count", metrics)
        self.assertEqual(metrics["signal_count"], 4)  # 4 non-zero signals

        self.assertIn("win_rate", metrics)
        self.assertIn("avg_return", metrics)
        self.assertIn("profit_factor", metrics)

        # Verify advanced metrics
        self.assertIn("signal_value_ratio", metrics)
        self.assertIn("signal_conviction", metrics)
        self.assertIn("signal_timing_efficiency", metrics)
        self.assertIn("signal_opportunity_cost", metrics)
        self.assertIn("signal_reliability", metrics)

        # Verify horizon metrics
        self.assertIn("horizon_metrics", metrics)
        self.assertIn("best_horizon", metrics)

    def test_horizon_metrics_integration(self):
        """Test that horizon metrics are correctly integrated with signal quality metrics."""
        # Create test data
        dates = [f"2023-01-{i+1:02d}" for i in range(20)]
        signals = [0] * 20
        signals[1] = 1  # Signal at t=1
        signals[5] = -1  # Signal at t=5
        signals[10] = 1  # Signal at t=10
        signals[15] = -1  # Signal at t=15

        returns = [0.01] * 20

        # Create DataFrames
        signals_df = pl.DataFrame({"Date": dates, "signal": signals})

        returns_df = pl.DataFrame({"Date": dates, "return": returns})

        # Calculate metrics
        log = MockLogger()
        metrics = calculate_signal_quality_metrics(
            signals_df, returns_df, "test_strategy", log
        )

        # Verify horizon metrics
        self.assertIn("horizon_metrics", metrics)
        horizon_metrics = metrics["horizon_metrics"]

        # Check that horizons were calculated
        for horizon in ["1", "3", "5", "10"]:
            if horizon in horizon_metrics:
                self.assertIn("win_rate", horizon_metrics[horizon])
                self.assertIn("avg_return", horizon_metrics[horizon])
                self.assertIn("sharpe", horizon_metrics[horizon])
                self.assertIn("sample_size", horizon_metrics[horizon])

    def test_empty_data(self):
        """Test behavior with empty data."""
        # Create empty DataFrames
        signals_df = pl.DataFrame({"Date": [], "signal": []})

        returns_df = pl.DataFrame({"Date": [], "return": []})

        # Calculate metrics
        log = MockLogger()
        metrics = calculate_signal_quality_metrics(
            signals_df, returns_df, "test_strategy", log
        )

        # Should return minimal metrics
        self.assertIn("signal_count", metrics)
        self.assertEqual(metrics["signal_count"], 0)
        self.assertIn("signal_quality_score", metrics)
        self.assertEqual(metrics["signal_quality_score"], 0.0)

    def test_no_signals(self):
        """Test behavior with no signals."""
        # Create test data with no signals
        dates = [f"2023-01-{i+1:02d}" for i in range(10)]
        signals = [0] * 10
        returns = [0.01] * 10

        # Create DataFrames
        signals_df = pl.DataFrame({"Date": dates, "signal": signals})

        returns_df = pl.DataFrame({"Date": dates, "return": returns})

        # Calculate metrics
        log = MockLogger()
        metrics = calculate_signal_quality_metrics(
            signals_df, returns_df, "test_strategy", log
        )

        # Should return basic metrics with signal_count = 0
        self.assertIn("signal_count", metrics)
        self.assertEqual(metrics["signal_count"], 0)
        self.assertIn("signal_quality_score", metrics)
        self.assertEqual(metrics["signal_quality_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
