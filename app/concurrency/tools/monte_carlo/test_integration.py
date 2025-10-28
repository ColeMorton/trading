"""
Integration Tests for Monte Carlo Review Pipeline.

Tests the end-to-end integration of Monte Carlo analysis with the
concurrency review pipeline including configuration, reporting, and visualization.
"""

import unittest
from unittest.mock import Mock, patch

from app.concurrency.tools.monte_carlo import (
    MonteCarloConfig,
    PortfolioMonteCarloManager,
    create_monte_carlo_config,
)


class TestMonteCarloIntegration(unittest.TestCase):
    """Test Monte Carlo integration with concurrency framework."""

    def setUp(self):
        """Set up test configuration."""
        self.base_config = {
            "PORTFOLIO": "test_portfolio.csv",
            "BASE_DIR": "test",
            "REFRESH": True,
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 50,  # Small for testing
            "MC_CONFIDENCE_LEVEL": 0.95,
            "MC_MAX_PARAMETERS_TO_TEST": 5,
        }

    def test_monte_carlo_config_creation(self):
        """Test Monte Carlo configuration creation from base config."""
        mc_config = create_monte_carlo_config(self.base_config)

        self.assertIsInstance(mc_config, MonteCarloConfig)
        self.assertTrue(mc_config.include_in_reports)
        self.assertEqual(mc_config.num_simulations, 50)
        self.assertEqual(mc_config.confidence_level, 0.95)
        self.assertEqual(mc_config.max_parameters_to_test, 5)

    def test_monte_carlo_config_defaults(self):
        """Test Monte Carlo configuration with defaults."""
        minimal_config = {"MC_INCLUDE_IN_REPORTS": True}
        mc_config = create_monte_carlo_config(minimal_config)

        self.assertTrue(mc_config.include_in_reports)
        self.assertEqual(mc_config.num_simulations, 100)  # Default
        self.assertEqual(mc_config.confidence_level, 0.95)  # Default
        self.assertEqual(mc_config.max_parameters_to_test, 10)  # Default

    def test_monte_carlo_disabled_config(self):
        """Test Monte Carlo with disabled configuration."""
        disabled_config = {"MC_INCLUDE_IN_REPORTS": False}
        mc_config = create_monte_carlo_config(disabled_config)

        self.assertFalse(mc_config.include_in_reports)
        self.assertFalse(mc_config.is_enabled())

    def test_portfolio_manager_creation(self):
        """Test creation of portfolio Monte Carlo manager."""
        mc_config = create_monte_carlo_config(self.base_config)

        manager = PortfolioMonteCarloManager(
            config=mc_config,
            max_workers=2,
            log=Mock(),
        )

        self.assertEqual(manager.config, mc_config)
        self.assertEqual(manager.max_workers, 2)
        self.assertIsNotNone(manager.analyzer)
        self.assertIsNotNone(manager.progress_tracker)

    @patch("app.concurrency.tools.monte_carlo.manager.download_data")
    def test_strategy_parameter_extraction(self, mock_download):
        """Test extraction of parameters from strategy format."""
        # Mock successful data download
        import polars as pl

        mock_data = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.0],
            },
        )
        mock_download.return_value = mock_data

        mc_config = create_monte_carlo_config(self.base_config)
        manager = PortfolioMonteCarloManager(mc_config, log=Mock())

        # Test strategy format used by concurrency module
        strategies = [
            {
                "ticker": "AAPL",
                "fast_period": 10,
                "slow_period": 20,
            },
            {
                "ticker": "MSFT",
                "FAST_PERIOD": 15,  # Alternative key format
                "SLOW_PERIOD": 30,
            },
            {
                # Missing ticker and parameters - should be filtered out
                "some_other_field": "value",
            },
        ]

        # Test grouping
        grouped = manager._group_strategies_by_ticker(strategies)
        self.assertEqual(len(grouped), 2)  # GOOGL filtered out
        self.assertIn("AAPL", grouped)
        self.assertIn("MSFT", grouped)

        # Test parameter extraction
        aapl_params = manager._extract_parameter_combinations(grouped["AAPL"])
        self.assertEqual(len(aapl_params), 1)
        self.assertEqual(aapl_params[0], (10, 20))

        msft_params = manager._extract_parameter_combinations(grouped["MSFT"])
        self.assertEqual(len(msft_params), 1)
        self.assertEqual(msft_params[0], (15, 30))

    def test_monte_carlo_report_format(self):
        """Test Monte Carlo results in report format."""
        # Mock Monte Carlo results
        mock_param_result = Mock()
        mock_param_result.parameter_combination = (10, 20)
        mock_param_result.stability_score = 0.8
        mock_param_result.parameter_robustness = 0.7
        mock_param_result.regime_consistency = 0.6
        mock_param_result.is_stable = True

        mock_portfolio_result = Mock()
        mock_portfolio_result.portfolio_stability_score = 0.75
        mock_portfolio_result.recommended_parameters = (10, 20)
        mock_portfolio_result.parameter_results = [mock_param_result]

        monte_carlo_results = {"AAPL": mock_portfolio_result}

        # Test report generation import
        from app.concurrency.tools.report.generator import generate_json_report

        # Mock strategies and stats
        strategies = [{"TICKER": "AAPL", "strategy_id": "test_1"}]
        stats = {
            "total_concurrent_periods": 100,
            "concurrency_ratio": 0.5,
            "exclusive_ratio": 0.3,
            "inactive_ratio": 0.2,
            "avg_concurrent_strategies": 1.5,
            "max_concurrent_strategies": 3,
            "efficiency_score": 0.8,
            "total_expectancy": 0.1,
            "diversification_multiplier": 1.2,
            "independence_multiplier": 1.1,
            "activity_multiplier": 1.0,
            "risk_concentration_index": 0.3,
            "signal_metrics": {
                "mean_signals": 1.0,
                "correlation_signals": 0.5,
                "independence_signals": 0.7,
            },
            "risk_metrics": {
                "mean_var": 0.1,
                "correlation_var": 0.3,
                "independence_var": 0.8,
            },
        }

        config = self.base_config.copy()

        # Generate report with Monte Carlo results
        report = generate_json_report(
            strategies,
            stats,
            Mock(),
            config,
            monte_carlo_results,
        )

        # Verify report structure
        self.assertIn("monte_carlo_analysis", report)
        mc_section = report["monte_carlo_analysis"]

        self.assertIn("portfolio_metrics", mc_section)
        self.assertIn("ticker_results", mc_section)

        # Verify portfolio metrics
        portfolio_metrics = mc_section["portfolio_metrics"]
        self.assertEqual(portfolio_metrics["total_tickers_analyzed"], 1)
        self.assertEqual(portfolio_metrics["stable_tickers_count"], 1)
        self.assertEqual(portfolio_metrics["stable_tickers_percentage"], 100.0)

        # Verify ticker results
        ticker_results = mc_section["ticker_results"]
        self.assertIn("AAPL", ticker_results)

        aapl_result = ticker_results["AAPL"]
        self.assertEqual(aapl_result["portfolio_stability_score"], 0.75)
        self.assertEqual(aapl_result["recommended_parameters"], (10, 20))
        self.assertEqual(len(aapl_result["parameter_results"]), 1)

        param_result = aapl_result["parameter_results"][0]
        self.assertEqual(param_result["parameter_combination"], (10, 20))
        self.assertEqual(param_result["stability_score"], 0.8)
        self.assertTrue(param_result["is_stable"])

    def test_visualization_integration(self):
        """Test visualization integration with Monte Carlo results."""
        from app.concurrency.tools.monte_carlo.visualization import (
            MonteCarloVisualizationConfig,
            PortfolioMonteCarloVisualizer,
        )

        # Test visualization config
        viz_config = MonteCarloVisualizationConfig(
            output_dir="test_output",
            enable_seaborn=False,  # Disable for testing
        )

        self.assertEqual(viz_config.output_dir, "test_output")
        self.assertFalse(viz_config.enable_seaborn)

        # Test visualizer creation
        visualizer = PortfolioMonteCarloVisualizer(viz_config)
        self.assertEqual(visualizer.config, viz_config)

    def test_configuration_validation(self):
        """Test configuration validation and type checking."""
        # Test valid configuration
        valid_config = {
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 100,
            "MC_CONFIDENCE_LEVEL": 0.95,
            "MC_MAX_PARAMETERS_TO_TEST": 10,
        }

        mc_config = create_monte_carlo_config(valid_config)
        validated = mc_config.validate()

        self.assertEqual(validated.num_simulations, 100)
        self.assertEqual(validated.confidence_level, 0.95)
        self.assertEqual(validated.max_parameters_to_test, 10)

        # Test configuration with validation needed
        invalid_config = {
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 5000,  # Too high
            "MC_CONFIDENCE_LEVEL": 1.5,  # Invalid
            "MC_MAX_PARAMETERS_TO_TEST": 100,  # Too high
        }

        mc_config = create_monte_carlo_config(invalid_config)
        validated = mc_config.validate()

        # Should be capped at limits
        self.assertEqual(validated.num_simulations, 1000)  # Capped
        self.assertEqual(validated.confidence_level, 0.999)  # Capped
        self.assertEqual(validated.max_parameters_to_test, 50)  # Capped


