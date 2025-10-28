"""
Comprehensive tests for Monte Carlo configuration and error handling.

This test suite covers configuration validation, error handling,
bootstrap sampling configuration, and edge cases in Monte Carlo analysis.
"""

from pathlib import Path
import sys

import numpy as np
import polars as pl
import pytest


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.bootstrap import (
    BootstrapSampler,
    create_bootstrap_sampler,
)
from app.concurrency.tools.monte_carlo.config import (
    MonteCarloConfig,
    create_monte_carlo_config,
)
from app.concurrency.tools.monte_carlo.core import MonteCarloAnalyzer


class TestMonteCarloConfig:
    """Test Monte Carlo configuration handling."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = MonteCarloConfig()

        assert config.num_simulations == 100
        assert config.confidence_level == 0.95
        assert config.max_parameters_to_test == 10
        assert config.include_in_reports is False

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = MonteCarloConfig(
            num_simulations=50,
            confidence_level=0.99,
            max_parameters_to_test=5,
            include_in_reports=True,
        )

        assert config.num_simulations == 50
        assert config.confidence_level == 0.99
        assert config.max_parameters_to_test == 5
        assert config.include_in_reports is True

    def test_configuration_validation(self):
        """Test configuration parameter validation via validate method."""
        # Test that validation normalizes extreme values
        config = MonteCarloConfig(
            num_simulations=5000,  # Too high
            confidence_level=1.5,  # Too high
            max_parameters_to_test=100,  # Too high
        )

        validated_config = config.validate()

        # Should be clamped to reasonable values
        assert validated_config.num_simulations <= 1000
        assert validated_config.confidence_level <= 0.999
        assert validated_config.max_parameters_to_test <= 50

        # Test lower bounds
        config = MonteCarloConfig(
            num_simulations=1,  # Too low
            confidence_level=0.1,  # Too low
            max_parameters_to_test=0,  # Too low
        )

        validated_config = config.validate()

        assert validated_config.num_simulations >= 10
        assert validated_config.confidence_level >= 0.5
        assert validated_config.max_parameters_to_test >= 1

    def test_configuration_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = MonteCarloConfig(
            num_simulations=25,
            confidence_level=0.90,
            max_parameters_to_test=3,
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["MC_NUM_SIMULATIONS"] == 25
        assert config_dict["MC_CONFIDENCE_LEVEL"] == 0.90
        assert config_dict["MC_MAX_PARAMETERS_TO_TEST"] == 3
        assert "MC_INCLUDE_IN_REPORTS" in config_dict

    def test_create_monte_carlo_config_from_dict(self):
        """Test creating configuration from dictionary."""
        input_config = {
            "MC_NUM_SIMULATIONS": 75,
            "MC_CONFIDENCE_LEVEL": 0.99,
            "MC_MAX_PARAMETERS_TO_TEST": 8,
            "MC_INCLUDE_IN_REPORTS": True,
        }

        config = create_monte_carlo_config(input_config)

        assert config.num_simulations == 75
        assert config.confidence_level == 0.99
        assert config.max_parameters_to_test == 8
        assert config.include_in_reports is True

    def test_create_monte_carlo_config_with_defaults(self):
        """Test creating configuration with partial input (using defaults)."""
        input_config = {"MC_NUM_SIMULATIONS": 30}

        config = create_monte_carlo_config(input_config)

        assert config.num_simulations == 30
        assert config.confidence_level == 0.95  # Default
        assert config.max_parameters_to_test == 10  # Default

    def test_create_monte_carlo_config_empty_dict(self):
        """Test creating configuration from empty dictionary."""
        config = create_monte_carlo_config({})

        # Should use all defaults
        assert config.num_simulations == 100
        assert config.confidence_level == 0.95
        assert config.max_parameters_to_test == 10


class TestBootstrapConfiguration:
    """Test bootstrap sampling configuration."""

    def test_create_bootstrap_sampler_default(self):
        """Test creating bootstrap sampler with default configuration."""
        config = {}
        sampler = create_bootstrap_sampler(config)

        assert isinstance(sampler, BootstrapSampler)
        assert sampler.block_size == 63  # Default block size
        assert sampler.min_data_fraction == 0.7  # Default fraction

    def test_create_bootstrap_sampler_custom(self):
        """Test creating bootstrap sampler with custom configuration."""
        config = {"MC_BOOTSTRAP_BLOCK_SIZE": 30, "MC_MIN_DATA_FRACTION": 0.5}

        sampler = create_bootstrap_sampler(config)

        assert sampler.block_size == 30
        assert sampler.min_data_fraction == 0.5

    def test_bootstrap_sampler_validation(self):
        """Test bootstrap sampler parameter handling."""
        # Test that bootstrap sampler handles edge case values gracefully
        config = {"MC_BOOTSTRAP_BLOCK_SIZE": 0}
        sampler = create_bootstrap_sampler(config)
        assert sampler.block_size == 0  # Should accept but may be handled in usage

        config = {"MC_MIN_DATA_FRACTION": 0.0}
        sampler = create_bootstrap_sampler(config)
        assert sampler.min_data_fraction == 0.0

        config = {"MC_MIN_DATA_FRACTION": 1.1}
        sampler = create_bootstrap_sampler(config)
        assert sampler.min_data_fraction == 1.1  # Will be handled during sampling


class TestMonteCarloErrorHandling:
    """Test error handling in Monte Carlo analysis."""

    @pytest.fixture
    def minimal_data(self):
        """Create minimal test data."""
        return pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2)],
                "Close": [100.0, 101.0],
            },
        )

    @pytest.fixture
    def empty_data(self):
        """Create empty test data."""
        return pl.DataFrame({"Date": [], "Close": []})

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with minimal configuration."""
        config = MonteCarloConfig(num_simulations=2, max_parameters_to_test=1)
        return MonteCarloAnalyzer(config=config)

    def test_empty_data_handling(self, analyzer, empty_data):
        """Test handling of empty data."""
        result = analyzer.analyze_parameter_stability(
            ticker="EMPTY",
            data=empty_data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        # Should handle gracefully and return result with zero performance
        assert result.ticker == "EMPTY"
        assert len(result.parameter_results) == 1

        param_result = result.parameter_results[0]
        # Performance should be zero or default values
        assert param_result.base_performance["total_return"] == 0.0

    def test_minimal_data_handling(self, analyzer, minimal_data):
        """Test handling of minimal data."""
        result = analyzer.analyze_parameter_stability(
            ticker="MINIMAL",
            data=minimal_data,
            parameter_combinations=[(1, 2)],  # Very small windows
            strategy_type="SMA",
        )

        # Should handle gracefully
        assert result.ticker == "MINIMAL"
        assert len(result.parameter_results) == 1

    def test_invalid_parameter_combinations(self, analyzer):
        """Test handling of invalid parameter combinations."""
        # Create valid data
        data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )

        # Test windows larger than data
        result = analyzer.analyze_parameter_stability(
            ticker="INVALID",
            data=data,
            parameter_combinations=[(10, 20)],  # Windows larger than data
            strategy_type="SMA",
        )

        # Should handle gracefully
        assert result.ticker == "INVALID"
        assert len(result.parameter_results) == 1

    def test_missing_required_columns(self, analyzer):
        """Test handling of data missing required columns."""
        # Data without Close column
        invalid_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2)],
                "Price": [100.0, 101.0],  # Wrong column name
            },
        )

        # Should handle gracefully and return zero performance
        result = analyzer.analyze_parameter_stability(
            ticker="INVALID_COLS",
            data=invalid_data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        # Should return result with zero performance
        assert result.ticker == "INVALID_COLS"
        param_result = result.parameter_results[0]
        assert param_result.base_performance["total_return"] == 0.0

    def test_invalid_strategy_configuration(self, analyzer):
        """Test handling of invalid strategy configuration."""
        data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )

        # Test MACD without signal period
        invalid_macd_config = {
            "STRATEGY_TYPE": "MACD",
            # Missing SIGNAL_PERIOD
        }

        # Should either handle gracefully or raise appropriate error
        try:
            result = analyzer.analyze_parameter_stability(
                ticker="INVALID_CONFIG",
                data=data,
                parameter_combinations=[(5, 10)],
                strategy_type="MACD",
                strategy_config=invalid_macd_config,
            )
            # If it succeeds, should have valid structure
            assert result.ticker == "INVALID_CONFIG"
        except ValueError as e:
            # Should be a meaningful error message
            assert "signal" in str(e).lower() or "window" in str(e).lower()

    def test_zero_confidence_level(self):
        """Test handling of edge case confidence levels."""
        # Very high confidence level (close to 1.0)
        config = MonteCarloConfig(confidence_level=0.999)
        analyzer = MonteCarloAnalyzer(config=config)

        # Should work without issues
        assert analyzer.config.confidence_level == 0.999

    def test_extreme_simulation_counts(self):
        """Test handling of extreme simulation counts."""
        # Very few simulations
        config = MonteCarloConfig(num_simulations=1)
        analyzer = MonteCarloAnalyzer(config=config)

        assert analyzer.config.num_simulations == 1

        # Very many simulations
        config = MonteCarloConfig(num_simulations=1000)
        analyzer = MonteCarloAnalyzer(config=config)

        assert analyzer.config.num_simulations == 1000

    def test_logging_integration(self):
        """Test that logging works properly."""
        log_messages = []

        def capture_log(message, level):
            log_messages.append((message, level))

        config = MonteCarloConfig(num_simulations=2)
        analyzer = MonteCarloAnalyzer(config=config, log=capture_log)

        # Create simple test data
        data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )

        analyzer.analyze_parameter_stability(
            ticker="LOG_TEST",
            data=data,
            parameter_combinations=[(1, 2)],
            strategy_type="SMA",
        )

        # Should have captured some log messages
        assert len(log_messages) > 0

        # Check for expected log messages
        messages = [msg for msg, level in log_messages]
        assert any("Starting Monte Carlo analysis" in msg for msg in messages)
        assert any("Completed Monte Carlo analysis" in msg for msg in messages)


