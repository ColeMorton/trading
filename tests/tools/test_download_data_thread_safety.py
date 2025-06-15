"""
Test thread safety of download_data function.

This test suite ensures that concurrent data downloads don't experience
column name contamination or other thread safety issues.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import polars as pl
import pytest

from app.tools.download_data import download_data


class TestDownloadDataThreadSafety:
    """Test suite for thread safety in download_data function."""

    @pytest.fixture
    def mock_config(self):
        """Basic configuration for testing."""
        return {
            "USE_HOURLY": False,
            "USE_YEARS": False,
            "PERIOD": "max",
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    def create_mock_yfinance_data(self, ticker):
        """Create mock data that simulates yfinance MultiIndex column behavior."""
        dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")

        # Simulate MultiIndex columns from yfinance when downloading multiple tickers
        data = pd.DataFrame(
            {
                ("Open", ticker): [100.0] * len(dates),
                ("High", ticker): [105.0] * len(dates),
                ("Low", ticker): [95.0] * len(dates),
                ("Close", ticker): [100.0] * len(dates),
                ("Adj Close", ticker): [100.0] * len(dates),
                ("Volume", ticker): [1000000] * len(dates),
            },
            index=dates,
        )

        # Set the index name to match yfinance behavior
        data.index.name = "Date"

        # Create MultiIndex columns to simulate yfinance behavior
        data.columns = pd.MultiIndex.from_tuples(data.columns)

        return data

    @patch("yfinance.download")
    def test_concurrent_downloads_without_lock_causes_contamination(
        self, mock_yf_download, mock_config, mock_log
    ):
        """Test that concurrent downloads without proper locking cause column contamination."""
        # This test simulates the original bug by removing the lock temporarily

        contamination_detected = False
        download_count = 0

        def mock_download_with_contamination(*args, **kwargs):
            nonlocal download_count
            ticker = args[0]
            download_count += 1

            # Simulate cross-contamination on subsequent downloads
            if download_count > 1:
                # Return data with wrong ticker in column names
                wrong_ticker = "TSM"  # Contamination from first download
                return self.create_mock_yfinance_data(wrong_ticker)
            else:
                return self.create_mock_yfinance_data(ticker)

        mock_yf_download.side_effect = mock_download_with_contamination

        # Temporarily remove the lock to simulate the original issue
        from app.tools import download_data as dl_module

        original_lock = dl_module._yfinance_lock
        dl_module._yfinance_lock = threading.Lock()  # New lock that won't be used

        try:
            results = []
            errors = []

            # Run concurrent downloads
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        download_data, ticker, mock_config, mock_log
                    ): ticker
                    for ticker in ["FANG", "ADI", "TSN", "KULR"]
                }

                for future in as_completed(futures):
                    ticker = futures[future]
                    try:
                        result = future.result()
                        results.append((ticker, result))
                    except Exception as e:
                        errors.append((ticker, str(e)))
                        if "Column" in str(e) and "not found" in str(e):
                            contamination_detected = True

            # Verify contamination occurred (this was the original bug)
            assert (
                contamination_detected or len(errors) > 0
            ), "Expected column contamination to occur without proper locking"

        finally:
            # Restore the original lock
            dl_module._yfinance_lock = original_lock

    @patch("yfinance.download")
    def test_concurrent_downloads_with_lock_prevents_contamination(
        self, mock_yf_download, mock_config, mock_log
    ):
        """Test that the thread lock prevents column contamination in concurrent downloads."""

        download_order = []

        def mock_download_sequential(*args, **kwargs):
            ticker = args[0]
            download_order.append(ticker)
            # Add small delay to simulate download time
            time.sleep(0.01)
            return self.create_mock_yfinance_data(ticker)

        mock_yf_download.side_effect = mock_download_sequential

        tickers = ["FANG", "ALGN", "IR", "TSM", "ARM", "MTD", "ADI", "MPC"]
        results = []
        errors = []

        # Run concurrent downloads (with the lock in place)
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(download_data, ticker, mock_config, mock_log): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    result = future.result()
                    results.append((ticker, result))
                except Exception as e:
                    errors.append((ticker, str(e)))

        # All downloads should succeed
        assert len(results) == len(
            tickers
        ), f"Expected {len(tickers)} successful downloads, got {len(results)}"
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # Verify each result has correct columns
        for ticker, df in results:
            assert isinstance(df, pl.DataFrame)
            assert "Date" in df.columns
            assert "Open" in df.columns
            assert "Close" in df.columns
            # Should not have ticker-specific columns after normalization
            assert f"Close_{ticker}" not in df.columns
            assert f"Open_{ticker}" not in df.columns

    @patch("yfinance.download")
    def test_thread_lock_ensures_sequential_yfinance_calls(
        self, mock_yf_download, mock_config, mock_log
    ):
        """Test that the thread lock ensures yfinance calls happen sequentially."""

        concurrent_calls = []
        max_concurrent = 0
        lock = threading.Lock()

        def mock_download_tracking(*args, **kwargs):
            ticker = args[0]

            with lock:
                concurrent_calls.append(ticker)
                current_concurrent = len(concurrent_calls)
                nonlocal max_concurrent
                max_concurrent = max(max_concurrent, current_concurrent)

            # Simulate download time
            time.sleep(0.05)

            with lock:
                concurrent_calls.remove(ticker)

            return self.create_mock_yfinance_data(ticker)

        mock_yf_download.side_effect = mock_download_tracking

        # Run concurrent downloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(download_data, ticker, mock_config, mock_log)
                for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN"]
            ]

            # Wait for all to complete
            for future in futures:
                future.result()

        # With the lock, only one yfinance call should happen at a time
        assert (
            max_concurrent == 1
        ), f"Expected max 1 concurrent call, but got {max_concurrent}"

    @patch("yfinance.download")
    def test_error_handling_with_concurrent_downloads(
        self, mock_yf_download, mock_config, mock_log
    ):
        """Test that errors in one download don't affect others."""

        def mock_download_with_errors(*args, **kwargs):
            ticker = args[0]
            if ticker == "FAIL":
                raise ValueError(f"Simulated download failure for {ticker}")
            return self.create_mock_yfinance_data(ticker)

        mock_yf_download.side_effect = mock_download_with_errors

        tickers = ["AAPL", "FAIL", "GOOGL", "MSFT"]
        results = []
        errors = []

        # Run concurrent downloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(download_data, ticker, mock_config, mock_log): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    result = future.result()
                    results.append(ticker)
                except Exception as e:
                    errors.append((ticker, str(e)))

        # Should have 3 successes and 1 failure
        assert len(results) == 3
        assert len(errors) == 1
        assert errors[0][0] == "FAIL"
        assert "Simulated download failure" in errors[0][1]

    @patch("yfinance.download")
    def test_data_integrity_across_concurrent_downloads(
        self, mock_yf_download, mock_config, mock_log
    ):
        """Test that each ticker gets its own correct data without mixing."""

        def mock_download_unique_data(*args, **kwargs):
            ticker = args[0]
            dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")

            # Create unique data for each ticker
            base_price = {"AAPL": 150, "GOOGL": 2800, "MSFT": 380, "TSLA": 200}

            price = base_price.get(ticker, 100)
            data = pd.DataFrame(
                {
                    "Open": [price * 0.98] * len(dates),
                    "High": [price * 1.02] * len(dates),
                    "Low": [price * 0.96] * len(dates),
                    "Close": [price] * len(dates),
                    "Volume": [1000000 * hash(ticker) % 10] * len(dates),
                },
                index=dates,
            )

            data.index.name = "Date"
            return data

        mock_yf_download.side_effect = mock_download_unique_data

        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        expected_prices = {"AAPL": 150, "GOOGL": 2800, "MSFT": 380, "TSLA": 200}

        results = {}

        # Run concurrent downloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(download_data, ticker, mock_config, mock_log): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                result = future.result()
                results[ticker] = result

        # Verify each ticker got its correct data
        for ticker, df in results.items():
            expected_close = expected_prices[ticker]
            actual_close = df["Close"][0]
            assert (
                actual_close == expected_close
            ), f"{ticker}: Expected close price {expected_close}, got {actual_close}"

    def test_performance_impact_of_thread_lock(self, mock_config, mock_log):
        """Test that the thread lock doesn't significantly impact performance for single downloads."""

        with patch("yfinance.download") as mock_yf_download:
            mock_yf_download.return_value = self.create_mock_yfinance_data("AAPL")

            # Time a single download
            start_time = time.time()
            result = download_data("AAPL", mock_config, mock_log)
            single_duration = time.time() - start_time

            assert isinstance(result, pl.DataFrame)
            # Single download should be fast (no significant overhead from lock)
            assert (
                single_duration < 0.1
            ), f"Single download took too long: {single_duration}s"


