"""
Unit tests for momentum calculation methods in MarketDataAnalyzer.

Tests momentum-based metrics for trend identification including
recent vs historical performance, rolling momentum, and price acceleration.
"""

from unittest.mock import Mock

import numpy as np
import pytest

from app.tools.market_data_analyzer import MarketDataAnalyzer


class TestMomentumMetricsCalculation:
    """Test momentum metrics calculation functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    @pytest.fixture
    def uptrend_returns(self):
        """Create returns data showing upward trend."""
        # Recent returns higher than historical
        historical = np.random.normal(0.0005, 0.015, 200)  # Slight positive drift
        recent = np.random.normal(0.002, 0.015, 50)  # Higher recent performance
        return np.concatenate([historical, recent])

    @pytest.fixture
    def downtrend_returns(self):
        """Create returns data showing downward trend."""
        # Recent returns lower than historical
        historical = np.random.normal(0.001, 0.015, 200)  # Positive historical
        recent = np.random.normal(-0.001, 0.015, 50)  # Negative recent
        return np.concatenate([historical, recent])

    @pytest.fixture
    def sideways_returns(self):
        """Create returns data showing sideways movement."""
        return np.random.normal(0.0, 0.015, 250)  # No trend

    def test_momentum_metrics_uptrend(self, analyzer, uptrend_returns):
        """Test momentum metrics with uptrending data."""
        result = analyzer._calculate_momentum_metrics(uptrend_returns)

        # Verify expected structure
        assert isinstance(result, dict)
        assert "momentum_differential" in result
        assert "recent_avg_return" in result
        assert "historical_avg_return" in result
        assert "momentum_5d" in result
        assert "momentum_20d" in result
        assert "momentum_60d" in result
        assert "price_acceleration" in result

        # For uptrend, recent should be higher than historical
        assert result["momentum_differential"] > 0
        assert result["recent_avg_return"] > result["historical_avg_return"]

        # All values should be numeric
        for _key, value in result.items():
            assert isinstance(value, int | float)
            assert not np.isnan(value)

    def test_momentum_metrics_downtrend(self, analyzer, downtrend_returns):
        """Test momentum metrics with downtrending data."""
        result = analyzer._calculate_momentum_metrics(downtrend_returns)

        # For downtrend, recent should be lower than historical
        assert result["momentum_differential"] < 0
        assert result["recent_avg_return"] < result["historical_avg_return"]

    def test_momentum_metrics_sideways(self, analyzer, sideways_returns):
        """Test momentum metrics with sideways movement."""
        result = analyzer._calculate_momentum_metrics(sideways_returns)

        # For sideways movement, differential should be close to zero
        assert abs(result["momentum_differential"]) < 0.001
        assert abs(result["recent_avg_return"]) < 0.001
        assert abs(result["historical_avg_return"]) < 0.001

    def test_momentum_metrics_short_series(self, analyzer):
        """Test momentum metrics with short data series."""
        short_returns = np.array([0.01, -0.005, 0.02])

        result = analyzer._calculate_momentum_metrics(short_returns)

        # Should handle short series gracefully
        assert isinstance(result, dict)
        assert all(
            key in result
            for key in [
                "momentum_differential",
                "recent_avg_return",
                "historical_avg_return",
                "momentum_5d",
                "momentum_20d",
                "momentum_60d",
                "price_acceleration",
            ]
        )

    def test_momentum_metrics_single_value(self, analyzer):
        """Test momentum metrics with single return value."""
        single_return = np.array([0.01])

        result = analyzer._calculate_momentum_metrics(single_return)

        # Should handle edge case
        assert isinstance(result, dict)
        # With single value, recent and historical should be the same
        assert result["recent_avg_return"] == result["historical_avg_return"]

    def test_momentum_metrics_empty_array(self, analyzer):
        """Test momentum metrics with empty returns array."""
        empty_returns = np.array([])

        result = analyzer._calculate_momentum_metrics(empty_returns)

        # Should return default values
        assert result["momentum_differential"] == 0.0
        assert result["recent_avg_return"] == 0.0
        assert result["historical_avg_return"] == 0.0


class TestRollingMomentumCalculation:
    """Test rolling momentum calculation method."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_rolling_momentum_sufficient_data(self, analyzer):
        """Test rolling momentum with sufficient data."""
        returns = np.array(
            [0.01, 0.02, -0.005, 0.015, 0.008, 0.012, -0.003, 0.01, 0.005, 0.02]
        )

        # Test 5-day momentum
        result_5d = analyzer._rolling_momentum(returns, 5)
        expected_5d = np.mean(returns[-5:])

        assert abs(result_5d - expected_5d) < 1e-10
        assert isinstance(result_5d, float)

    def test_rolling_momentum_insufficient_data(self, analyzer):
        """Test rolling momentum with insufficient data."""
        short_returns = np.array([0.01, 0.02])

        # Request 5-day momentum but only have 2 data points
        result = analyzer._rolling_momentum(short_returns, 5)

        assert result == 0.0

    def test_rolling_momentum_exact_window(self, analyzer):
        """Test rolling momentum with exact window size."""
        returns = np.array([0.01, 0.02, 0.015, 0.008, 0.012])

        result = analyzer._rolling_momentum(returns, 5)
        expected = np.mean(returns)

        assert abs(result - expected) < 1e-10

    def test_rolling_momentum_different_windows(self, analyzer):
        """Test rolling momentum with different window sizes."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 100)

        result_5d = analyzer._rolling_momentum(returns, 5)
        result_20d = analyzer._rolling_momentum(returns, 20)
        result_60d = analyzer._rolling_momentum(returns, 60)

        # All should be valid numbers
        assert isinstance(result_5d, float)
        assert isinstance(result_20d, float)
        assert isinstance(result_60d, float)

        # Should not be NaN
        assert not np.isnan(result_5d)
        assert not np.isnan(result_20d)
        assert not np.isnan(result_60d)


class TestPriceAcceleration:
    """Test price acceleration calculation within momentum metrics."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_acceleration_accelerating_trend(self, analyzer):
        """Test acceleration with accelerating uptrend."""
        # Create returns that show increasing momentum
        returns = np.array(
            [
                0.005,
                0.006,
                0.008,
                0.010,
                0.013,
                0.016,
                0.020,
                0.025,
                0.030,
                0.035,
                0.040,
                0.045,
            ]
        )

        result = analyzer._calculate_momentum_metrics(returns)

        # Should detect positive acceleration
        assert result["price_acceleration"] > 0

    def test_acceleration_decelerating_trend(self, analyzer):
        """Test acceleration with decelerating trend."""
        # Create returns that show decreasing momentum
        returns = np.array(
            [
                0.040,
                0.035,
                0.030,
                0.025,
                0.020,
                0.016,
                0.013,
                0.010,
                0.008,
                0.006,
                0.005,
                0.004,
            ]
        )

        result = analyzer._calculate_momentum_metrics(returns)

        # Should detect negative acceleration (deceleration)
        assert result["price_acceleration"] < 0

    def test_acceleration_constant_trend(self, analyzer):
        """Test acceleration with constant trend."""
        # Create returns with constant momentum
        constant_return = 0.01
        returns = np.array([constant_return] * 20)

        result = analyzer._calculate_momentum_metrics(returns)

        # Should detect near-zero acceleration
        assert abs(result["price_acceleration"]) < 0.001

    def test_acceleration_insufficient_data(self, analyzer):
        """Test acceleration calculation with insufficient data."""
        short_returns = np.array([0.01, 0.02])

        result = analyzer._calculate_momentum_metrics(short_returns)

        # Should handle gracefully and return zero
        assert result["price_acceleration"] == 0.0


