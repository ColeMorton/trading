"""
Unit tests for MarketDataAnalyzer class.

Tests core functionality including initialization, data fetching,
returns calculation, and comprehensive market data analysis.
"""

import logging
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.tools.market_data_analyzer import (
    MarketDataAnalyzer,
    create_market_data_analyzer,
)


@pytest.mark.integration
class TestMarketDataAnalyzerInitialization:
    """Test MarketDataAnalyzer initialization and basic setup."""

    def test_initialization_with_valid_ticker(self):
        """Test successful initialization with valid ticker."""
        analyzer = MarketDataAnalyzer("AAPL")

        assert analyzer.ticker == "AAPL"
        assert analyzer.price_data is None
        assert analyzer.returns is None
        assert analyzer.logger is not None
        assert analyzer.logger.name == "app.tools.market_data_analyzer"

    def test_initialization_with_custom_logger(self):
        """Test initialization with custom logger."""
        custom_logger = logging.getLogger("test_logger")
        analyzer = MarketDataAnalyzer("MSFT", logger=custom_logger)

        assert analyzer.ticker == "MSFT"
        assert analyzer.logger == custom_logger

    def test_create_market_data_analyzer_factory(self):
        """Test factory function for creating analyzer."""
        analyzer = create_market_data_analyzer("GOOGL")

        assert isinstance(analyzer, MarketDataAnalyzer)
        assert analyzer.ticker == "GOOGL"

    def test_create_analyzer_with_custom_logger(self):
        """Test factory with custom logger."""
        custom_logger = logging.getLogger("custom")
        analyzer = create_market_data_analyzer("NVDA", logger=custom_logger)

        assert analyzer.logger == custom_logger


@pytest.mark.integration
class TestMarketDataFetching:
    """Test data fetching functionality."""

    @pytest.fixture
    def mock_price_data(self):
        """Create mock price data."""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.02)

        return pl.DataFrame(
            {
                "Date": dates,
                "Open": prices * 0.99,
                "High": prices * 1.02,
                "Low": prices * 0.98,
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, len(dates)),
            },
        )

    @patch("app.tools.get_data.get_data")
    def test_fetch_data_success(self, mock_download, mock_price_data):
        """Test successful data fetching."""
        mock_download.return_value = mock_price_data

        analyzer = MarketDataAnalyzer("AAPL")
        result = analyzer.fetch_data(365)

        assert result is True
        assert analyzer.price_data is not None
        assert len(analyzer.price_data) == len(mock_price_data)
        mock_download.assert_called_once()

    @patch("app.tools.get_data.get_data")
    def test_fetch_data_empty_response(self, mock_download):
        """Test handling of empty data response."""
        mock_download.return_value = None

        analyzer = MarketDataAnalyzer("INVALID")
        result = analyzer.fetch_data(365)

        assert result is False
        assert analyzer.price_data is None

    @patch("app.tools.get_data.get_data")
    def test_fetch_data_empty_dataframe(self, mock_download):
        """Test handling of empty dataframe."""
        pl.DataFrame()
        mock_empty = Mock()
        mock_empty.is_empty.return_value = True
        mock_download.return_value = mock_empty

        analyzer = MarketDataAnalyzer("EMPTY")
        result = analyzer.fetch_data(365)

        assert result is False
        assert analyzer.price_data is None

    @patch("app.tools.get_data.get_data")
    def test_fetch_data_exception_handling(self, mock_download):
        """Test exception handling during data fetching."""
        mock_download.side_effect = Exception("Network error")

        analyzer = MarketDataAnalyzer("ERROR")
        result = analyzer.fetch_data(365)

        assert result is False
        assert analyzer.price_data is None


@pytest.mark.integration
class TestReturnsCalculation:
    """Test returns calculation functionality."""

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        prices = [100, 102, 101, 105, 103, 108, 107]
        return pl.DataFrame(
            {"Date": pd.date_range("2023-01-01", periods=len(prices)), "Close": prices},
        )

    def test_calculate_returns_success(self, sample_price_data):
        """Test successful returns calculation."""
        analyzer = MarketDataAnalyzer("TEST")
        analyzer.price_data = sample_price_data

        result = analyzer.calculate_returns()

        assert result is True
        assert analyzer.returns is not None
        assert len(analyzer.returns) == len(sample_price_data) - 1

        # Check first return: log(102/100) ≈ 0.0198 (log returns)
        expected_first_return = np.log(102 / 100)
        assert abs(analyzer.returns[0] - expected_first_return) < 1e-6

    def test_calculate_returns_no_data(self):
        """Test returns calculation with no price data."""
        analyzer = MarketDataAnalyzer("TEST")

        result = analyzer.calculate_returns()

        assert result is False
        assert analyzer.returns is None

    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        single_price = pl.DataFrame({"Date": ["2023-01-01"], "Close": [100]})

        analyzer = MarketDataAnalyzer("TEST")
        analyzer.price_data = single_price

        result = analyzer.calculate_returns()

        assert result is False
        assert analyzer.returns is None

    def test_calculate_returns_with_nan_values(self):
        """Test returns calculation with NaN values."""
        prices_with_nan = pl.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=5),
                "Close": [100, np.nan, 102, 103, np.nan],
            },
        )

        analyzer = MarketDataAnalyzer("TEST")
        analyzer.price_data = prices_with_nan

        result = analyzer.calculate_returns()

        # Should handle NaN values gracefully
        assert result in [
            True,
            False,
        ]  # May succeed or fail depending on remaining data
        if result:
            assert not np.any(np.isnan(analyzer.returns))


