"""
Tests for the horizon analysis methodology.
"""

import unittest

import numpy as np

from app.concurrency.tools.signal_quality import (
    _calculate_horizon_metrics,
    _find_best_horizon,
)


class TestHorizonAnalysis(unittest.TestCase):
    """Test cases for the horizon analysis methodology."""

    def test_no_forward_looking_bias(self):
        """Test that the horizon analysis doesn't use future data."""
        # Create test data
        # Signals at t=1 and t=5
        signals = np.array([0, 1, 0, 0, 0, -1, 0, 0, 0, 0])

        # Returns pattern: first signal followed by positive returns,
        # second signal followed by negative returns
        returns = np.array(
            [0.01, 0.01, 0.02, 0.03, 0.01, -0.01, -0.02, -0.03, -0.01, 0.01]
        )

        # Calculate horizon metrics
        horizon_metrics = _calculate_horizon_metrics(signals, returns)

        # Check that horizons were calculated correctly
        self.assertIn("1", horizon_metrics)
        self.assertIn("3", horizon_metrics)
        self.assertIn("5", horizon_metrics)

        # For horizon 1, we should have 2 positions (from the 2 signals)
        self.assertEqual(horizon_metrics["1"]["sample_size"], 2)

        # Check that positions are correctly shifted from signals
        # Signal at t=1 creates position at t=2, which sees return[2] = 0.02
        # Signal at t=5 creates position at t=6, which sees return[6] = -0.02
        # For long position (signal=1), we want positive returns
        # For short position (signal=-1), we want negative returns
        # So both positions should be profitable for horizon 1
        self.assertAlmostEqual(horizon_metrics["1"]["win_rate"], 1.0)

        # For horizon 3, check the returns calculation
        # Position at t=2 sees returns[2:5] = [0.02, 0.03, 0.01] = 0.06
        # Position at t=6 sees returns[6:9] = [-0.02, -0.03, -0.01] = -0.06
        # For short position, we negate the returns, so it's 0.06
        # Both should be profitable
        self.assertAlmostEqual(horizon_metrics["3"]["win_rate"], 1.0)

    def test_position_based_evaluation(self):
        """Test that horizon analysis evaluates positions, not signals."""
        # Create test data with signals and corresponding positions
        signals = np.array([0, 1, 0, 0, 1, 0, 0, -1, 0, 0])

        # Expected positions (shifted by 1)
        expected_positions = np.array([0, 0, 1, 0, 0, 1, 0, 0, -1, 0])

        # Returns that would make some positions profitable and others not
        returns = np.array(
            [0.01, 0.01, -0.02, 0.03, 0.01, 0.02, -0.02, -0.03, 0.01, 0.01]
        )

        # Calculate horizon metrics
        horizon_metrics = _calculate_horizon_metrics(signals, returns)

        # For horizon 1, we should have 3 positions
        self.assertEqual(horizon_metrics["1"]["sample_size"], 3)

        # Check win rate for horizon 1
        # Position at t=2 sees return[2] = -0.02 (loss for long)
        # Position at t=5 sees return[5] = 0.02 (win for long)
        # Position at t=8 sees return[8] = 0.01 (loss for short)
        # Win rate should be 1/3
        self.assertAlmostEqual(horizon_metrics["1"]["win_rate"], 1 / 3)

    def test_find_best_horizon(self):
        """Test the best horizon selection logic."""
        # Create test horizon metrics
        horizon_metrics = {
            "1": {"sharpe": 0.5, "win_rate": 0.55, "sample_size": 100},
            "3": {"sharpe": 1.2, "win_rate": 0.60, "sample_size": 80},
            "5": {"sharpe": 1.5, "win_rate": 0.65, "sample_size": 15},  # Small sample
            "10": {"sharpe": 0.8, "win_rate": 0.58, "sample_size": 50},
        }

        # Find best horizon with default min_sample_size (20)
        best_horizon = _find_best_horizon(horizon_metrics)

        # Horizon 5 has best metrics but small sample, so horizon 3 should be selected
        self.assertEqual(best_horizon, 3)

        # Test with lower min_sample_size
        best_horizon_low_threshold = _find_best_horizon(
            horizon_metrics, min_sample_size=10
        )

        # Now horizon 5 should be selected
        self.assertEqual(best_horizon_low_threshold, 5)

    def test_empty_data(self):
        """Test behavior with empty data."""
        signals = np.array([])
        returns = np.array([])

        # Calculate horizon metrics
        horizon_metrics = _calculate_horizon_metrics(signals, returns)

        # Should return empty dict
        self.assertEqual(horizon_metrics, {})

        # Find best horizon should return None
        best_horizon = _find_best_horizon(horizon_metrics)
        self.assertIsNone(best_horizon)

    def test_no_signals(self):
        """Test behavior with no signals."""
        signals = np.zeros(10)
        returns = np.random.randn(10) * 0.01

        # Calculate horizon metrics
        horizon_metrics = _calculate_horizon_metrics(signals, returns)

        # Should return empty dict (no positions)
        self.assertEqual(horizon_metrics, {})


if __name__ == "__main__":
    unittest.main()
