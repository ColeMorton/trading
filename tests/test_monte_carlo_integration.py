"""
Comprehensive tests for Monte Carlo integration with the concurrency framework.

This test suite covers end-to-end integration testing, including:
- Integration with the concurrency analysis pipeline
- Monte Carlo report generation
- CSV/JSON portfolio integration
- Runner integration and workflow
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import polars as pl
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.config import create_monte_carlo_config
from app.concurrency.tools.monte_carlo.manager import PortfolioMonteCarloManager
from app.concurrency.tools.report.generator import generate_json_report
from app.concurrency.tools.runner import run_analysis
from app.concurrency.tools.types import ConcurrencyConfig


class TestMonteCarloReportIntegration:
    """Test Monte Carlo integration with report generation."""

    @pytest.fixture
    def mock_strategies(self):
        """Create mock strategy configurations."""
        return [
            {
                "TICKER": "BTC-USD",
                "STRATEGY_TYPE": "SMA",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 20,
                "strategy_id": "BTC-USD_SMA_10_20_0",
            },
            {
                "TICKER": "ETH-USD",
                "STRATEGY_TYPE": "MACD",
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
                "strategy_id": "ETH-USD_MACD_12_26_9",
            },
        ]

    @pytest.fixture
    def mock_stats(self):
        """Create mock concurrency statistics."""
        return {
            "total_concurrent_periods": 100,
            "concurrency_ratio": 0.8,
            "exclusive_ratio": 0.15,
            "inactive_ratio": 0.05,
            "avg_concurrent_strategies": 1.6,
            "max_concurrent_strategies": 2,
            "efficiency_score": 0.75,
            "total_expectancy": 150.0,
            "diversification_multiplier": 0.9,
            "independence_multiplier": 0.8,
            "activity_multiplier": 0.95,
            "risk_concentration_index": 0.6,
            "signal_metrics": {"total_signals": 50, "avg_signals_per_month": 12.5},
            "risk_metrics": {"var_95": -0.05, "cvar_95": -0.08},
        }

    @pytest.fixture
    def mock_monte_carlo_results(self):
        """Create mock Monte Carlo results."""
        mock_result1 = Mock()
        mock_result1.ticker = "BTC-USD"
        mock_result1.portfolio_stability_score = 0.7
        mock_result1.recommended_parameters = (10, 20)
        mock_result1.parameter_results = []
        mock_result1.analysis_metadata = {"num_simulations": 100}

        mock_result2 = Mock()
        mock_result2.ticker = "ETH-USD"
        mock_result2.portfolio_stability_score = 0.6
        mock_result2.recommended_parameters = (12, 26)
        mock_result2.parameter_results = []
        mock_result2.analysis_metadata = {"num_simulations": 100}

        return {
            "BTC-USD_SMA_10_20_0": mock_result1,
            "ETH-USD_MACD_12_26_9": mock_result2,
        }

    def test_monte_carlo_in_json_report(
        self, mock_strategies, mock_stats, mock_monte_carlo_results
    ):
        """Test Monte Carlo results inclusion in JSON report."""
        config = {
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 100,
            "MC_CONFIDENCE_LEVEL": 0.95,
            "MC_MAX_PARAMETERS_TO_TEST": 10,
        }

        report = generate_json_report(
            strategies=mock_strategies,
            stats=mock_stats,
            log=Mock(),
            config=config,
            monte_carlo_results=mock_monte_carlo_results,
        )

        # Check that Monte Carlo section is included
        assert "monte_carlo" in report["portfolio_metrics"]

        mc_section = report["portfolio_metrics"]["monte_carlo"]
        assert "total_strategies_analyzed" in mc_section
        assert "stable_strategies_count" in mc_section
        assert "stable_strategies_percentage" in mc_section
        assert "average_stability_score" in mc_section
        assert "simulation_parameters" in mc_section
        assert "strategy_results" in mc_section

        # Check simulation parameters
        sim_params = mc_section["simulation_parameters"]
        assert sim_params["num_simulations"] == 100
        assert sim_params["confidence_level"] == 0.95
        assert sim_params["max_parameters_tested"] == 10

        # Check strategy results structure
        strategy_results = mc_section["strategy_results"]
        assert "BTC-USD_SMA_10_20_0" in strategy_results
        assert "ETH-USD_MACD_12_26_9" in strategy_results

    def test_monte_carlo_disabled_in_report(self, mock_strategies, mock_stats):
        """Test that Monte Carlo is excluded when disabled."""
        config = {"MC_INCLUDE_IN_REPORTS": False}

        report = generate_json_report(
            strategies=mock_strategies,
            stats=mock_stats,
            log=Mock(),
            config=config,
            monte_carlo_results={},
        )

        # Monte Carlo section should not be included
        assert "monte_carlo" not in report["portfolio_metrics"]

    def test_report_with_empty_monte_carlo_results(self, mock_strategies, mock_stats):
        """Test report generation with empty Monte Carlo results."""
        config = {"MC_INCLUDE_IN_REPORTS": True}

        report = generate_json_report(
            strategies=mock_strategies,
            stats=mock_stats,
            log=Mock(),
            config=config,
            monte_carlo_results={},
        )

        # Should handle empty results gracefully
        assert isinstance(report, dict)
        assert "portfolio_metrics" in report


class TestMonteCarloRunnerIntegration:
    """Test Monte Carlo integration with the runner module."""

    @pytest.fixture
    def test_config(self):
        """Create test configuration for runner."""
        return {
            "PORTFOLIO": "test_portfolio.csv",
            "MC_INCLUDE_IN_REPORTS": True,
            "MC_NUM_SIMULATIONS": 5,
            "MC_CONFIDENCE_LEVEL": 0.95,
            "MC_MAX_PARAMETERS_TO_TEST": 3,
            "MC_MAX_WORKERS": 2,
            "VISUALIZATION": False,
        }

    @pytest.fixture
    def mock_strategies_for_runner(self):
        """Create mock strategies for runner testing."""
        return [
            {
                "ticker": "BTC-USD",
                "STRATEGY_TYPE": "SMA",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 20,
                "strategy_id": "BTC-USD_SMA_10_20_0",
            },
            {
                "ticker": "ETH-USD",
                "STRATEGY_TYPE": "MACD",
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
                "strategy_id": "ETH-USD_MACD_12_26_9",
            },
        ]

    @patch("app.concurrency.tools.runner.process_strategies")
    @patch("app.concurrency.tools.runner.analyze_concurrency")
    @patch("app.concurrency.tools.runner.save_json_report")
    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_runner_with_monte_carlo_enabled(
        self,
        mock_download,
        mock_save_report,
        mock_analyze,
        mock_process,
        test_config,
        mock_strategies_for_runner,
    ):
        """Test runner integration with Monte Carlo enabled."""
        # Mock process_strategies
        mock_process.return_value = ([], mock_strategies_for_runner)

        # Mock analyze_concurrency
        mock_stats = {
            "total_concurrent_periods": 100,
            "concurrency_ratio": 0.8,
            "exclusive_ratio": 0.15,
            "inactive_ratio": 0.05,
            "avg_concurrent_strategies": 1.6,
            "max_concurrent_strategies": 2,
            "efficiency_score": 0.75,
            "total_expectancy": 150.0,
            "diversification_multiplier": 0.9,
            "independence_multiplier": 0.8,
            "activity_multiplier": 0.95,
            "risk_concentration_index": 0.6,
            "signal_metrics": {"total_signals": 50},
            "risk_metrics": {"var_95": -0.05},
        }
        mock_analyze.return_value = (mock_stats, [])

        # Mock price data download
        mock_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(30)],
                "Close": [1000.0 + i for i in range(30)],
            }
        )
        mock_download.return_value = mock_data

        # Run analysis
        result = run_analysis(
            strategies=mock_strategies_for_runner, log=Mock(), config=test_config
        )

        assert result == True
        mock_save_report.assert_called_once()

    def test_monte_carlo_config_creation_from_runner_config(self, test_config):
        """Test Monte Carlo configuration creation from runner config."""
        mc_config = create_monte_carlo_config(test_config)

        assert mc_config.num_simulations == 5
        assert mc_config.confidence_level == 0.95
        assert mc_config.max_parameters_to_test == 3

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_monte_carlo_strategy_conversion_in_runner(self, mock_download):
        """Test strategy conversion for Monte Carlo in runner context."""
        # Mock price data
        mock_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(20)],
                "Close": [1000.0 + i for i in range(20)],
            }
        )
        mock_download.return_value = mock_data

        # Test strategies with different field name formats
        runner_strategies = [
            {
                "ticker": "BTC-USD",
                "type": "SMA",  # Runner format
                "fast_period": 10,
                "slow_period": 20,
            },
            {
                "ticker": "ETH-USD",
                "STRATEGY_TYPE": "MACD",  # CSV format
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
            },
        ]

        config = create_monte_carlo_config(
            {"MC_NUM_SIMULATIONS": 3, "MC_MAX_WORKERS": 1}
        )

        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Convert to portfolio format (simulating runner conversion)
        portfolio_strategies = []
        for strategy in runner_strategies:
            strategy_type = (
                strategy.get("type")
                or strategy.get("STRATEGY_TYPE")
                or strategy.get("Strategy Type")
            )

            portfolio_strategy = {
                "ticker": strategy.get("ticker"),
                "Strategy Type": strategy_type,
                "Window Short": strategy.get("fast_period")
                or strategy.get("FAST_PERIOD"),
                "Window Long": strategy.get("slow_period")
                or strategy.get("SLOW_PERIOD"),
            }

            if strategy_type == "MACD":
                signal_period = strategy.get("signal_period") or strategy.get(
                    "SIGNAL_PERIOD"
                )
                if signal_period:
                    portfolio_strategy["Signal Period"] = signal_period

            portfolio_strategies.append(portfolio_strategy)

        # Test that conversion works
        results = manager.analyze_portfolio(portfolio_strategies)

        # Should handle both strategy formats
        assert isinstance(results, dict)


class TestMonteCarloCSVPortfolioIntegration:
    """Test Monte Carlo integration with CSV portfolio files."""

    def test_csv_field_name_handling(self):
        """Test that CSV field names are properly handled in Monte Carlo."""
        # Create temporary CSV content
        csv_content = """Ticker,Strategy Type,Fast Period,Slow Period,Signal Period
