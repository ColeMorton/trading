"""
Helper functions for injecting errors in unit tests.

This module provides reusable utilities for creating mock data and
configuring error injection scenarios in unit tests.
"""

from datetime import date, timedelta
from typing import List

import polars as pl


def create_mock_price_data(
    ticker: str = "AAPL",
    rows: int = 100,
    start_date: date | None = None,
    start_price: float = 100.0,
) -> pl.DataFrame:
    """
    Create realistic mock price data for testing.

    Args:
        ticker: Ticker symbol (for reference, not included in DataFrame)
        rows: Number of data points to generate
        start_date: Starting date (defaults to 2023-01-01)
        start_price: Starting price for the data

    Returns:
        Polars DataFrame with OHLCV data
    """
    if start_date is None:
        start_date = date(2023, 1, 1)

    dates = [start_date + timedelta(days=i) for i in range(rows)]
    prices = [start_price + (i * 0.5) for i in range(rows)]

    return pl.DataFrame(
        {
            "Date": dates,
            "Close": prices,
            "Open": [p - 0.5 for p in prices],
            "High": [p + 1.0 for p in prices],
            "Low": [p - 1.0 for p in prices],
            "Volume": [1000000 + (i * 1000) for i in range(rows)],
        }
    )


def create_failing_get_data_mock(
    fail_tickers: list[str], failure_type: str = "none", **kwargs
):
    """
    Create a mock side_effect function for get_data that fails for specific tickers.

    Args:
        fail_tickers: List of ticker symbols that should fail
        failure_type: Type of failure - "none" (returns None), "connection" (raises ConnectionError),
                     "timeout" (raises TimeoutError), "value" (raises ValueError)
        **kwargs: Additional arguments passed to create_mock_price_data

    Returns:
        A side_effect function suitable for mock.side_effect

    Example:
        >>> mock_get_data.side_effect = create_failing_get_data_mock(
        ...     fail_tickers=["INVALID"],
        ...     failure_type="none"
        ... )
    """

    def side_effect(ticker, *args, **inner_kwargs):
        if ticker in fail_tickers:
            if failure_type == "none":
                return None
            if failure_type == "connection":
                raise ConnectionError(f"Failed to connect for ticker {ticker}")
            if failure_type == "timeout":
                raise TimeoutError(f"Timeout fetching data for {ticker}")
            if failure_type == "value":
                raise ValueError(f"Invalid ticker symbol: {ticker}")
            raise RuntimeError(f"Unknown failure type: {failure_type}")

        return create_mock_price_data(ticker=ticker, **kwargs)

    return side_effect


def create_mock_portfolios(
    ticker: str = "AAPL",
    strategy_type: str = "SMA",
    count: int = 5,
) -> list[dict]:
    """
    Create mock portfolio data for export testing.

    Args:
        ticker: Ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD, etc.)
        count: Number of portfolio entries to generate

    Returns:
        List of portfolio dictionaries
    """
    portfolios = []
    for i in range(count):
        fast = 10 + (i * 5)
        slow = 20 + (i * 10)
        portfolios.append(
            {
                "Ticker": ticker,
                "Strategy Type": strategy_type,
                "Fast Period": fast,
                "Slow Period": slow,
                "Score": 1.0 + (i * 0.1),
                "Win Rate [%]": 50.0 + (i * 2),
                "Total Trades": 100 + (i * 10),
                "Profit Factor": 1.5 + (i * 0.1),
                "Sortino Ratio": 1.0 + (i * 0.1),
            }
        )
    return portfolios


def create_filesystem_error(error_type: str, path: str = "/tmp/test") -> Exception:
    """
    Create filesystem-related errors for testing.

    Args:
        error_type: Type of error - "permission", "not_found", "disk_full", "io_error"
        path: Path to include in error message

    Returns:
        Appropriate exception instance
    """
    if error_type == "permission":
        return PermissionError(f"Permission denied: {path}")
    if error_type == "not_found":
        return FileNotFoundError(f"No such file or directory: {path}")
    if error_type == "disk_full":
        import errno

        return OSError(errno.ENOSPC, f"No space left on device: {path}")
    if error_type == "io_error":
        return OSError(f"I/O error: {path}")
    raise ValueError(f"Unknown error type: {error_type}")
