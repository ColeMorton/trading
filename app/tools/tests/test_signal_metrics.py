"""
Tests for the standardized signal metrics module.
"""

import unittest
import pandas as pd
import polars as pl
import numpy as np
from datetime import datetime, timedelta
from app.tools.signal_metrics import (
    SignalMetrics,
    calculate_signal_metrics,
    calculate_signal_quality_metrics
)


class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def __call__(self, message, level="info"):
        self.logs.append((message, level))


class TestSignalMetrics(unittest.TestCase):
    """Test cases for the SignalMetrics class."""
    
    def setUp(self):
        """Set up test data."""
        # Create test data
        self.dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        
        # Create signals data
        self.signals_data = pd.DataFrame({
            'Date': self.dates,
            'Signal': [0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, -1, 0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1]
        })
        
        # Create returns data
        self.returns_data = pd.DataFrame({
            'Date': self.dates,
            'return': [0.01, 0.02, 0.01, -0.01, -0.02, -0.01, 0.01, 0.02, 0.01, -0.01, 
                      -0.02, -0.01, 0.01, 0.02, 0.01, -0.01, -0.02, -0.01, 0.01, 0.02,
                      0.01, -0.01, -0.02, -0.01, 0.01, 0.02, 0.01, -0.01, -0.02, -0.01]
        })
        
        # Create logger
        self.log = MockLogger()
        
        # Create SignalMetrics instance
        self.metrics = SignalMetrics(self.log)
    
    def test_calculate_frequency_metrics(self):
        """Test calculating signal frequency metrics."""
        # Calculate frequency metrics
        metrics = self.metrics.calculate_frequency_metrics(self.signals_data)
        
        # Verify metrics
        self.assertIn("mean_signals_per_month", metrics)
        self.assertIn("median_signals_per_month", metrics)
        self.assertIn("signal_volatility", metrics)
        self.assertIn("total_signals", metrics)
        
        # Verify total signals
        self.assertEqual(metrics["total_signals"], 10)  # 10 non-zero signals
    
    def test_calculate_quality_metrics(self):
        """Test calculating signal quality metrics."""
        # Convert signals data to have 'signal' column
        signals_df = self.signals_data.copy()
        signals_df.rename(columns={'Signal': 'signal'}, inplace=True)
        
        # Calculate quality metrics
        metrics = self.metrics.calculate_quality_metrics(
            signals_df,
            self.returns_data,
            "test_strategy"
        )
        
        # Verify metrics
        self.assertIn("signal_count", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("profit_factor", metrics)
        self.assertIn("expectancy_per_signal", metrics)
        self.assertIn("signal_quality_score", metrics)
        self.assertIn("horizon_metrics", metrics)
        self.assertIn("best_horizon", metrics)
        
        # Verify signal count
        self.assertEqual(metrics["signal_count"], 10)  # 10 non-zero signals
    
    def test_calculate_portfolio_metrics(self):
        """Test calculating portfolio-level signal metrics."""
        # Create multiple dataframes
        df1 = self.signals_data.copy()
        df2 = self.signals_data.copy()
        df2['Signal'] = [0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, -1]
        
        # Calculate portfolio metrics
        metrics = self.metrics.calculate_portfolio_metrics(
            [df1, df2],
            ["strategy_1", "strategy_2"]
        )
        
        # Verify metrics
        self.assertIn("strategy_1_total_signals", metrics)
        self.assertIn("strategy_2_total_signals", metrics)
        self.assertIn("portfolio_total_signals", metrics)
        
        # Verify total signals
        self.assertEqual(metrics["strategy_1_total_signals"], 10)  # 10 non-zero signals in df1
        self.assertEqual(metrics["strategy_2_total_signals"], 10)  # 10 non-zero signals in df2
        self.assertEqual(metrics["portfolio_total_signals"], 20)  # 20 total signals
    
    def test_horizon_metrics(self):
        """Test calculating horizon metrics."""
        # Create signals and returns arrays
        signals = np.array([0, 1, 0, 0, -1, 0, 0, 1, 0, 0])
        returns = np.array([0.01, 0.02, 0.01, -0.01, -0.02, -0.01, 0.01, 0.02, 0.01, -0.01])
        
        # Calculate horizon metrics
        horizon_metrics = self.metrics._calculate_horizon_metrics(signals, returns)
        
        # Verify metrics
        self.assertIn("1", horizon_metrics)
        self.assertIn("3", horizon_metrics)
        
        # Verify horizon 1 metrics
        self.assertIn("avg_return", horizon_metrics["1"])
        self.assertIn("win_rate", horizon_metrics["1"])
        self.assertIn("sharpe", horizon_metrics["1"])
        self.assertIn("sample_size", horizon_metrics["1"])
    
    def test_find_best_horizon(self):
        """Test finding the best horizon."""
        # Create horizon metrics
        horizon_metrics = {
            "1": {"sharpe": 0.5, "win_rate": 0.55, "sample_size": 100},
            "3": {"sharpe": 1.2, "win_rate": 0.60, "sample_size": 80},
            "5": {"sharpe": 1.5, "win_rate": 0.65, "sample_size": 15},  # Small sample
            "10": {"sharpe": 0.8, "win_rate": 0.58, "sample_size": 50}
        }
        
        # Find best horizon with default min_sample_size (20)
        best_horizon = self.metrics._find_best_horizon(horizon_metrics)
        
        # Verify best horizon
        self.assertEqual(best_horizon, 3)  # Horizon 3 should be selected
    
    def test_empty_data(self):
        """Test behavior with empty data."""
        # Create empty dataframes
        empty_df = pd.DataFrame({'Date': [], 'Signal': []})
        empty_returns = pd.DataFrame({'Date': [], 'return': []})
        
        # Calculate frequency metrics
        freq_metrics = self.metrics.calculate_frequency_metrics(empty_df)
        
        # Verify metrics
        self.assertEqual(freq_metrics["total_signals"], 0)
        
        # Calculate quality metrics
        empty_df_renamed = empty_df.copy()
        empty_df_renamed.rename(columns={'Signal': 'signal'}, inplace=True)
        
        quality_metrics = self.metrics.calculate_quality_metrics(
            empty_df_renamed,
            empty_returns,
            "test_strategy"
        )
        
        # Verify metrics
        self.assertEqual(quality_metrics["signal_count"], 0)
        self.assertEqual(quality_metrics["signal_quality_score"], 0.0)
    
    def test_legacy_functions(self):
        """Test legacy functions for backward compatibility."""
        # Convert to polars
        signals_pl = pl.from_pandas(self.signals_data)
        returns_pl = pl.from_pandas(self.returns_data)
        
        # Rename Signal to Position for calculate_signal_metrics
        signals_pl = signals_pl.rename({"Signal": "Position"})
        
        # Test calculate_signal_metrics
        metrics = calculate_signal_metrics([signals_pl], self.log)
        
        # Verify metrics
        self.assertIn("portfolio_total_signals", metrics)
        
        # Test calculate_signal_quality_metrics
        signals_df = signals_pl.rename({"Position": "signal"})
        
        quality_metrics = calculate_signal_quality_metrics(
            signals_df,
            returns_pl,
            "test_strategy",
            self.log
        )
        
        # Verify metrics
        self.assertIn("signal_count", quality_metrics)
        self.assertIn("signal_quality_score", quality_metrics)


if __name__ == "__main__":
    unittest.main()