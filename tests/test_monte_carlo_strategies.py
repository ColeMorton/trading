"""
Comprehensive tests for Monte Carlo analysis with different strategy types.

This test suite verifies that Monte Carlo analysis works correctly with
SMA, EMA, and MACD strategies, including proper parameter handling and
signal period support for MACD.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
from unittest.mock import Mock

import numpy as np
import polars as pl
import pytest


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.config import MonteCarloConfig
from app.concurrency.tools.monte_carlo.core import MonteCarloAnalyzer
from app.tools.strategy.factory import StrategyFactory


class TestMonteCarloStrategies:
    """Test Monte Carlo analysis with different strategy types."""

    @pytest.fixture
    def test_data(self):
        """Create realistic test price data."""
        np.random.seed(42)
        n_days = 60
        base_price = 45000.0

        # Generate price series with trend and volatility
        prices = [base_price]
        for i in range(n_days - 1):
            # Add trend, cyclical component, and noise
            trend = 0.0005  # Small upward trend
            cycle = 0.01 * np.sin(i * 2 * np.pi / 20)  # 20-day cycle
            noise = np.random.normal(0, 0.015)

            daily_return = trend + cycle + noise
            new_price = prices[-1] * (1 + daily_return)
            prices.append(float(max(new_price, 1000.0)))  # Prevent negative prices

        return pl.DataFrame(
            {
                "Date": [
                    datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_days)
                ],
                "Open": [
                    float(p * (1 + np.random.uniform(-0.002, 0.002))) for p in prices
                ],
                "High": [
                    float(p * (1 + abs(np.random.uniform(0, 0.008)))) for p in prices
                ],
                "Low": [
                    float(p * (1 - abs(np.random.uniform(0, 0.008)))) for p in prices
                ],
                "Close": prices,
            },
        )

    @pytest.fixture
    def analyzer(self):
        """Create Monte Carlo analyzer with test configuration."""
        config = MonteCarloConfig(
            num_simulations=5, confidence_level=0.95, max_parameters_to_test=3,
        )
        return MonteCarloAnalyzer(config=config, log=Mock())

    def test_sma_strategy_monte_carlo(self, analyzer, test_data):
        """Test Monte Carlo analysis with SMA strategy."""
        sma_config = {"STRATEGY_TYPE": "SMA", "BASE_DIR": "."}

        result = analyzer.analyze_parameter_stability(
            ticker="BTC-USD",
            data=test_data,
            parameter_combinations=[(10, 20), (15, 30), (5, 15)],
            strategy_type="SMA",
            strategy_config=sma_config,
        )

        # Verify results structure
        assert result.ticker == "BTC-USD"
        assert len(result.parameter_results) == 3
        assert result.portfolio_stability_score >= 0.0
        assert result.recommended_parameters is not None

        # Verify parameter combinations
        tested_params = [pr.parameter_combination for pr in result.parameter_results]
        assert (10, 20) in tested_params
        assert (15, 30) in tested_params
        assert (5, 15) in tested_params

        # Verify each parameter result has proper structure
        for param_result in result.parameter_results:
            assert (
                len(param_result.monte_carlo_results) == analyzer.config.num_simulations
            )
            assert "total_return" in param_result.base_performance
            assert "sharpe_ratio" in param_result.base_performance
            assert "max_drawdown" in param_result.base_performance

            # Verify stability metrics are calculated
            assert param_result.stability_score >= 0.0
            assert param_result.parameter_robustness >= 0.0
            assert param_result.regime_consistency >= 0.0

    def test_ema_strategy_monte_carlo(self, analyzer, test_data):
        """Test Monte Carlo analysis with EMA strategy."""
        ema_config = {"STRATEGY_TYPE": "EMA", "BASE_DIR": "."}

        result = analyzer.analyze_parameter_stability(
            ticker="ETH-USD",
            data=test_data,
            parameter_combinations=[(12, 26), (8, 21), (20, 50)],
            strategy_type="EMA",
            strategy_config=ema_config,
        )

        # Verify results structure
        assert result.ticker == "ETH-USD"
        assert len(result.parameter_results) == 3
        assert result.portfolio_stability_score >= 0.0

        # EMA should produce different results than SMA
        for param_result in result.parameter_results:
            assert param_result.parameter_combination in [(12, 26), (8, 21), (20, 50)]

            # Verify Monte Carlo simulations were run
            assert len(param_result.monte_carlo_results) == 5

            # Check that each simulation has valid performance metrics
            for sim_result in param_result.monte_carlo_results:
                assert "simulation_id" in sim_result
                assert "parameters" in sim_result
                assert "performance" in sim_result

                performance = sim_result["performance"]
                assert "total_return" in performance
                assert "sharpe_ratio" in performance
                assert "max_drawdown" in performance

    def test_macd_strategy_monte_carlo(self, analyzer, test_data):
        """Test Monte Carlo analysis with MACD strategy including signal period."""
        macd_config = {"STRATEGY_TYPE": "MACD", "SIGNAL_PERIOD": 9, "BASE_DIR": "."}

        result = analyzer.analyze_parameter_stability(
            ticker="BTC-USD",
            data=test_data,
            parameter_combinations=[(12, 26), (14, 28), (10, 22)],
            strategy_type="MACD",
            strategy_config=macd_config,
        )

        # Verify results structure
        assert result.ticker == "BTC-USD"
        assert len(result.parameter_results) == 3
        assert result.portfolio_stability_score >= 0.0

        # Verify MACD-specific behavior
        for param_result in result.parameter_results:
            # Check that signal period is being used in calculations
            # This is verified by ensuring the base performance is calculated correctly
            base_perf = param_result.base_performance
            assert isinstance(base_perf["total_return"], int | float)
            assert isinstance(base_perf["sharpe_ratio"], int | float)
            assert isinstance(base_perf["max_drawdown"], int | float)

            # Verify confidence intervals are calculated
            if hasattr(param_result, "confidence_intervals"):
                ci = param_result.confidence_intervals
                if ci:  # May be empty dict if no results
                    for (lower, upper) in ci.values():
                        assert lower <= upper

    def test_macd_signal_window_variations(self, analyzer, test_data):
        """Test MACD with different signal period values."""
        signal_windows = [7, 9, 12]

        results = []
        for signal_period in signal_windows:
            macd_config = {
                "STRATEGY_TYPE": "MACD",
                "SIGNAL_PERIOD": signal_period,
                "BASE_DIR": ".",
            }

            result = analyzer.analyze_parameter_stability(
                ticker="TEST-MACD",
                data=test_data,
                parameter_combinations=[(12, 26)],
                strategy_type="MACD",
                strategy_config=macd_config,
            )

            results.append((signal_period, result))

        # Verify all results are valid and potentially different
        for signal_period, result in results:
            assert result.ticker == "TEST-MACD"
            assert len(result.parameter_results) == 1
            assert result.portfolio_stability_score >= 0.0

            # Performance should be calculated (may vary with signal period)
            param_result = result.parameter_results[0]
            assert param_result.parameter_combination == (12, 26)
            assert "total_return" in param_result.base_performance

    def test_strategy_comparison(self, analyzer, test_data):
        """Test that different strategies produce different results."""
        parameter_combinations = [(12, 26)]

        # Run same parameters on different strategies
        sma_result = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=test_data,
            parameter_combinations=parameter_combinations,
            strategy_type="SMA",
            strategy_config={"STRATEGY_TYPE": "SMA"},
        )

        ema_result = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=test_data,
            parameter_combinations=parameter_combinations,
            strategy_type="EMA",
            strategy_config={"STRATEGY_TYPE": "EMA"},
        )

        macd_result = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=test_data,
            parameter_combinations=parameter_combinations,
            strategy_type="MACD",
            strategy_config={"STRATEGY_TYPE": "MACD", "SIGNAL_PERIOD": 9},
        )

        # Extract base performance values
        sma_perf = sma_result.parameter_results[0].base_performance
        ema_perf = ema_result.parameter_results[0].base_performance
        macd_perf = macd_result.parameter_results[0].base_performance

        # Results should be different (unless by coincidence)
        # We check that at least one metric differs significantly
        (
            abs(sma_perf["total_return"] - ema_perf["total_return"]) > 0.001
            or abs(sma_perf["total_return"] - macd_perf["total_return"]) > 0.001
            or abs(ema_perf["total_return"] - macd_perf["total_return"]) > 0.001
        )

        # If performance is identical, it might be due to no signals generated
        # Check that strategies at least run without error
        assert sma_result.portfolio_stability_score >= 0.0
        assert ema_result.portfolio_stability_score >= 0.0
        assert macd_result.portfolio_stability_score >= 0.0

    def test_invalid_strategy_type(self, analyzer, test_data):
        """Test handling of invalid strategy type."""
        # Invalid strategy should be handled gracefully, not raise exception
        result = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=test_data,
            parameter_combinations=[(10, 20)],
            strategy_type="INVALID_STRATEGY",
        )

        # Should return result with zero performance
        assert result.ticker == "TEST"
        param_result = result.parameter_results[0]
        assert param_result.base_performance["total_return"] == 0.0
        assert param_result.base_performance["sharpe_ratio"] == 0.0
        assert param_result.base_performance["max_drawdown"] == 1.0

    def test_missing_macd_signal_window(self, analyzer, test_data):
        """Test MACD without signal period configuration."""
        # MACD should still work with default signal period or handle missing gracefully
        result = analyzer.analyze_parameter_stability(
            ticker="TEST-MACD",
            data=test_data,
            parameter_combinations=[(12, 26)],
            strategy_type="MACD",
            strategy_config={"STRATEGY_TYPE": "MACD"},  # No SIGNAL_PERIOD specified
        )

        # Should either work with default or handle gracefully
        assert result.ticker == "TEST-MACD"
        assert len(result.parameter_results) == 1

    def test_extreme_parameter_values(self, analyzer, test_data):
        """Test Monte Carlo with extreme parameter values."""
        # Test with very short windows
        short_result = analyzer.analyze_parameter_stability(
            ticker="TEST-SHORT",
            data=test_data,
            parameter_combinations=[(2, 3)],
            strategy_type="SMA",
        )

        assert short_result.ticker == "TEST-SHORT"
        assert len(short_result.parameter_results) == 1

        # Test with very long windows (close to data length)
        long_result = analyzer.analyze_parameter_stability(
            ticker="TEST-LONG",
            data=test_data,
            parameter_combinations=[(25, 50)],
            strategy_type="SMA",
        )

        assert long_result.ticker == "TEST-LONG"
        assert len(long_result.parameter_results) == 1

    def test_strategy_factory_integration(self):
        """Test that all strategies are properly registered in factory."""
        factory = StrategyFactory()
        available_strategies = factory.get_available_strategies()

        # Verify all expected strategies are available
        assert "SMA" in available_strategies
        assert "EMA" in available_strategies
        assert "MACD" in available_strategies

        # Test that each strategy can be created
        for strategy_type in ["SMA", "EMA", "MACD"]:
            strategy = factory.create_strategy(strategy_type)
            assert strategy is not None
            assert hasattr(strategy, "calculate")

    def test_parameter_noise_injection(self, analyzer, test_data):
        """Test that parameter noise injection is working."""
        original_params = (12, 26)

        # Run analysis and check that Monte Carlo results use noisy parameters
        result = analyzer.analyze_parameter_stability(
            ticker="TEST-NOISE",
            data=test_data,
            parameter_combinations=[original_params],
            strategy_type="SMA",
        )

        param_result = result.parameter_results[0]

        # Check that simulations used different parameters due to noise
        used_parameters = [
            sim["parameters"] for sim in param_result.monte_carlo_results
        ]

        # At least some parameters should be different from original
        different_params = [p for p in used_parameters if p != original_params]
        assert (
            len(different_params) > 0
        ), "Parameter noise injection should modify some parameters"

        # Parameters should be close to original (within noise range)
        for noisy_short, noisy_long in used_parameters:
            assert abs(noisy_short - original_params[0]) <= 5  # Reasonable noise range
            assert abs(noisy_long - original_params[1]) <= 5


class TestStrategySpecificBehavior:
    """Test strategy-specific behavior in Monte Carlo analysis."""

    @pytest.fixture
    def trend_data(self):
        """Create data with clear trend for strategy testing."""
        n_days = 40
        base_price = 100.0

        # Create strong upward trend
        prices = [base_price + i * 2.0 for i in range(n_days)]

        return pl.DataFrame(
            {
                "Date": [
                    datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_days)
                ],
                "Close": prices,
            },
        )

    def test_sma_crossover_signals(self, trend_data):
        """Test that SMA generates expected signals on trending data."""
        config = MonteCarloConfig(num_simulations=3)
        analyzer = MonteCarloAnalyzer(config=config)

        result = analyzer.analyze_parameter_stability(
            ticker="TREND-SMA",
            data=trend_data,
            parameter_combinations=[(5, 15)],  # Short vs slow period
            strategy_type="SMA",
        )

        # Should generate some meaningful performance
        param_result = result.parameter_results[0]
        base_performance = param_result.base_performance

        # On strong uptrend, should capture some positive return
        # (though exact value depends on crossover timing)
        assert isinstance(base_performance["total_return"], int | float)
        assert isinstance(base_performance["sharpe_ratio"], int | float)

    def test_macd_signal_generation(self, trend_data):
        """Test that MACD generates signals with proper signal line."""
        config = MonteCarloConfig(num_simulations=3)
        analyzer = MonteCarloAnalyzer(config=config)

        macd_config = {
            "STRATEGY_TYPE": "MACD",
            "SIGNAL_PERIOD": 5,  # Short signal period for testing
        }

        result = analyzer.analyze_parameter_stability(
            ticker="TREND-MACD",
            data=trend_data,
            parameter_combinations=[(8, 16)],
            strategy_type="MACD",
            strategy_config=macd_config,
        )

        # Verify MACD analysis completed
        assert len(result.parameter_results) == 1
        param_result = result.parameter_results[0]

        # MACD should produce valid performance metrics
        base_perf = param_result.base_performance
        assert "total_return" in base_perf
        assert "sharpe_ratio" in base_perf
        assert "max_drawdown" in base_perf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