class TestMomentumErrorHandling:
    """Test error handling in momentum calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_momentum_with_nan_values(self, analyzer):
        """Test momentum calculation with NaN values."""
        returns_with_nan = np.array([0.01, np.nan, 0.02, 0.015, np.nan, 0.008])

        result = analyzer._calculate_momentum_metrics(returns_with_nan)

        # Should handle NaN values and return valid numbers
        assert isinstance(result, dict)
        for _key, value in result.items():
            assert isinstance(value, int | float)
            # Results should either be valid numbers or default zeros
            assert not np.isnan(value) or value == 0.0

    def test_momentum_with_infinite_values(self, analyzer):
        """Test momentum calculation with infinite values."""
        returns_with_inf = np.array([0.01, np.inf, 0.02, -np.inf, 0.015])

        result = analyzer._calculate_momentum_metrics(returns_with_inf)

        # Should handle infinite values gracefully
        assert isinstance(result, dict)
        for _key, value in result.items():
            assert np.isfinite(value) or value == 0.0

    def test_momentum_calculation_exception(self, analyzer):
        """Test momentum calculation when exception occurs."""
        # Mock the logger to verify error logging
        analyzer.logger = Mock()

        # This should trigger the exception handling
        with pytest.patch.object(
            analyzer, "_rolling_momentum", side_effect=Exception("Test error")
        ):
            result = analyzer._calculate_momentum_metrics(np.array([0.01, 0.02, 0.03]))

        # Should return default values when exception occurs
        expected_defaults = {
            "momentum_differential": 0.0,
            "recent_avg_return": 0.0,
            "historical_avg_return": 0.0,
            "momentum_5d": 0.0,
            "momentum_20d": 0.0,
            "momentum_60d": 0.0,
            "price_acceleration": 0.0,
        }

        assert result == expected_defaults
        analyzer.logger.warning.assert_called_once()


class TestMomentumIntegration:
    """Test momentum calculation integration with other components."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_momentum_in_full_analysis(self, analyzer):
        """Test that momentum metrics are included in distribution analysis."""
        # Set up returns data
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        analyzer.returns = returns

        result = analyzer.analyze_distribution()

        # Verify momentum metrics are included
        assert "momentum_differential" in result
        assert "recent_avg_return" in result
        assert "momentum_5d" in result
        assert "momentum_20d" in result
        assert "momentum_60d" in result
        assert "price_acceleration" in result

        # Verify all momentum values are numeric
        momentum_keys = [
            "momentum_differential",
            "recent_avg_return",
            "historical_avg_return",
            "momentum_5d",
            "momentum_20d",
            "momentum_60d",
            "price_acceleration",
        ]

        for key in momentum_keys:
            if key in result:
                assert isinstance(result[key], int | float)
                assert not np.isnan(result[key])


if __name__ == "__main__":
    pytest.main([__file__])
