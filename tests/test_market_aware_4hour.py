"""
Comprehensive tests for market-aware 4-hour data processing functionality.

This test suite validates the complete implementation of market-aware 4-hour
timeframe analysis, ensuring proper handling of crypto vs stock market differences.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pandas as pd
import polars as pl
import pytest

from app.tools.data_processing import DataProcessor
from app.tools.market_hours import (
    MarketType,
    detect_market_type,
    filter_trading_hours,
    get_trading_hours,
    validate_4hour_bars,
    validate_market_hours_data,
)


@pytest.mark.integration
class TestMarketTypeDetection:
    """Test market type detection functionality."""

    def test_crypto_detection(self):
        """Test cryptocurrency market detection."""
        crypto_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "ADA-USD"]
        for ticker in crypto_tickers:
            assert detect_market_type(ticker) == MarketType.CRYPTO

    def test_stock_detection(self):
        """Test US stock market detection."""
        stock_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "MSTR", "NVDA"]
        for ticker in stock_tickers:
            assert detect_market_type(ticker) == MarketType.US_STOCK

    def test_edge_cases(self):
        """Test edge cases in market type detection."""
        # Case sensitivity
        assert detect_market_type("btc-usd") == MarketType.CRYPTO
        assert detect_market_type("eth-USD") == MarketType.CRYPTO
        assert detect_market_type("aapl") == MarketType.US_STOCK
        assert detect_market_type("AAPL") == MarketType.US_STOCK


@pytest.mark.integration
class TestMarketAware4HourConversion:
    """Test market-aware 4-hour data conversion."""

    @pytest.fixture
    def sample_hourly_data_pandas(self):
        """Create sample 1-hour pandas data for testing."""
        # Start at midnight for clean 4-hour intervals
        dates = [datetime(2024, 1, 1, 0) + timedelta(hours=i) for i in range(24)]
        return pd.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i * 0.5 for i in range(24)],
                "High": [105.0 + i * 0.5 for i in range(24)],
                "Low": [95.0 + i * 0.5 for i in range(24)],
                "Close": [102.0 + i * 0.5 for i in range(24)],
                "Volume": [1000 + i * 100 for i in range(24)],
            },
        )

    @pytest.fixture
    def sample_hourly_data_polars(self):
        """Create sample 1-hour polars data for testing."""
        # Start at midnight for clean 4-hour intervals
        dates = [datetime(2024, 1, 1, 0) + timedelta(hours=i) for i in range(24)]
        return pl.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i * 0.5 for i in range(24)],
                "High": [105.0 + i * 0.5 for i in range(24)],
                "Low": [95.0 + i * 0.5 for i in range(24)],
                "Close": [102.0 + i * 0.5 for i in range(24)],
                "Volume": [1000 + i * 100 for i in range(24)],
            },
        )

    def test_crypto_4hour_conversion_pandas(self, sample_hourly_data_pandas):
        """Test 4-hour conversion for crypto with pandas data."""
        # Mock the logging to avoid setup issues in tests
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # Test crypto conversion (should use standard UTC-aligned 4-hour bars)
        result = processor.convert_hourly_to_4hour(
            sample_hourly_data_pandas,
            ticker="ETH-USD",
        )

        # Should have 6 bars from 24 hours of data (24/4 = 6)
        assert len(result) == 6
        assert isinstance(result, pd.DataFrame)

        # Validate OHLC structure
        assert list(result.columns) == [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        # Check first bar aggregation
        assert result.iloc[0]["Open"] == 100.0  # First open
        assert result.iloc[0]["High"] == max(
            [105.0 + i * 0.5 for i in range(4)],
        )  # Max high
        assert result.iloc[0]["Low"] == min(
            [95.0 + i * 0.5 for i in range(4)],
        )  # Min low
        assert result.iloc[0]["Close"] == 102.0 + 3 * 0.5  # Last close of 4-hour period
        assert result.iloc[0]["Volume"] == sum(
            [1000 + i * 100 for i in range(4)],
        )  # Sum volume

    def test_crypto_4hour_conversion_polars(self, sample_hourly_data_polars):
        """Test 4-hour conversion for crypto with polars data."""
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # Test crypto conversion
        result = processor.convert_hourly_to_4hour(
            sample_hourly_data_polars,
            ticker="BTC-USD",
        )

        # Should have 6 bars from 24 hours of data
        assert len(result) == 6
        assert isinstance(result, pl.DataFrame)

        # Validate OHLC structure
        assert list(result.columns) == [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

    def test_stock_4hour_conversion_pandas(self, sample_hourly_data_pandas):
        """Test 4-hour conversion for stocks with pandas data."""
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # Test stock conversion (should use market-aware filtering)
        result = processor.convert_hourly_to_4hour(
            sample_hourly_data_pandas,
            ticker="AAPL",
        )

        # Result should be smaller due to trading hours filtering
        assert len(result) <= len(sample_hourly_data_pandas)
        assert isinstance(result, pd.DataFrame)

        # Validate OHLC structure
        assert list(result.columns) == [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

    def test_stock_4hour_conversion_polars(self, sample_hourly_data_polars):
        """Test 4-hour conversion for stocks with polars data."""
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # Test stock conversion
        result = processor.convert_hourly_to_4hour(
            sample_hourly_data_polars,
            ticker="MSFT",
        )

        # Result should be processed through market hours filtering
        assert len(result) <= len(sample_hourly_data_polars)
        assert isinstance(result, pl.DataFrame)

    def test_conversion_without_ticker(self, sample_hourly_data_pandas):
        """Test legacy conversion without ticker (backward compatibility)."""
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # Test without ticker - should use legacy conversion
        result = processor.convert_hourly_to_4hour(sample_hourly_data_pandas)

        # Should return converted data
        assert len(result) <= len(sample_hourly_data_pandas)
        assert isinstance(result, pd.DataFrame)


@pytest.mark.integration
class TestDataValidation:
    """Test data validation for market-aware functionality."""

    @pytest.fixture
    def sample_4hour_data(self):
        """Create sample 4-hour data for validation testing."""
        dates = [datetime(2024, 1, 1) + timedelta(hours=i * 4) for i in range(6)]
        return pl.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i for i in range(6)],
                "High": [105.0 + i for i in range(6)],
                "Low": [95.0 + i for i in range(6)],
                "Close": [102.0 + i for i in range(6)],
                "Volume": [1000 + i * 100 for i in range(6)],
            },
        )

    def test_crypto_data_validation(self, sample_4hour_data):
        """Test validation of crypto 4-hour data."""
        validation = validate_4hour_bars(sample_4hour_data, MarketType.CRYPTO)

        assert validation["is_valid"] is True
        assert validation["bar_count"] == 6
        assert validation["expected_bars_per_day"] == 6  # 24/7 trading
        assert validation["recommendation"] == "optimal_for_crypto_analysis"
        assert len(validation["issues"]) == 0

    def test_stock_data_validation(self, sample_4hour_data):
        """Test validation of stock 4-hour data."""
        validation = validate_4hour_bars(sample_4hour_data, MarketType.US_STOCK)

        assert validation["is_valid"] is True
        assert validation["bar_count"] == 6
        assert validation["expected_bars_per_day"] == 1.6  # 6.5 hours / 4 hours
        assert validation["recommendation"] == "validate_volume_patterns"
        assert (
            len(validation["issues"]) > 0
        )  # Should warn about potential after-hours data

    def test_market_hours_validation_crypto(self, sample_4hour_data):
        """Test market hours validation for crypto data."""
        validation = validate_market_hours_data(sample_4hour_data, MarketType.CRYPTO)

        assert validation["validation_passed"] is True
        assert validation["trading_hours_records"] == validation["total_records"]
        assert validation["after_hours_percentage"] == 0.0
        assert (
            validation["weekend_percentage"] == 0.0
        )  # Sample data doesn't include weekends

    def test_market_hours_validation_stock(self, sample_4hour_data):
        """Test market hours validation for stock data."""
        validation = validate_market_hours_data(sample_4hour_data, MarketType.US_STOCK)

        assert validation["total_records"] == 6
        # Note: Validation results will depend on the actual timestamps in sample data
        assert "validation_passed" in validation
        assert "after_hours_percentage" in validation
        assert "weekend_percentage" in validation


@pytest.mark.integration
class TestTradingHoursFiltering:
    """Test trading hours filtering functionality."""

    @pytest.fixture
    def mixed_hours_data_pandas(self):
        """Create pandas data with mixed trading and after-hours timestamps."""
        # Create data spanning multiple days with various hours
        dates = []
        base_date = datetime(2024, 1, 2)  # Tuesday
        for day in range(3):  # 3 days
            for hour in range(24):
                dates.append(base_date + timedelta(days=day, hours=hour))

        # Convert to timezone-aware datetime with UTC timezone
        dates_tz = pd.to_datetime(dates).tz_localize("UTC")

        return pd.DataFrame(
            {
                "Date": dates_tz,
                "Open": [100.0 + i * 0.1 for i in range(len(dates))],
                "High": [105.0 + i * 0.1 for i in range(len(dates))],
                "Low": [95.0 + i * 0.1 for i in range(len(dates))],
                "Close": [102.0 + i * 0.1 for i in range(len(dates))],
                "Volume": [1000 + i * 10 for i in range(len(dates))],
            },
        )

    @pytest.fixture
    def mixed_hours_data_polars(self):
        """Create polars data with mixed trading and after-hours timestamps."""
        dates = []
        base_date = datetime(2024, 1, 2)  # Tuesday
        for day in range(3):  # 3 days
            for hour in range(24):
                dates.append(base_date + timedelta(days=day, hours=hour))

        return pl.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i * 0.1 for i in range(len(dates))],
                "High": [105.0 + i * 0.1 for i in range(len(dates))],
                "Low": [95.0 + i * 0.1 for i in range(len(dates))],
                "Close": [102.0 + i * 0.1 for i in range(len(dates))],
                "Volume": [1000 + i * 10 for i in range(len(dates))],
            },
        )

    def test_crypto_no_filtering(self, mixed_hours_data_pandas):
        """Test that crypto data is not filtered (24/7 trading)."""
        original_length = len(mixed_hours_data_pandas)
        filtered = filter_trading_hours(mixed_hours_data_pandas, MarketType.CRYPTO)

        # Crypto should return all data (no filtering)
        assert len(filtered) == original_length
        assert isinstance(filtered, pd.DataFrame)

    def test_stock_trading_hours_filtering_pandas(self, mixed_hours_data_pandas):
        """Test stock trading hours filtering with pandas data."""
        original_length = len(mixed_hours_data_pandas)
        filtered = filter_trading_hours(mixed_hours_data_pandas, MarketType.US_STOCK)

        # Stock filtering should remove some data (after-hours and weekends)
        assert len(filtered) < original_length
        assert isinstance(filtered, pd.DataFrame)

    def test_stock_trading_hours_filtering_polars(self, mixed_hours_data_polars):
        """Test stock trading hours filtering with polars data."""
        original_length = len(mixed_hours_data_polars)
        filtered = filter_trading_hours(mixed_hours_data_polars, MarketType.US_STOCK)

        # Stock filtering should remove some data
        assert len(filtered) < original_length
        assert isinstance(filtered, pl.DataFrame)


@pytest.mark.integration
class TestTradingHoursConfiguration:
    """Test trading hours configuration functionality."""

    def test_crypto_trading_hours(self):
        """Test crypto trading hours configuration."""
        crypto_hours = get_trading_hours(MarketType.CRYPTO)

        assert crypto_hours.start_time.hour == 0
        assert crypto_hours.start_time.minute == 0
        assert crypto_hours.end_time.hour == 23
        assert crypto_hours.end_time.minute == 59
        assert len(crypto_hours.trading_days) == 7  # All days

    def test_stock_trading_hours(self):
        """Test US stock trading hours configuration."""
        stock_hours = get_trading_hours(MarketType.US_STOCK)

        assert stock_hours.start_time.hour == 9
        assert stock_hours.start_time.minute == 30
        assert stock_hours.end_time.hour == 16
        assert stock_hours.end_time.minute == 0
        assert len(stock_hours.trading_days) == 5  # Monday-Friday


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the complete market-aware system."""

    def test_end_to_end_crypto_processing(self):
        """Test complete crypto data processing pipeline."""
        # Create sample data
        dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(48)]  # 2 days
        hourly_data = pl.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i * 0.5 for i in range(48)],
                "High": [105.0 + i * 0.5 for i in range(48)],
                "Low": [95.0 + i * 0.5 for i in range(48)],
                "Close": [102.0 + i * 0.5 for i in range(48)],
                "Volume": [1000 + i * 100 for i in range(48)],
            },
        )

        # Process through complete pipeline
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # 1. Market type detection
        market_type = detect_market_type("ETH-USD")
        assert market_type == MarketType.CRYPTO

        # 2. Market-aware 4-hour conversion
        four_hour_data = processor.convert_hourly_to_4hour(
            hourly_data,
            ticker="ETH-USD",
        )

        # 3. Validation
        validation = validate_4hour_bars(four_hour_data, market_type)

        # Assertions
        assert len(four_hour_data) == 12  # 48 hours / 4 = 12 bars
        assert validation["is_valid"] is True
        assert validation["recommendation"] == "optimal_for_crypto_analysis"

    def test_end_to_end_stock_processing(self):
        """Test complete stock data processing pipeline."""
        # Create sample data (include after-hours data)
        dates = [
            datetime(2024, 1, 2, 8) + timedelta(hours=i) for i in range(24)
        ]  # Tuesday
        hourly_data = pl.DataFrame(
            {
                "Date": dates,
                "Open": [100.0 + i * 0.5 for i in range(24)],
                "High": [105.0 + i * 0.5 for i in range(24)],
                "Low": [95.0 + i * 0.5 for i in range(24)],
                "Close": [102.0 + i * 0.5 for i in range(24)],
                "Volume": [1000 + i * 100 for i in range(24)],
            },
        )

        # Process through complete pipeline
        mock_log = Mock()
        processor = DataProcessor(log=mock_log)

        # 1. Market type detection
        market_type = detect_market_type("AAPL")
        assert market_type == MarketType.US_STOCK

        # 2. Market-aware 4-hour conversion (includes filtering)
        four_hour_data = processor.convert_hourly_to_4hour(hourly_data, ticker="AAPL")

        # 3. Validation
        validation = validate_4hour_bars(four_hour_data, market_type)

        # Assertions
        assert len(four_hour_data) <= len(hourly_data)  # Should be filtered
        assert validation["is_valid"] is True
        assert validation["recommendation"] == "validate_volume_patterns"
        assert len(validation["issues"]) > 0  # Should warn about potential issues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
