#!/usr/bin/env python3
"""
Test Data Stabilization Utilities

This module provides decorators and utilities to replace external API calls
with stable, deterministic mock data for reliable test execution.

Key Features:
- Automatic mocking of yfinance and other external APIs
- Centralized test data management
- Performance optimizations for test suites
- Consistent data across test runs
- Easy integration with existing tests
"""

import functools
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

from tests.fixtures.market_data_factory import MarketDataFactory, mock_yfinance_download


class DataStabilizer:
    """Manages stable data generation and API mocking for tests."""

    def __init__(self, seed: int = 42):
        """Initialize with a seed for consistent data generation."""
        self.seed = seed
        self.factory = MarketDataFactory(seed=seed)
        self._cache = {}  # Cache frequently used data

    def get_stable_data(self, key: str, generator_func: Callable, *args, **kwargs):
        """Get cached stable data or generate if not exists."""
        if key not in self._cache:
            self._cache[key] = generator_func(*args, **kwargs)
        return self._cache[key]

    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()


# Global stabilizer instance
_stabilizer = DataStabilizer()


def stable_market_data(
    tickers: list[str] | None = None,
    mock_yfinance: bool = True,
    mock_get_data: bool = True,
    cache_key: str | None = None,
):
    """
    Decorator to provide stable market data for tests.

    Args:
        tickers: List of tickers to generate data for (default: ["AAPL", "MSFT", "GOOGL"])
        mock_yfinance: Whether to mock yfinance.download calls
        mock_get_data: Whether to mock app.tools.get_data calls
        cache_key: Key for caching generated data across tests

    Example:
        @stable_market_data(tickers=["AAPL", "MSFT"])
        def test_strategy_with_stable_data(self):
            # Test will use mocked, stable data for AAPL and MSFT
            pass
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            patches = []

            # Mock yfinance if requested
            if mock_yfinance:

                def mock_yf_download(symbols, start=None, end=None, **yf_kwargs):
                    return mock_yfinance_download(symbols, start, end, **yf_kwargs)

                patches.append(patch("yfinance.download", side_effect=mock_yf_download))

            # Mock get_data if requested
            if mock_get_data:

                def mock_get_data_func(ticker, config, log):
                    cache_key_data = f"get_data_{ticker}_{hash(str(config))}"
                    return _stabilizer.get_stable_data(
                        cache_key_data,
                        _stabilizer.factory.create_price_data,
                        ticker=ticker,
                        pattern="trending_with_signals",
                    )

                patches.append(
                    patch(
                        "app.tools.get_data.get_data", side_effect=mock_get_data_func
                    ),
                )

            # Apply all patches
            for p in patches:
                p.start()

            try:
                result = test_func(*args, **kwargs)
            finally:
                # Stop all patches
                for p in patches:
                    p.stop()

            return result

        return wrapper

    return decorator


def mock_external_apis(
    apis: list[str] | None = None,
    return_values: dict[str, Any] | None = None,
):
    """
    Decorator to mock specific external APIs with custom return values.

    Args:
        apis: List of API modules/functions to mock (e.g., ['yfinance.download'])
        return_values: Dictionary mapping API names to return values

    Example:
        @mock_external_apis(['yfinance.download'], {'yfinance.download': mock_df})
        def test_with_custom_data(self):
            pass
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            apis_to_mock = apis or ["yfinance.download"]
            values = return_values or {}
            patches = []

            for api in apis_to_mock:
                if api in values:
                    mock_obj = Mock(return_value=values[api])
                else:
                    # Use our stable data factory as default
                    mock_obj = Mock(side_effect=mock_yfinance_download)

                patches.append(patch(api, mock_obj))

            # Start patches
            for p in patches:
                p.start()

            try:
                result = test_func(*args, **kwargs)
            finally:
                # Stop patches
                for p in patches:
                    p.stop()

            return result

        return wrapper

    return decorator


