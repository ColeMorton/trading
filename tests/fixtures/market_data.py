#!/usr/bin/env python3
"""
Market Data Test Fixtures

Provides realistic market data that passes validation and represents
actual trading scenarios for comprehensive testing.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import polars as pl


def create_realistic_price_data(
    ticker: str,
    days: int = 100,
    start_price: float = 100.0,
    start_date: datetime | None = None,
    volatility: float = 0.02,
    trend: float = 0.0005,
) -> pl.DataFrame:
    """
    Create realistic OHLCV price data that passes validation.

    Args:
        ticker: Stock ticker symbol
        days: Number of trading days
        start_price: Starting price
        start_date: Starting date (defaults to 100 days ago)
        volatility: Daily volatility (std dev of returns)
        trend: Daily trend (drift in returns)

    Returns:
        DataFrame with realistic OHLCV data
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days + 10)

    # Generate realistic price series using geometric Brownian motion
    np.random.seed(42)  # Reproducible results

    dates = pd.bdate_range(start=start_date, periods=days)

    # Generate returns with trend and volatility
    returns = np.random.normal(trend, volatility, days)

    # Calculate cumulative prices
    prices = [start_price]
    for i in range(1, days):
        prices.append(prices[-1] * (1 + returns[i]))

    # Generate OHLC from close prices with realistic spreads
    closes = np.array(prices)

    # High/Low typically within 1-3% of close
    high_factor = np.random.uniform(1.005, 1.03, days)
    low_factor = np.random.uniform(0.97, 0.995, days)

    highs = closes * high_factor
    lows = closes * low_factor

    # Opens are typically close to previous close with some gap
    opens = np.roll(closes, 1) * np.random.uniform(0.995, 1.005, days)
    opens[0] = start_price

    # Volume should be realistic (thousands to millions)
    base_volume = np.random.randint(100000, 5000000)
    volumes = np.random.normal(base_volume, base_volume * 0.3, days).astype(int)
    volumes = np.maximum(volumes, 10000)  # Minimum volume

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
            "Ticker": ticker,
        }
    )
    return pl.from_pandas(df)


def create_crossover_scenario_data(
    ticker: str = "TEST", crossover_day: int = 50
) -> pl.DataFrame:
    """
    Create data with a clear MA crossover at specified day.
    Useful for testing signal generation logic.
    """
    days = 100

    # Create data that ensures crossover
    dates = pd.bdate_range(start=datetime.now() - timedelta(days=days), periods=days)

    # Price starts low, trends up to create crossover
    base_price = 100.0
    prices = []

    for i in range(days):
        if i < crossover_day:
            # Gentle decline then recovery
            factor = 0.999 + (i / crossover_day) * 0.002
        else:
            # Strong uptrend after crossover
            factor = 1.002

        if i == 0:
            prices.append(base_price)
        else:
            prices.append(prices[-1] * factor)

    # Add some noise but preserve trend
    noise = np.random.normal(0, 0.005, days)
    prices = np.array(prices) * (1 + noise)

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": prices * 0.999,
            "High": prices * 1.005,
            "Low": prices * 0.995,
            "Close": prices,
            "Volume": np.random.randint(100000, 1000000, days),
            "Ticker": ticker,
        }
    )
    return pl.from_pandas(df)


def create_portfolio_test_data() -> list[dict]:
    """
    Create realistic portfolio data for testing filtering and processing.
    """
    return [
        {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Total Return [%]": 125.5,
            "Win Rate [%]": 65.2,
            "Total Trades": 45,
            "Profit Factor": 1.85,
            "Expectancy per Trade": 2.1,
            "Sortino Ratio": 1.2,
            "Beats BNH [%]": 35.5,
            "Max Drawdown [%]": 15.2,
            "Sharpe Ratio": 1.1,
            "Signal Entry": True,
            "Signal Exit": False,
            "Total Open Trades": 1,
            "Score": 1.8,
        },
        {
            "Ticker": "GOOGL",
            "Strategy Type": "EMA",
            "Fast Period": 12,
            "Slow Period": 26,
            "Total Return [%]": 89.3,
            "Win Rate [%]": 58.7,
            "Total Trades": 38,
            "Profit Factor": 1.45,
            "Expectancy per Trade": 1.2,
            "Sortino Ratio": 0.95,
            "Beats BNH [%]": 15.3,
            "Max Drawdown [%]": 22.1,
            "Sharpe Ratio": 0.85,
            "Signal Entry": False,
            "Signal Exit": True,
            "Total Open Trades": 0,
            "Score": 1.2,
        },
        {
            "Ticker": "TSLA",
            "Strategy Type": "SMA",
            "Fast Period": 15,
            "Slow Period": 35,
            "Total Return [%]": 45.2,
            "Win Rate [%]": 52.1,
            "Total Trades": 28,
            "Profit Factor": 1.15,
            "Expectancy per Trade": 0.8,
            "Sortino Ratio": 0.65,
            "Beats BNH [%]": -5.2,
            "Max Drawdown [%]": 28.5,
            "Sharpe Ratio": 0.45,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Open Trades": 0,
            "Score": 0.9,
        },
    ]


def create_invalid_test_data() -> pl.DataFrame:
    """Create data that should fail validation for negative testing."""
    df = pd.DataFrame(
        {
            "Date": ["invalid_date", "2023-01-02"],
            "Close": [None, "not_a_number"],
            "Volume": [-100, "negative_volume"],
        }
    )
    return pl.from_pandas(df)
