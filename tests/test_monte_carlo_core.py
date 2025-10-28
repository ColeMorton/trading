"""
Comprehensive tests for Monte Carlo core functionality.

This test suite covers the core Monte Carlo parameter robustness analysis engine,
including bootstrap sampling, parameter stability analysis, and performance calculations.
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
from app.concurrency.tools.monte_carlo.core import (
    MonteCarloAnalyzer,
    MonteCarloPortfolioResult,
    ParameterStabilityResult,
)


class TestMonteCarloConfig:
    """Test Monte Carlo configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MonteCarloConfig()

        assert config.num_simulations == 100
        assert config.confidence_level == 0.95
        assert config.max_parameters_to_test == 10
        assert config.include_in_reports is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MonteCarloConfig(
            num_simulations=50, confidence_level=0.99, max_parameters_to_test=5,
        )

        assert config.num_simulations == 50
        assert config.confidence_level == 0.99
        assert config.max_parameters_to_test == 5

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = MonteCarloConfig(num_simulations=25)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["MC_NUM_SIMULATIONS"] == 25
        assert "MC_CONFIDENCE_LEVEL" in config_dict


class TestParameterStabilityResult:
    """Test parameter stability result data class."""

    def test_stability_result_creation(self):
        """Test creating a parameter stability result."""
        result = ParameterStabilityResult(
            parameter_combination=(12, 26),
            base_performance={"total_return": 0.1, "sharpe_ratio": 1.2},
            monte_carlo_results=[],
        )

        assert result.parameter_combination == (12, 26)
        assert result.base_performance["total_return"] == 0.1
        assert result.stability_score == 0.0  # Default value

    def test_is_stable_property(self):
        """Test stability evaluation."""
        # Create unstable result
        unstable_result = ParameterStabilityResult(
            parameter_combination=(12, 26), base_performance={}, monte_carlo_results=[],
        )
        assert not unstable_result.is_stable

        # Create stable result
        stable_result = ParameterStabilityResult(
            parameter_combination=(12, 26), base_performance={}, monte_carlo_results=[],
        )
        stable_result.stability_score = 0.6
        stable_result.parameter_robustness = 0.5
        stable_result.regime_consistency = 0.5
        assert stable_result.is_stable


