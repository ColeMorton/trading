"""
Tests for the stop loss simulator module.
"""

import unittest
import numpy as np
from app.tools.stop_loss_simulator import (
    apply_stop_loss_to_returns,
    calculate_stop_loss_adjusted_metrics,
    compare_stop_loss_levels,
    find_optimal_stop_loss,
    apply_stop_loss_to_signal_quality_metrics
)


class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def __call__(self, message, level="info"):
        self.logs.append((message, level))


class TestStopLossSimulator(unittest.TestCase):
    """Test cases for the stop loss simulator module."""
    
    def setUp(self):
        """Set up test data."""
        # Create mock logger
        self.log = MockLogger()
        
        # Create test data
        # Returns sequence with a significant drawdown to trigger stop loss
        self.returns = np.array([0.01, 0.02, -0.01, -0.06, 0.02, 0.01, -0.02, -0.07, 0.03, 0.02])
        
        # Signal sequence (1 for long, -1 for short, 0 for no position)
        self.signals = np.array([0, 1, 1, 1, 1, 0, -1, -1, -1, 0])
    
    def test_apply_stop_loss_to_returns(self):
        """Test applying stop loss to returns."""
        # Apply a 3% stop loss (smaller value to ensure it gets triggered)
        adjusted_returns, triggers = apply_stop_loss_to_returns(
            self.returns, self.signals, 0.03, self.log
        )
        
        # Verify that returns are adjusted
        self.assertNotEqual(np.sum(self.returns), np.sum(adjusted_returns))
        
        # Verify that stop loss is triggered at least once
        self.assertGreater(np.sum(triggers), 0)
        
        # Verify that adjusted returns are different at trigger points
        trigger_indices = np.where(triggers == 1)[0]
        for idx in trigger_indices:
            self.assertNotEqual(self.returns[idx], adjusted_returns[idx])
    
    def test_calculate_stop_loss_adjusted_metrics(self):
        """Test calculating stop loss adjusted metrics."""
        # Calculate metrics with a 3% stop loss
        metrics = calculate_stop_loss_adjusted_metrics(
            self.returns, self.signals, 0.03, self.log
        )
        
        # Verify that metrics are calculated
        self.assertIn("raw_avg_return", metrics)
        self.assertIn("adjusted_avg_return", metrics)
        self.assertIn("stop_loss_count", metrics)
        
        # Verify that raw and adjusted metrics are different
        self.assertNotEqual(metrics["raw_avg_return"], metrics["adjusted_avg_return"])
        
        # Verify that impact metrics are calculated
        self.assertIn("return_impact", metrics)
        self.assertIn("win_rate_impact", metrics)
    
    def test_compare_stop_loss_levels(self):
        """Test comparing different stop loss levels."""
        # Compare multiple stop loss levels
        stop_loss_levels = [0.02, 0.03, 0.05]
        results = compare_stop_loss_levels(
            self.returns, self.signals, stop_loss_levels, self.log
        )
        
        # Verify that results are calculated for each level
        self.assertIn("stop_loss_2pct", results)
        self.assertIn("stop_loss_3pct", results)
        self.assertIn("stop_loss_5pct", results)
        self.assertIn("no_stop_loss", results)
        
        # Verify that metrics are different across levels
        self.assertNotEqual(
            results["stop_loss_2pct"]["adjusted_avg_return"],
            results["stop_loss_3pct"]["adjusted_avg_return"]
        )
    
    def test_find_optimal_stop_loss(self):
        """Test finding the optimal stop loss level."""
        # Find optimal stop loss
        result = find_optimal_stop_loss(
            self.returns, self.signals, (0.02, 0.05), 0.01, "adjusted_avg_return", self.log
        )
        
        # Verify that optimal stop loss is found
        self.assertIn("optimal_stop_loss", result)
        self.assertIsNotNone(result["optimal_stop_loss"])
        
        # Verify that optimal metrics are calculated
        self.assertIn("optimal_metrics", result)
        self.assertIn("adjusted_avg_return", result["optimal_metrics"])
        
        # Verify that all results are included
        self.assertIn("all_results", result)
        self.assertGreater(len(result["all_results"]), 0)
    
    def test_apply_stop_loss_to_signal_quality_metrics(self):
        """Test applying stop loss to signal quality metrics."""
        # Create mock signal quality metrics
        metrics = {
            "signal_count": 5,
            "avg_return": 0.02,
            "win_rate": 0.6,
            "profit_factor": 1.5,
            "avg_win": 0.03,
            "avg_loss": -0.02,
            "risk_reward_ratio": 1.5,
            "max_drawdown": 0.05
        }
        
        # Apply stop loss to metrics
        updated_metrics = apply_stop_loss_to_signal_quality_metrics(
            metrics, self.returns, self.signals, 0.03, self.log
        )
        
        # Verify that metrics are updated
        self.assertIn("avg_return", updated_metrics)
        self.assertIn("win_rate", updated_metrics)
        self.assertIn("profit_factor", updated_metrics)
        
        # Verify that stop loss metrics are added
        self.assertIn("stop_loss", updated_metrics)
        self.assertIn("stop_loss_count", updated_metrics)
        self.assertIn("stop_loss_rate", updated_metrics)
        
        # Verify that raw vs. adjusted comparison is added
        self.assertIn("raw_vs_adjusted", updated_metrics)
        self.assertIn("avg_return", updated_metrics["raw_vs_adjusted"])
        self.assertIn("win_rate", updated_metrics["raw_vs_adjusted"])
    
    def test_invalid_stop_loss(self):
        """Test behavior with invalid stop loss values."""
        # Test with negative stop loss
        adjusted_returns, triggers = apply_stop_loss_to_returns(
            self.returns, self.signals, -0.05, self.log
        )
        
        # Verify that returns are not adjusted
        np.testing.assert_array_equal(self.returns, adjusted_returns)
        
        # Test with stop loss > 1
        adjusted_returns, triggers = apply_stop_loss_to_returns(
            self.returns, self.signals, 1.5, self.log
        )
        
        # Verify that returns are not adjusted
        np.testing.assert_array_equal(self.returns, adjusted_returns)
    
    def test_empty_data(self):
        """Test behavior with empty data."""
        # Create empty arrays
        empty_returns = np.array([])
        empty_signals = np.array([])
        
        # Apply stop loss to empty data
        adjusted_returns, triggers = apply_stop_loss_to_returns(
            empty_returns, empty_signals, 0.05, self.log
        )
        
        # Verify that empty arrays are returned
        self.assertEqual(len(adjusted_returns), 0)
        self.assertEqual(len(triggers), 0)
        
        # Calculate metrics with empty data
        metrics = calculate_stop_loss_adjusted_metrics(
            empty_returns, empty_signals, 0.05, self.log
        )
        
        # Verify that metrics are calculated with default values
        self.assertIn("raw_avg_return", metrics)
        self.assertIn("adjusted_avg_return", metrics)


if __name__ == "__main__":
    unittest.main()