class TestMonteCarloConfigDefaults(unittest.TestCase):
    """Test Monte Carlo configuration defaults integration."""

    def test_config_defaults_integration(self):
        """Test integration with config_defaults.py."""
        from app.concurrency.config_defaults import (
            get_default_config,
            get_monte_carlo_defaults,
        )

        # Test Monte Carlo defaults are included
        mc_defaults = get_monte_carlo_defaults()
        self.assertIn("MC_INCLUDE_IN_REPORTS", mc_defaults)
        self.assertIn("MC_NUM_SIMULATIONS", mc_defaults)
        self.assertIn("MC_CONFIDENCE_LEVEL", mc_defaults)
        self.assertIn("MC_MAX_PARAMETERS_TO_TEST", mc_defaults)

        # Test default values
        self.assertFalse(mc_defaults["MC_INCLUDE_IN_REPORTS"])
        self.assertEqual(mc_defaults["MC_NUM_SIMULATIONS"], 100)
        self.assertEqual(mc_defaults["MC_CONFIDENCE_LEVEL"], 0.95)
        self.assertEqual(mc_defaults["MC_MAX_PARAMETERS_TO_TEST"], 10)

        # Test integration with full config
        full_config = get_default_config()
        for key in mc_defaults:
            self.assertIn(key, full_config)
            self.assertEqual(full_config[key], mc_defaults[key])


if __name__ == "__main__":
    unittest.main()
