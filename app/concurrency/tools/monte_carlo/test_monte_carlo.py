"""
Unit Tests for Monte Carlo Parameter Robustness Analysis.

Tests core Monte Carlo functionality including bootstrap sampling,
parameter stability analysis, and configuration management.
"""

import unittest
from unittest.mock import patch

import numpy as np
import polars as pl

from app.concurrency.tools.monte_carlo import (
    BootstrapSampler,
    MonteCarloAnalyzer,
    MonteCarloConfig,
    create_monte_carlo_config,
)


class TestMonteCarloConfig(unittest.TestCase):
    """Test Monte Carlo configuration management."""

    def test_default_config_creation(self):
        """Test creation of default Monte Carlo configuration."""
        config = MonteCarloConfig()

        self.assertFalse(config.include_in_reports)
        self.assertEqual(config.num_simulations, 100)
        self.assertEqual(config.confidence_level, 0.95)
        self.assertEqual(config.max_parameters_to_test, 10)

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 500,
            "MC_CONFIDENCE_LEVEL": 0.99,
            "MC_MAX_PARAMETERS_TO_TEST": 20,
        }

        config = MonteCarloConfig.from_dict(config_dict)

        self.assertTrue(config.include_in_reports)
        self.assertEqual(config.num_simulations, 500)
        self.assertEqual(config.confidence_level, 0.99)
        self.assertEqual(config.max_parameters_to_test, 20)

    def test_config_validation(self):
        """Test configuration validation and bounds checking."""
        config = MonteCarloConfig(
            num_simulations=5000,  # Should be capped at 1000
            confidence_level=1.5,  # Should be capped at 0.999
            max_parameters_to_test=100,  # Should be capped at 50
        )

        validated = config.validate()

        self.assertEqual(validated.num_simulations, 1000)
        self.assertEqual(validated.confidence_level, 0.999)
        self.assertEqual(validated.max_parameters_to_test, 50)

    def test_create_monte_carlo_config(self):
        """Test config creation helper function."""
        base_config = {"MC_NUM_SIMULATIONS": 200}
        config = create_monte_carlo_config(base_config)

        self.assertEqual(config.num_simulations, 200)
        self.assertFalse(config.include_in_reports)  # Default value


class TestBootstrapSampler(unittest.TestCase):
    """Test bootstrap sampling functionality."""

    def setUp(self):
        """Set up test data."""
        # Create sample price data
        dates = pl.date_range(
            start=pl.date(2023, 1, 1),
            end=pl.date(2023, 12, 31),
            interval="1d",
            eager=True,
        )
        n_periods = len(dates)

        # Generate synthetic price data
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.normal(0, 1, n_periods))

        self.test_data = pl.DataFrame(
            {
                "Date": dates,
                "Close": prices,
                "Open": prices * 0.99,
                "High": prices * 1.01,
                "Low": prices * 0.98,
            },
        )

        self.sampler = BootstrapSampler(block_size=30, min_data_fraction=0.7)

    def test_bootstrap_sample_length(self):
        """Test that bootstrap sample has appropriate length."""
        sample = self.sampler.block_bootstrap_sample(self.test_data, seed=42)

        min_expected = int(len(self.test_data) * 0.7)
        self.assertGreaterEqual(len(sample), min_expected)

    def test_bootstrap_sample_structure(self):
        """Test that bootstrap sample maintains DataFrame structure."""
        sample = self.sampler.block_bootstrap_sample(self.test_data, seed=42)

        # Check columns are preserved
        self.assertEqual(list(sample.columns), list(self.test_data.columns))

        # Check data types are preserved
        for col in sample.columns:
            self.assertEqual(sample[col].dtype, self.test_data[col].dtype)

    def test_bootstrap_sample_reproducibility(self):
        """Test that bootstrap sampling is reproducible with same seed."""
        sample1 = self.sampler.block_bootstrap_sample(self.test_data, seed=42)
        sample2 = self.sampler.block_bootstrap_sample(self.test_data, seed=42)

        # Should be identical with same seed
        self.assertTrue(sample1.equals(sample2))

    def test_bootstrap_sample_variability(self):
        """Test that bootstrap sampling produces different results with different seeds."""
        sample1 = self.sampler.block_bootstrap_sample(self.test_data, seed=42)
        sample2 = self.sampler.block_bootstrap_sample(self.test_data, seed=43)

        # Should be different with different seeds
        self.assertFalse(sample1.equals(sample2))

    def test_parameter_noise_injection(self):
        """Test parameter noise injection functionality."""
        short, long = 20, 50

        # Test multiple iterations to ensure variability
        results = []
        for _ in range(100):
            noisy_short, noisy_long = self.sampler.parameter_noise_injection(
                short, long, noise_std=0.1,
            )
            results.append((noisy_short, noisy_long))

        # Check that results vary
        unique_results = set(results)
        self.assertGreater(len(unique_results), 50)  # Should have variety

        # Check constraints are maintained
        for noisy_short, noisy_long in results:
            self.assertGreaterEqual(noisy_short, 2)  # Minimum fast period
            self.assertGreater(noisy_long, noisy_short)  # Long > short

    def test_short_time_series_handling(self):
        """Test bootstrap sampling with short time series."""
        # Create short dataset
        short_data = self.test_data[:20]  # Only 20 periods

        sample = self.sampler.block_bootstrap_sample(short_data, seed=42)

        # Should handle short series gracefully
        self.assertGreater(len(sample), 10)
        self.assertEqual(list(sample.columns), list(short_data.columns))


