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

    def test_trend_metrics_uptrend(self, analyzer, uptrend_data):
        """Test trend metrics with uptrending data."""
        analyzer.price_data = uptrend_data

        result = analyzer._calculate_trend_metrics()

        # Verify expected structure
        assert isinstance(result, dict)
        expected_keys = [
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

        for key in expected_keys:
            assert key in result
            assert isinstance(result[key], int | float)
            assert not np.isnan(result[key])

        # For uptrend, current price should be above moving averages
        assert result["current_price"] > result["ma_20"]
        assert result["trend_direction_20d"] > 0
        assert result["trend_direction_50d"] > 0

        # Trend consistency should favor upward movement
        assert result["trend_consistency"] > 0.5

        # Trend slope should be positive
        assert result["trend_slope"] > 0

    def test_trend_metrics_downtrend(self, analyzer, downtrend_data):
        """Test trend metrics with downtrending data."""
        analyzer.price_data = downtrend_data

        result = analyzer._calculate_trend_metrics()

        # For downtrend, current price should be below moving averages
        assert result["current_price"] < result["ma_20"]
        assert result["trend_direction_20d"] < 0
        assert result["trend_direction_50d"] < 0

        # Trend consistency should favor downward movement
        assert result["trend_consistency"] < 0.5

        # Trend slope should be negative
        assert result["trend_slope"] < 0

    def test_trend_metrics_sideways(self, analyzer, sideways_data):
        """Test trend metrics with sideways movement."""
        analyzer.price_data = sideways_data

        result = analyzer._calculate_trend_metrics()

        # For sideways movement, trend directions should be small
        assert abs(result["trend_direction_20d"]) < 0.1
        assert abs(result["trend_direction_50d"]) < 0.1

        # Trend consistency should be around 0.5
        assert 0.3 < result["trend_consistency"] < 0.7

        # Trend slope should be close to zero
        assert abs(result["trend_slope"]) < 0.01

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


class TestMovingAverageCalculations:
    """Test moving average calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_moving_averages_calculation(self, analyzer):
        """Test moving average calculations with known data."""
        # Create data where we can verify MA calculations
        prices = list(range(100, 300))  # 200 data points: 100, 101, 102, ..., 299
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=len(prices)), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Verify 20-day MA (last 20 prices: 280-299)
        expected_ma_20 = np.mean(prices[-20:])
        assert abs(result["ma_20"] - expected_ma_20) < 1e-10

        # Verify 50-day MA (last 50 prices: 250-299)
        expected_ma_50 = np.mean(prices[-50:])
        assert abs(result["ma_50"] - expected_ma_50) < 1e-10

        # Verify 200-day MA (all prices: 100-299)
        expected_ma_200 = np.mean(prices[-200:])
        assert abs(result["ma_200"] - expected_ma_200) < 1e-10

        # Verify current price
        assert result["current_price"] == prices[-1]

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


class TestTrendDirectionCalculations:
    """Test trend direction calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_direction_above_ma(self, analyzer):
        """Test trend direction when price is above moving averages."""
        # Create data where current price is 10% above the average
        base_prices = [100] * 49 + [110]  # 49 prices at 100, last at 110
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=50), "Close": base_prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Current price (110) vs MA_20 (should be close to 100)
        expected_direction = (110 - result["ma_20"]) / result["ma_20"]
        assert abs(result["trend_direction_20d"] - expected_direction) < 1e-10

        # Should be positive (price above MA)
        assert result["trend_direction_20d"] > 0

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

    def test_trend_direction_equal_ma(self, analyzer):
        """Test trend direction when price equals moving average."""
        # Create data where current price equals the average
        base_prices = [100] * 50
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=50), "Close": base_prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Should be zero (price equals MA)
        assert abs(result["trend_direction_20d"]) < 1e-10


class TestTrendConsistencyCalculations:
    """Test trend consistency calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_consistency_strong_uptrend(self, analyzer):
        """Test trend consistency with strong uptrend."""
        # Create data where price is above MA for all 20 days
        ma_20 = 100
        prices = [ma_20 + 1] * 20  # All prices above MA

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # All days above MA, so consistency should be 1.0
        assert result["trend_consistency"] == 1.0

    def test_trend_consistency_strong_downtrend(self, analyzer):
        """Test trend consistency with strong downtrend."""
        # Create data where price is below MA for all 20 days
        base_prices = [105] * 19 + [95]  # MA will be ~105, last price is 95

        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=20), "Close": base_prices},
        )

        analyzer.price_data = data

        result = analyzer._calculate_trend_metrics()

        # Most days below MA, so consistency should be low
        assert result["trend_consistency"] < 0.5

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


class TestTrendErrorHandling:
    """Test error handling in trend calculations."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_trend_with_nan_prices(self, analyzer):
        """Test trend calculation with NaN prices."""
        prices = [100, np.nan, 102, 103, np.nan, 105]
        data = pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=len(prices)), "Close": prices},
        )

        analyzer.price_data = data

        # Should either handle gracefully or return defaults
        result = analyzer._calculate_trend_metrics()

        assert isinstance(result, dict)
        # If calculation fails, should return defaults
        if result == analyzer._default_trend_metrics():
            assert True  # Expected behavior
        else:
            # If calculation succeeds, verify no NaN values
            for value in result.values():
                assert not np.isnan(value)

    def test_trend_calculation_exception(self, analyzer):
        """Test trend calculation when exception occurs."""
        # Mock the logger
        analyzer.logger = Mock()

        # Create data that might cause issues
        problematic_data = pl.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=20),
                "Close": [0] * 20,  # Zero prices might cause division by zero
            },
        )

        analyzer.price_data = problematic_data

        result = analyzer._calculate_trend_metrics()

        # Should return default values or handle gracefully
        assert isinstance(result, dict)
        for value in result.values():
            assert isinstance(value, int | float)

    def test_default_trend_metrics(self, analyzer):
        """Test default trend metrics structure."""
        defaults = analyzer._default_trend_metrics()

        expected_keys = [
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

        for key in expected_keys:
            assert key in defaults
            assert defaults[key] == 0.0


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