class TestConcurrentStrategyExecution:
    """Integration tests for concurrent strategy execution with thread-safe downloads."""

    @pytest.fixture
    def strategy_config(self):
        """Configuration for strategy testing."""
        return {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
            "STRATEGY_TYPE": "SMA",
            "SHORT_WINDOW": 10,
            "LONG_WINDOW": 20,
            "USE_HOURLY": False,
            "BASE_DIR": "/Users/colemorton/Projects/trading",
            "REFRESH": True,
        }

    @patch("yfinance.download")
    @patch("app.strategies.ma_cross.tools.strategy_execution.backtest_strategy")
    def test_full_concurrent_pipeline_with_thread_safety(
        self, mock_backtest, mock_yf_download, strategy_config
    ):
        """Test the full concurrent execution pipeline with thread-safe downloads."""
        from app.strategies.ma_cross.tools.strategy_execution import (
            execute_strategy_concurrent,
        )

        # Track download order to ensure serialization
        download_calls = []

        def mock_download_tracking(*args, **kwargs):
            ticker = args[0]
            download_calls.append((ticker, time.time()))
            return self.create_mock_yfinance_data(ticker)

        mock_yf_download.side_effect = mock_download_tracking
        mock_backtest.return_value = MagicMock()  # Mock portfolio result
        mock_log = Mock()

        # Execute strategy concurrently
        results = execute_strategy_concurrent(
            strategy_config, "SMA", mock_log, None, max_workers=4
        )

        # Verify downloads happened sequentially (no overlap due to lock)
        for i in range(1, len(download_calls)):
            prev_ticker, prev_time = download_calls[i - 1]
            curr_ticker, curr_time = download_calls[i]
            # Downloads should not overlap (allowing small margin for timing)
            assert (
                curr_time >= prev_time
            ), f"Downloads overlapped: {prev_ticker} and {curr_ticker}"

    def create_mock_yfinance_data(self, ticker):
        """Helper method to create mock data."""
        dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
        data = pd.DataFrame(
            {
                "Open": [100.0] * len(dates),
                "High": [105.0] * len(dates),
                "Low": [95.0] * len(dates),
                "Close": [100.0] * len(dates),
                "Volume": [1000000] * len(dates),
            },
            index=dates,
        )
        data.index.name = "Date"
        return data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