class TestMonteCarloAnalyzer(unittest.TestCase):
    """Test Monte Carlo analyzer functionality."""

    def setUp(self):
        """Set up test analyzer and data."""
        self.config = MonteCarloConfig(
            include_in_reports=True,
            num_simulations=10,  # Small number for fast testing
            confidence_level=0.95,
            max_parameters_to_test=3,
        )

        self.analyzer = MonteCarloAnalyzer(self.config)

        # Create test data
        dates = pl.date_range(
            start=pl.date(2023, 1, 1),
            end=pl.date(2023, 6, 30),
            interval="1d",
            eager=True,
        )
        n_periods = len(dates)

        # Generate trending price data for more predictable test results
        np.random.seed(42)
        trend = np.linspace(100, 110, n_periods)
        noise = np.random.normal(0, 0.5, n_periods)
        prices = trend + noise

        self.test_data = pl.DataFrame(
            {
                "Date": dates,
                "Close": prices,
                "Open": prices * 0.999,
                "High": prices * 1.001,
                "Low": prices * 0.999,
            },
        )

    @patch("app.concurrency.tools.monte_carlo.core.calculate_ma_and_signals")
    def test_strategy_performance_calculation(self, mock_calculate_signals):
        """Test strategy performance calculation."""
        # Mock the calculate_ma_and_signals function
        mock_returns = np.array([0.01, -0.005, 0.02, 0.01, -0.01])
        mock_signals_data = pl.DataFrame({"Returns": mock_returns})
        mock_calculate_signals.return_value = mock_signals_data

        performance = self.analyzer._calculate_strategy_performance(
            self.test_data, 10, 20,
        )

        self.assertIn("total_return", performance)
        self.assertIn("sharpe_ratio", performance)
        self.assertIn("max_drawdown", performance)

        # Check that performance metrics are reasonable
        self.assertIsInstance(performance["total_return"], float)
        self.assertIsInstance(performance["sharpe_ratio"], float)
        self.assertIsInstance(performance["max_drawdown"], float)

    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        alpha = 0.1  # 90% confidence interval

        lower, upper = self.analyzer._calculate_confidence_interval(values, alpha)

        # Should be reasonable bounds
        self.assertLess(lower, upper)
        self.assertGreaterEqual(lower, min(values))
        self.assertLessEqual(upper, max(values))

    def test_empty_values_handling(self):
        """Test handling of empty or invalid data."""
        # Test empty confidence interval
        lower, upper = self.analyzer._calculate_confidence_interval([], 0.1)
        self.assertEqual((lower, upper), (0.0, 0.0))

        # Test portfolio stability with empty results
        score = self.analyzer._calculate_portfolio_stability_score([])
        self.assertEqual(score, 0.0)

    def test_parameter_combination_limiting(self):
        """Test that parameter combinations are limited as configured."""
        # Create many parameter combinations
        many_params = [(i, i + 10) for i in range(5, 25)]  # 20 combinations

        # Analyzer is configured to test max 3 parameters
        with patch.object(
            self.analyzer, "_analyze_single_parameter_combination",
        ) as mock_analyze:
            mock_analyze.return_value = None

            # This would normally fail, but we're just testing the limiting logic
            try:
                self.analyzer.analyze_parameter_stability(
                    "TEST", self.test_data, many_params,
                )
            except:
                pass  # We expect this to fail due to mocked method

            # Should only call analyze for 3 parameter combinations
            self.assertEqual(mock_analyze.call_count, 3)


if __name__ == "__main__":
    unittest.main()