def fast_test_data(pattern: str = "simple", periods: int = 100):
    """
    Decorator to provide minimal, fast test data for performance-sensitive tests.

    Args:
        pattern: Data pattern ('simple', 'trending', 'volatile')
        periods: Number of data points to generate

    Example:
        @fast_test_data(pattern='trending', periods=50)
        def test_quick_strategy_check(self):
            pass
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            def mock_fast_get_data(ticker, config, log):
                return _stabilizer.factory.create_strategy_test_data(
                    ticker=ticker,
                    periods=periods,
                    pattern="trending_with_signals",
                )

            def mock_fast_yf_download(symbols, **yf_kwargs):
                if isinstance(symbols, str):
                    symbols = [symbols]

                # Generate minimal data for each symbol
                data_dict = {}
                for symbol in symbols:
                    df = _stabilizer.factory.create_strategy_test_data(
                        ticker=symbol,
                        periods=periods,
                    ).to_pandas()
                    df = df.set_index("Date")
                    data_dict.update(
                        {
                            ("Open", symbol): df["Open"],
                            ("High", symbol): df["High"],
                            ("Low", symbol): df["Low"],
                            ("Close", symbol): df["Close"],
                            ("Volume", symbol): df["Volume"],
                        },
                    )

                import pandas as pd

                result_df = pd.DataFrame(data_dict)
                result_df.columns = pd.MultiIndex.from_tuples(result_df.columns)
                return result_df

            patches = [
                patch("yfinance.download", side_effect=mock_fast_yf_download),
                patch("app.tools.get_data.get_data", side_effect=mock_fast_get_data),
            ]

            for p in patches:
                p.start()

            try:
                result = test_func(*args, **kwargs)
            finally:
                for p in patches:
                    p.stop()

            return result

        return wrapper

    return decorator


def stabilize_integration_test(
    tickers: list[str] | None = None,
    timeout_override: int = 30,
    cache_data: bool = True,
):
    """
    Decorator specifically for integration tests that need comprehensive mocking.

    Args:
        tickers: Tickers to generate data for
        timeout_override: Override test timeout for stability
        cache_data: Whether to cache generated data

    Example:
        @stabilize_integration_test(tickers=['AAPL', 'MSFT'], timeout_override=60)
        def test_full_pipeline_integration(self):
            pass
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            test_tickers = tickers or ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

            # Generate comprehensive test data upfront
            if cache_data:
                cache_key = f"integration_data_{hash(tuple(test_tickers))}"
                test_data = _stabilizer.get_stable_data(
                    cache_key,
                    _stabilizer.factory.create_multi_ticker_data,
                    test_tickers,
                )
            else:
                test_data = _stabilizer.factory.create_multi_ticker_data(test_tickers)

            def mock_comprehensive_get_data(ticker, config, log):
                if ticker in test_data:
                    return test_data[ticker]
                # Generate on-demand for missing tickers
                return _stabilizer.factory.create_price_data(ticker)

            def mock_comprehensive_yf_download(symbols, **yf_kwargs):
                return _stabilizer.factory.create_yfinance_compatible_data(
                    symbols,
                    **yf_kwargs,
                )

            # Comprehensive API mocking
            patches = [
                patch("yfinance.download", side_effect=mock_comprehensive_yf_download),
                patch(
                    "app.tools.get_data.get_data",
                    side_effect=mock_comprehensive_get_data,
                ),
                patch(
                    "app.tools.download_data.download_data",
                    side_effect=mock_comprehensive_get_data,
                ),
            ]

            # Start all patches
            for p in patches:
                p.start()

            try:
                result = test_func(*args, **kwargs)
            finally:
                # Clean up patches
                for p in patches:
                    p.stop()

            return result

        return wrapper

    return decorator


# Utility functions for test setup
def setup_stable_test_environment():
    """Set up stable test environment with common mocks."""
    _stabilizer.clear_cache()


def get_test_data_factory() -> MarketDataFactory:
    """Get the global test data factory instance."""
    return _stabilizer.factory


def create_test_fixtures(tickers: list[str]) -> dict[str, Any]:
    """Create common test fixtures for a set of tickers."""
    factory = _stabilizer.factory

    return {
        "price_data": factory.create_multi_ticker_data(tickers),
        "single_ticker_data": (
            factory.create_price_data(tickers[0]) if tickers else None
        ),
        "strategy_test_data": factory.create_strategy_test_data() if tickers else None,
        "yfinance_format_data": (
            factory.create_yfinance_compatible_data(tickers) if tickers else None
        ),
    }


# Context managers for temporary API mocking
class MockExternalAPIs:
    """Context manager for temporarily mocking external APIs."""

    def __init__(self, apis: list[str], mock_data: dict | None = None):
        self.apis = apis
        self.mock_data = mock_data or {}
        self.patches = []

    def __enter__(self):
        for api in self.apis:
            if api in self.mock_data:
                mock_obj = Mock(return_value=self.mock_data[api])
            else:
                mock_obj = Mock(side_effect=mock_yfinance_download)

            patch_obj = patch(api, mock_obj)
            self.patches.append(patch_obj)
            patch_obj.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in self.patches:
            patch_obj.stop()
        self.patches.clear()


# Performance monitoring for tests
class TestPerformanceTracker:
    """Track test performance and identify slow tests."""

    def __init__(self):
        self.execution_times = {}
        self.api_call_counts = {}

    def track_test(self, test_name: str, execution_time: float, api_calls: int = 0):
        """Track test execution metrics."""
        self.execution_times[test_name] = execution_time
        self.api_call_counts[test_name] = api_calls

    def get_slow_tests(self, threshold: float = 5.0) -> list[str]:
        """Get tests that exceed the execution time threshold."""
        return [
            test_name
            for test_name, exec_time in self.execution_times.items()
            if exec_time > threshold
        ]

    def generate_report(self) -> dict[str, Any]:
        """Generate performance report."""
        return {
            "total_tests": len(self.execution_times),
            "average_execution_time": (
                sum(self.execution_times.values()) / len(self.execution_times)
                if self.execution_times
                else 0
            ),
            "slow_tests": self.get_slow_tests(),
            "total_api_calls": sum(self.api_call_counts.values()),
            "tests_with_api_calls": len(
                [c for c in self.api_call_counts.values() if c > 0],
            ),
        }


# Global performance tracker
performance_tracker = TestPerformanceTracker()