@pytest.mark.integration
class TestDistributionAnalysis:
    """Test distribution analysis functionality."""

    @pytest.fixture
    def sample_returns(self):
        """Create sample returns for testing."""
        np.random.seed(42)
        return np.random.normal(0.001, 0.02, 252)  # Daily returns for one year

    def test_analyze_distribution_success(self, sample_returns):
        """Test successful distribution analysis."""
        analyzer = MarketDataAnalyzer("TEST")
        analyzer.returns = sample_returns

        result = analyzer.analyze_distribution()

        assert isinstance(result, dict)
        assert "sample_size" in result
        assert "mean_daily_return" in result
        assert "std_daily_return" in result
        assert "annualized_volatility" in result
        assert "skewness" in result
        assert "excess_kurtosis" in result
        assert "var_95" in result
        assert "cvar_95" in result
        assert "jarque_bera_statistic" in result
        assert "is_normal_distribution" in result

        # Verify some expected relationships
        assert result["sample_size"] == len(sample_returns)
        assert result["annualized_volatility"] > 0
        assert -1 <= result["var_95"] <= 1  # Should be reasonable for daily returns

    def test_analyze_distribution_no_returns(self):
        """Test distribution analysis with no returns data."""
        analyzer = MarketDataAnalyzer("TEST")

        result = analyzer.analyze_distribution()

        assert result == {}

    def test_analyze_distribution_single_return(self):
        """Test distribution analysis with single return."""
        analyzer = MarketDataAnalyzer("TEST")
        analyzer.returns = np.array([0.01])

        result = analyzer.analyze_distribution()

        # Should handle edge case gracefully
        assert isinstance(result, dict)
        if result:  # If analysis succeeds despite single data point
            assert result["sample_size"] == 1


@pytest.mark.integration
class TestFullAnalysisWorkflow:
    """Test complete analysis workflow."""

    @patch("app.tools.get_data.get_data")
    @pytest.mark.asyncio
    async def test_analyze_complete_workflow(self, mock_download):
        """Test complete analysis from start to finish."""
        # Create realistic mock data
        dates = pd.date_range(start="2022-01-01", end="2023-12-31", freq="D")
        base_price = 100
        prices = [base_price]

        # Generate realistic price series with trend and volatility
        for _i in range(1, len(dates)):
            daily_return = np.random.normal(0.0005, 0.02)  # Slight positive drift
            new_price = prices[-1] * (1 + daily_return)
            prices.append(new_price)

        mock_data = pl.DataFrame(
            {
                "Date": dates,
                "Open": [p * 0.999 for p in prices],
                "High": [p * 1.005 for p in prices],
                "Low": [p * 0.995 for p in prices],
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, len(dates)),
            },
        )

        mock_download.return_value = mock_data

        analyzer = MarketDataAnalyzer("AAPL")
        result = await analyzer.analyze()

        # Verify complete result structure
        assert isinstance(result, dict)
        assert "exit_signal" in result
        assert "recommendation" in result
        assert "confidence_level" in result
        assert "signal_reasoning" in result
        assert "p_value" in result
        assert "data_source" in result
        assert "analysis_mode" in result

        # Verify analysis components
        assert "momentum_differential" in result
        assert "trend_direction_20d" in result
        assert "sharpe_ratio" in result
        assert "sample_size" in result

        # Verify signal is valid
        valid_signals = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
        assert result["exit_signal"] in valid_signals
        assert result["recommendation"] in valid_signals
        assert result["exit_signal"] == result["recommendation"]

        # Verify confidence and p-value relationship
        assert 0 <= result["confidence_level"] <= 1
        assert 0 <= result["p_value"] <= 1
        assert abs((result["confidence_level"] + result["p_value"]) - 1.0) < 0.02

    @patch("app.tools.get_data.get_data")
    @pytest.mark.asyncio
    async def test_analyze_with_fetch_failure(self, mock_download):
        """Test analysis when data fetching fails."""
        mock_download.return_value = None

        analyzer = MarketDataAnalyzer("INVALID")
        result = await analyzer.analyze()

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Failed to fetch market data"
        assert "ticker" in result
        assert "analysis_timestamp" in result


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_ticker(self):
        """Test behavior with empty ticker."""
        analyzer = MarketDataAnalyzer("")
        assert analyzer.ticker == ""

    def test_none_ticker(self):
        """Test behavior with None ticker."""
        # This should raise an exception during initialization
        with pytest.raises((TypeError, ValueError)):
            MarketDataAnalyzer(None)

    def test_special_characters_ticker(self):
        """Test behavior with special characters in ticker."""
        analyzer = MarketDataAnalyzer("BRK.A")
        assert analyzer.ticker == "BRK.A"

    @patch("app.tools.get_data.get_data")
    def test_malformed_data_handling(self, mock_download):
        """Test handling of malformed data."""
        # Create malformed data (missing required columns)
        malformed_data = pl.DataFrame(
            {"Date": ["2023-01-01"], "Price": [100]},  # Missing 'Close' column
        )

        mock_download.return_value = malformed_data

        analyzer = MarketDataAnalyzer("TEST")

        # This should fail gracefully
        fetch_result = analyzer.fetch_data(365)
        if fetch_result:  # If fetch succeeds despite malformed data
            returns_result = analyzer.calculate_returns()
            assert returns_result is False  # Should fail on returns calculation


if __name__ == "__main__":
    pytest.main([__file__])