class TestMonteCarloAnalyzer:
    """Test Monte Carlo analyzer functionality."""

    @pytest.fixture
    def test_data(self):
        """Create test price data."""
        np.random.seed(42)
        n_days = 100
        base_price = 50000.0

        # Generate realistic price series
        prices = [base_price]
        for _i in range(n_days - 1):
            change = np.random.normal(0.001, 0.02)
            new_price = prices[-1] * (1 + change)
            prices.append(float(new_price))

        return pl.DataFrame(
            {
                "Date": [
                    datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_days)
                ],
                "Open": [
                    float(p * (1 + np.random.uniform(-0.005, 0.005))) for p in prices
                ],
                "High": [
                    float(p * (1 + abs(np.random.uniform(0, 0.01)))) for p in prices
                ],
                "Low": [
                    float(p * (1 - abs(np.random.uniform(0, 0.01)))) for p in prices
                ],
                "Close": prices,
            },
        )

    @pytest.fixture
    def mock_log(self):
        """Create a mock logging function."""
        return Mock()

    @pytest.fixture
    def test_config(self):
        """Create test Monte Carlo configuration."""
        return MonteCarloConfig(
            num_simulations=5,  # Small for testing
            confidence_level=0.95,
            max_parameters_to_test=3,
        )

    @pytest.fixture
    def analyzer(self, test_config, mock_log):
        """Create Monte Carlo analyzer instance."""
        return MonteCarloAnalyzer(config=test_config, log=mock_log)

    def test_analyzer_initialization(self, analyzer, test_config):
        """Test analyzer initialization."""
        assert analyzer.config == test_config
        assert analyzer.bootstrap_sampler is not None
        assert analyzer.results == []

    def test_field_name_standardization(self, analyzer):
        """Test field name standardization."""
        csv_config = {
            "Signal Period": 9,
            "Fast Period": 12,
            "Slow Period": 26,
            "Strategy Type": "MACD",
        }

        standardized = analyzer._standardize_field_names(csv_config)

        assert standardized["SIGNAL_PERIOD"] == 9
        assert standardized["FAST_PERIOD"] == 12
        assert standardized["SLOW_PERIOD"] == 26
        assert standardized["STRATEGY_TYPE"] == "MACD"

        # Original keys should also be preserved
        assert standardized["Signal Period"] == 9

    def test_calculate_strategy_performance_sma(self, analyzer, test_data):
        """Test strategy performance calculation for SMA."""
        performance = analyzer._calculate_strategy_performance(
            test_data,
            fast_period=10,
            slow_period=20,
            strategy_type="SMA",
            strategy_config={"STRATEGY_TYPE": "SMA"},
        )

        assert isinstance(performance, dict)
        assert "total_return" in performance
        assert "sharpe_ratio" in performance
        assert "max_drawdown" in performance

        # Values should be finite numbers
        assert np.isfinite(performance["total_return"])
        assert np.isfinite(performance["sharpe_ratio"])
        assert np.isfinite(performance["max_drawdown"])

    def test_calculate_strategy_performance_ema(self, analyzer, test_data):
        """Test strategy performance calculation for EMA."""
        performance = analyzer._calculate_strategy_performance(
            test_data,
            fast_period=12,
            slow_period=26,
            strategy_type="EMA",
            strategy_config={"STRATEGY_TYPE": "EMA"},
        )

        assert isinstance(performance, dict)
        assert "total_return" in performance
        assert "sharpe_ratio" in performance
        assert "max_drawdown" in performance

    def test_calculate_strategy_performance_macd(self, analyzer, test_data):
        """Test strategy performance calculation for MACD."""
        macd_config = {"STRATEGY_TYPE": "MACD", "SIGNAL_PERIOD": 9}

        performance = analyzer._calculate_strategy_performance(
            test_data,
            fast_period=12,
            slow_period=26,
            strategy_type="MACD",
            strategy_config=macd_config,
        )

        assert isinstance(performance, dict)
        assert "total_return" in performance
        assert "sharpe_ratio" in performance
        assert "max_drawdown" in performance

    def test_calculate_strategy_performance_error_handling(self, analyzer):
        """Test error handling in performance calculation."""
        # Test with invalid data
        invalid_data = pl.DataFrame({"Close": []})

        performance = analyzer._calculate_strategy_performance(
            invalid_data, fast_period=10, slow_period=20, strategy_type="SMA",
        )

        # Should return default values on error
        assert performance["total_return"] == 0.0
        assert performance["sharpe_ratio"] == 0.0
        assert performance["max_drawdown"] == 1.0

    def test_confidence_interval_calculation(self, analyzer):
        """Test confidence interval calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        alpha = 0.1  # 90% confidence

        lower, upper = analyzer._calculate_confidence_interval(values, alpha)

        assert lower <= upper
        assert lower >= min(values)
        assert upper <= max(values)

    def test_confidence_interval_empty_values(self, analyzer):
        """Test confidence interval with empty values."""
        lower, upper = analyzer._calculate_confidence_interval([], 0.1)
        assert lower == 0.0
        assert upper == 0.0

    def test_analyze_single_parameter_combination(self, analyzer, test_data):
        """Test analysis of a single parameter combination."""
        result = analyzer._analyze_single_parameter_combination(
            test_data,
            fast_period=10,
            slow_period=20,
            strategy_type="SMA",
            strategy_config={"STRATEGY_TYPE": "SMA"},
        )

        assert isinstance(result, ParameterStabilityResult)
        assert result.parameter_combination == (10, 20)
        assert isinstance(result.base_performance, dict)
        assert len(result.monte_carlo_results) == analyzer.config.num_simulations

        # Check that stability metrics were calculated
        assert hasattr(result, "stability_score")
        assert hasattr(result, "parameter_robustness")
        assert hasattr(result, "regime_consistency")

    def test_analyze_parameter_stability_sma(self, analyzer, test_data):
        """Test full parameter stability analysis for SMA."""
        parameter_combinations = [(10, 20), (12, 26)]

        result = analyzer.analyze_parameter_stability(
            ticker="BTC-USD",
            data=test_data,
            parameter_combinations=parameter_combinations,
            strategy_type="SMA",
            strategy_config={"STRATEGY_TYPE": "SMA"},
        )

        assert isinstance(result, MonteCarloPortfolioResult)
        assert result.ticker == "BTC-USD"
        assert len(result.parameter_results) == 2
        assert result.portfolio_stability_score >= 0.0
        assert result.recommended_parameters in parameter_combinations

    def test_analyze_parameter_stability_macd(self, analyzer, test_data):
        """Test full parameter stability analysis for MACD."""
        parameter_combinations = [(12, 26), (14, 28)]
        macd_config = {"STRATEGY_TYPE": "MACD", "SIGNAL_PERIOD": 9}

        result = analyzer.analyze_parameter_stability(
            ticker="BTC-USD",
            data=test_data,
            parameter_combinations=parameter_combinations,
            strategy_type="MACD",
            strategy_config=macd_config,
        )

        assert isinstance(result, MonteCarloPortfolioResult)
        assert result.ticker == "BTC-USD"
        assert len(result.parameter_results) == 2
        assert "num_simulations" in result.analysis_metadata
        assert "confidence_level" in result.analysis_metadata

    def test_parameter_limit_enforcement(self, analyzer, test_data):
        """Test that parameter combinations are limited correctly."""
        # Create more parameters than the limit
        many_parameters = [(i, i + 10) for i in range(5, 20)]  # 15 combinations

        result = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=test_data,
            parameter_combinations=many_parameters,
            strategy_type="SMA",
        )

        # Should be limited to max_parameters_to_test (3 in test config)
        assert len(result.parameter_results) == analyzer.config.max_parameters_to_test

    def test_portfolio_stability_score_calculation(self, analyzer):
        """Test portfolio stability score calculation."""
        # Create mock parameter results
        param_results = [
            ParameterStabilityResult((10, 20), {}, []),
            ParameterStabilityResult((12, 26), {}, []),
        ]
        param_results[0].stability_score = 0.6
        param_results[1].stability_score = 0.8

        score = analyzer._calculate_portfolio_stability_score(param_results)
        expected_score = (0.6 + 0.8) / 2
        assert abs(score - expected_score) < 1e-6

    def test_select_most_stable_parameters(self, analyzer):
        """Test selection of most stable parameters."""
        param_results = [
            ParameterStabilityResult((10, 20), {}, []),
            ParameterStabilityResult((12, 26), {}, []),
        ]

        # Set different stability scores
        param_results[0].stability_score = 0.3
        param_results[0].parameter_robustness = 0.4
        param_results[0].regime_consistency = 0.2

        param_results[1].stability_score = 0.7
        param_results[1].parameter_robustness = 0.6
        param_results[1].regime_consistency = 0.8

        best_params = analyzer._select_most_stable_parameters(param_results)
        assert best_params == (12, 26)  # Second one should be better

    def test_select_most_stable_parameters_empty(self, analyzer):
        """Test selection with no parameters."""
        best_params = analyzer._select_most_stable_parameters([])
        assert best_params is None


class TestMonteCarloIntegration:
    """Test Monte Carlo integration scenarios."""

    def test_end_to_end_analysis(self):
        """Test complete end-to-end Monte Carlo analysis."""
        # Create realistic test scenario
        config = MonteCarloConfig(num_simulations=3, max_parameters_to_test=2)
        analyzer = MonteCarloAnalyzer(config=config)

        # Generate test data
        np.random.seed(42)
        n_days = 50
        dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_days)]
        prices = [100.0 + i * 0.2 + np.sin(i * 0.1) * 2 for i in range(n_days)]

        data = pl.DataFrame({"Date": dates, "Close": prices})

        # Test with multiple strategy types
        for strategy_type in ["SMA", "EMA", "MACD"]:
            strategy_config = {"STRATEGY_TYPE": strategy_type}
            if strategy_type == "MACD":
                strategy_config["SIGNAL_PERIOD"] = 9

            result = analyzer.analyze_parameter_stability(
                ticker=f"TEST-{strategy_type}",
                data=data,
                parameter_combinations=[(10, 20), (12, 26)],
                strategy_type=strategy_type,
                strategy_config=strategy_config,
            )

            assert isinstance(result, MonteCarloPortfolioResult)
            assert result.ticker == f"TEST-{strategy_type}"
            assert len(result.parameter_results) == 2
            assert result.portfolio_stability_score >= 0.0

    def test_bootstrap_sampling_consistency(self):
        """Test that bootstrap sampling produces consistent results."""
        config = MonteCarloConfig(num_simulations=5)
        analyzer = MonteCarloAnalyzer(config=config)

        # Create deterministic data
        data = pl.DataFrame(
            {
                "Date": [datetime(2023, 1, 1) + timedelta(days=i) for i in range(30)],
                "Close": [100.0 + i for i in range(30)],  # Linear trend
            },
        )

        # Run analysis twice with same seed
        np.random.seed(123)
        result1 = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        np.random.seed(123)
        result2 = analyzer.analyze_parameter_stability(
            ticker="TEST",
            data=data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        # Results should be similar (within tolerance due to randomness)
        assert (
            abs(result1.portfolio_stability_score - result2.portfolio_stability_score)
            < 0.1
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