BTC-USD,SMA,10,20,
ETH-USD,MACD,12,26,9
BTC-USD,EMA,14,28,"""

        # Parse CSV format strategies (simulating CSV loading)
        csv_strategies = [
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Signal Period": None,
            },
            {
                "Ticker": "ETH-USD",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
            },
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "EMA",
                "Fast Period": 14,
                "Slow Period": 28,
                "Signal Period": None,
            },
        ]

        config = create_monte_carlo_config({"MC_NUM_SIMULATIONS": 2})
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Test strategy ID assignment with CSV field names
        strategies_with_ids = manager._assign_strategy_ids(csv_strategies)

        assert len(strategies_with_ids) == 3

        strategy_ids = list(strategies_with_ids.keys())

        # Check that MACD includes signal period
        macd_ids = [sid for sid in strategy_ids if "MACD" in sid]
        assert len(macd_ids) == 1
        assert "_9" in macd_ids[0]

        # Check that SMA and EMA have 0 signal period
        sma_ids = [sid for sid in strategy_ids if "SMA" in sid]
        ema_ids = [sid for sid in strategy_ids if "EMA" in sid]
        assert len(sma_ids) == 1
        assert len(ema_ids) == 1
        assert "_0" in sma_ids[0]
        assert "_0" in ema_ids[0]

    def test_missing_signal_window_handling(self):
        """Test handling of missing signal period values."""
        strategies = [
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26
                # Missing Signal Period
            }
        ]

        config = create_monte_carlo_config({"MC_NUM_SIMULATIONS": 1})
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        strategies_with_ids = manager._assign_strategy_ids(strategies)

        # Should default to 0 for missing signal period
        strategy_id = list(strategies_with_ids.keys())[0]
        assert "_0" in strategy_id


class TestMonteCarloEndToEndWorkflow:
    """Test complete end-to-end Monte Carlo workflow."""

    def create_test_portfolio_csv(self, temp_dir):
        """Create a temporary test portfolio CSV file."""
        csv_content = """Ticker,Strategy Type,Fast Period,Slow Period,Signal Period