class TestMonteCarloEdgeCases:
    """Test edge cases in Monte Carlo analysis."""

    def test_identical_parameter_combinations(self):
        """Test handling of duplicate parameter combinations."""
        config = MonteCarloConfig(num_simulations=2)
        analyzer = MonteCarloAnalyzer(config=config)

        data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )

        # Test with duplicate parameters
        result = analyzer.analyze_parameter_stability(
            ticker="DUPLICATE",
            data=data,
            parameter_combinations=[(5, 10), (5, 10), (5, 10)],  # Duplicates
            strategy_type="SMA",
        )

        # Should handle gracefully
        assert result.ticker == "DUPLICATE"
        assert len(result.parameter_results) >= 1

    def test_single_parameter_combination(self):
        """Test analysis with only one parameter combination."""
        config = MonteCarloConfig(num_simulations=3)
        analyzer = MonteCarloAnalyzer(config=config)

        data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )

        result = analyzer.analyze_parameter_stability(
            ticker="SINGLE",
            data=data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        assert result.ticker == "SINGLE"
        assert len(result.parameter_results) == 1
        assert result.recommended_parameters == (5, 10)

    def test_constant_price_data(self):
        """Test analysis with constant price data (no volatility)."""
        config = MonteCarloConfig(num_simulations=3)
        analyzer = MonteCarloAnalyzer(config=config)

        # Create constant price data
        constant_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(20)],
                "Close": [100.0] * 20,  # Constant price
            },
        )

        result = analyzer.analyze_parameter_stability(
            ticker="CONSTANT",
            data=constant_data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        # Should handle gracefully - no returns expected
        assert result.ticker == "CONSTANT"
        param_result = result.parameter_results[0]
        assert param_result.base_performance["total_return"] == 0.0

    def test_highly_volatile_data(self):
        """Test analysis with highly volatile data."""
        config = MonteCarloConfig(num_simulations=3)
        analyzer = MonteCarloAnalyzer(config=config)

        # Create highly volatile data
        np.random.seed(42)
        n_days = 30
        prices = [100.0]
        for _i in range(n_days - 1):
            # Extreme volatility (±50% daily moves)
            change = np.random.choice([-0.5, 0.5])
            new_price = max(prices[-1] * (1 + change), 1.0)  # Prevent negative
            prices.append(new_price)

        volatile_data = pl.DataFrame(
            {
                "Date": [
                    pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(n_days)
                ],
                "Close": prices,
            },
        )

        result = analyzer.analyze_parameter_stability(
            ticker="VOLATILE",
            data=volatile_data,
            parameter_combinations=[(5, 10)],
            strategy_type="SMA",
        )

        # Should handle extreme volatility
        assert result.ticker == "VOLATILE"
        param_result = result.parameter_results[0]

        # May have extreme returns but should be finite
        assert np.isfinite(param_result.base_performance["total_return"])
        assert np.isfinite(param_result.base_performance["max_drawdown"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
