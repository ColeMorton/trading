"""
Unit tests for trend calculation methods in MarketDataAnalyzer.

Tests trend strength and direction metrics including moving averages,
trend consistency, and linear regression slope calculations.
"""

from unittest.mock import Mock

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.tools.market_data_analyzer import MarketDataAnalyzer


@pytest.mark.integration
class TestTrendMetricsCalculation:
    """Test trend metrics calculation functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    @pytest.fixture
    def uptrend_data(self):
        """Create price data showing clear uptrend."""
        dates = pd.date_range("2023-01-01", periods=250, freq="D")
        # Generate uptrending prices
        base_price = 100
        trend_component = np.linspace(0, 50, 250)  # 50% gain over period
        noise = np.random.normal(0, 2, 250)
        prices = base_price + trend_component + noise

        return pl.DataFrame({"Date": dates, "Close": prices})

    @pytest.fixture
    def downtrend_data(self):
        """Create price data showing clear downtrend."""
        dates = pd.date_range("2023-01-01", periods=250, freq="D")
        # Generate downtrending prices
        base_price = 100
        trend_component = np.linspace(0, -30, 250)  # 30% decline over period
        noise = np.random.normal(0, 1.5, 250)
        prices = base_price + trend_component + noise

        return pl.DataFrame({"Date": dates, "Close": prices})

    @pytest.fixture
    def sideways_data(self):
        """Create price data showing sideways movement."""
        dates = pd.date_range("2023-01-01", periods=250, freq="D")
        # Generate sideways prices with mean reversion
        base_price = 100
        noise = np.random.normal(0, 3, 250)
        prices = [base_price]

        for i in range(1, 250):
            # Mean reversion toward base price
            mean_reversion = (base_price - prices[-1]) * 0.05
            new_price = prices[-1] + mean_reversion + noise[i]
            prices.append(new_price)

        return pl.DataFrame({"Date": dates, "Close": prices})

    def test_trend_metrics_insufficient_data(self, analyzer):
        """Test trend metrics with insufficient data."""
        # Create data with only 10 points (less than 20 required)
        short_data = pl.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=10),
                "Close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            },
        )

        analyzer.price_data = short_data

        result = analyzer._calculate_trend_metrics()

        # Should return default values
        expected_defaults = analyzer._default_trend_metrics()
        assert result == expected_defaults

    def test_trend_metrics_no_data(self, analyzer):
        """Test trend metrics with no price data."""
        analyzer.price_data = None

        result = analyzer._calculate_trend_metrics()

        # Should return default values
        expected_defaults = analyzer._default_trend_metrics()
        assert result == expected_defaults


@pytest.mark.integration
class TestMovingAverageCalculations:
    """Test moving average calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_moving_averages_short_series(self, analyzer):
        """Test moving averages with series shorter than MA periods."""
        # Only 30 data points
        prices = list(range(100, 130))
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=len(prices)), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # MA_20 should use last 20 points
        expected_ma_20 = np.mean(prices[-20:])
        assert abs(result["ma_20"] - expected_ma_20) < 1e-10

        # MA_50 should fall back to MA_20 (insufficient data)
        assert result["ma_50"] == result["ma_20"]

        # MA_200 should fall back to MA_50
        assert result["ma_200"] == result["ma_50"]


@pytest.mark.integration
class TestTrendDirectionCalculations:
    """Test trend direction calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_direction_below_ma(self, analyzer):
        """Test trend direction when price is below moving averages."""
        # Create data where current price is 10% below the average
        base_prices = [100] * 49 + [90]  # 49 prices at 100, last at 90
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=50), "Close": base_prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should be negative (price below MA)
        assert result["trend_direction_20d"] < 0


@pytest.mark.integration
class TestTrendConsistencyCalculations:
    """Test trend consistency calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_consistency_mixed(self, analyzer):
        """Test trend consistency with mixed signals."""
        # Create data with half above, half below MA
        prices = [
            98,
            102,
            99,
            101,
            97,
            103,
            100,
            100,
            99,
            101,
            102,
            98,
            101,
            99,
            103,
            97,
            100,
            100,
            101,
            99,
        ]

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should be around 0.5 for mixed signals
        assert 0.3 < result["trend_consistency"] < 0.7


@pytest.mark.integration
class TestTrendSlopeCalculations:
    """Test trend slope calculations using linear regression."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_slope_positive(self, analyzer):
        """Test trend slope with positive trend."""
        # Create linear uptrend
        prices = [100 + i for i in range(20)]  # 100, 101, 102, ..., 119

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should detect positive slope
        assert result["trend_slope"] > 0

    def test_trend_slope_negative(self, analyzer):
        """Test trend slope with negative trend."""
        # Create linear downtrend
        prices = [120 - i for i in range(20)]  # 120, 119, 118, ..., 101

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should detect negative slope
        assert result["trend_slope"] < 0

    def test_trend_slope_flat(self, analyzer):
        """Test trend slope with flat trend."""
        # Create flat prices
        prices = [100] * 20

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should detect near-zero slope
        assert abs(result["trend_slope"]) < 1e-10


@pytest.mark.integration
class TestTrendIntegration:
    """Test trend calculation integration with other components."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_in_full_analysis(self, analyzer):
        """Test that trend metrics are included in distribution analysis."""
        # Create sample data
        prices = [100 + i + np.random.normal(0, 0.5) for i in range(252)]
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=252), "Close": prices},
        )

        analyzer.price_data = data

        # Set up returns for distribution analysis
        close_prices = data.select("Close").to_pandas()["Close"].values
        returns = np.diff(close_prices) / close_prices[:-1]
        analyzer.returns = returns

        result = analyzer.analyze_distribution()

        # Verify trend metrics are included
        trend_keys = [
            "trend_direction_20d",
            "trend_direction_50d",
            "trend_direction_200d",
            "trend_consistency",
            "trend_slope",
            "ma_20",
            "ma_50",
            "ma_200",
            "current_price",
        ]

        for key in trend_keys:
            assert key in result
            assert isinstance(result[key], int | float)
            assert not np.isnan(result[key])


if __name__ == "__main__":
    pytest.main([__file__])