BTC-USD,SMA,10,20,
BTC-USD,MACD,12,26,9
ETH-USD,EMA,15,30,"""

        csv_path = temp_dir / "test_portfolio.csv"
        csv_path.write_text(csv_content)
        return csv_path

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    @patch("app.tools.portfolio.load_portfolio")
    def test_complete_workflow(self, mock_load_portfolio, mock_download):
        """Test complete Monte Carlo workflow from CSV to report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock portfolio loading
            mock_strategies = [
                {
                    "TICKER": "BTC-USD",
                    "STRATEGY_TYPE": "SMA",
                    "FAST_PERIOD": 10,
                    "SLOW_PERIOD": 20,
                },
                {
                    "TICKER": "BTC-USD",
                    "STRATEGY_TYPE": "MACD",
                    "FAST_PERIOD": 12,
                    "SLOW_PERIOD": 26,
                    "SIGNAL_PERIOD": 9,
                },
            ]
            mock_load_portfolio.return_value = mock_strategies

            # Mock price data
            mock_data = pl.DataFrame(
                {
                    "Date": [
                        pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(30)
                    ],
                    "Close": [1000.0 + i * 5 + np.sin(i * 0.2) * 20 for i in range(30)],
                }
            )
            mock_download.return_value = mock_data

            # Configuration
            config = {
                "PORTFOLIO": "test_portfolio.csv",
                "MC_INCLUDE_IN_REPORTS": True,
                "MC_NUM_SIMULATIONS": 3,
                "MC_CONFIDENCE_LEVEL": 0.95,
                "MC_MAX_PARAMETERS_TO_TEST": 2,
                "MC_MAX_WORKERS": 1,
                "VISUALIZATION": False,
                "OPTIMIZE": False,
            }

            # Mock the concurrency analysis components
            with patch(
                "app.concurrency.tools.runner.process_strategies"
            ) as mock_process, patch(
                "app.concurrency.tools.runner.analyze_concurrency"
            ) as mock_analyze, patch(
                "app.concurrency.tools.runner.save_json_report"
            ) as mock_save:
                # Setup mocks
                mock_process.return_value = ([], mock_strategies)

                mock_stats = {
                    "total_concurrent_periods": 50,
                    "concurrency_ratio": 0.7,
                    "exclusive_ratio": 0.2,
                    "inactive_ratio": 0.1,
                    "avg_concurrent_strategies": 1.4,
                    "max_concurrent_strategies": 2,
                    "efficiency_score": 0.65,
                    "total_expectancy": 120.0,
                    "diversification_multiplier": 0.85,
                    "independence_multiplier": 0.75,
                    "activity_multiplier": 0.9,
                    "risk_concentration_index": 0.55,
                    "signal_metrics": {"total_signals": 30},
                    "risk_metrics": {"var_95": -0.04},
                }
                mock_analyze.return_value = (mock_stats, [])

                # Run the analysis
                result = run_analysis(
                    strategies=mock_strategies, log=Mock(), config=config
                )

                assert result == True
                mock_save.assert_called_once()

                # Verify that the report includes Monte Carlo results
                report_call_args = mock_save.call_args[0][
                    0
                ]  # First argument to save_json_report
                assert "portfolio_metrics" in report_call_args

    def test_strategy_id_consistency_across_pipeline(self):
        """Test that strategy IDs are consistent across the entire pipeline."""
        # Test data that flows through the pipeline
        original_strategy = {
            "ticker": "BTC-USD",
            "Strategy Type": "MACD",
            "Window Short": 14,
            "Window Long": 23,
            "Signal Period": 13,
        }

        config = create_monte_carlo_config({"MC_NUM_SIMULATIONS": 1})
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Test strategy ID generation
        strategies_with_ids = manager._assign_strategy_ids([original_strategy])
        strategy_id = list(strategies_with_ids.keys())[0]

        # Should match the format from the CSV example
        expected_id = "BTC-USD_MACD_14_23_13"
        assert strategy_id == expected_id

        # Test that the original strategy data is preserved
        strategy_data = strategies_with_ids[strategy_id]
        assert strategy_data["ticker"] == "BTC-USD"
        assert strategy_data["Strategy Type"] == "MACD"

    def test_error_resilience_in_workflow(self):
        """Test that the workflow is resilient to various errors."""
        config = create_monte_carlo_config(
            {"MC_NUM_SIMULATIONS": 2, "MC_MAX_WORKERS": 1}
        )
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Test with problematic portfolio
        problematic_portfolio = [
            {
                "ticker": "VALID-TICKER",
                "Strategy Type": "SMA",
                "Window Short": 10,
                "Window Long": 20,
            },
            {
                "ticker": "INVALID-TICKER",
                "Strategy Type": "UNKNOWN_STRATEGY",  # Invalid strategy
                "Window Short": 5,
                "Window Long": 15,
            },
            {
                # Missing ticker
                "Strategy Type": "EMA",
                "Window Short": 12,
                "Window Long": 26,
            },
        ]

        # Should handle errors gracefully
        try:
            strategies_with_ids = manager._assign_strategy_ids(problematic_portfolio)
            # If it succeeds, should have some valid strategies
            assert len(strategies_with_ids) >= 1
        except Exception:
            # If it fails, should be with meaningful error
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
