#!/usr/bin/env python3
"""
Market Data Factory for Test Stabilization

This module provides stable, repeatable market data generation for tests,
replacing unreliable external API calls with consistent mock data.

Key Features:
- Deterministic data generation using seeds
- Realistic price patterns and volatility
- Multiple timeframe support (daily, hourly, 4-hour)
- Volume and technical indicator data
- Multi-ticker support with correlation
- Performance optimized for test suites
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import polars as pl


class MarketDataFactory:
    """Factory for generating realistic market data for testing purposes."""

    def __init__(self, seed: int = 42):
        """
        Initialize the market data factory.

        Args:
            seed: Random seed for reproducible data generation
        """
        self.seed = seed
        np.random.seed(seed)

        # Common market parameters
        self.base_volatility = 0.02
        self.daily_drift = 0.0005  # Small positive bias
        self.market_correlation = 0.6  # Base correlation between assets

    def create_price_data(
        self,
        ticker: str,
        start_date: str | datetime = "2023-01-01",
        end_date: str | datetime = "2023-12-31",
        frequency: str = "D",
        base_price: float = 100.0,
        volatility: float | None = None,
        trend: float | None = None,
        pattern: str = "random_walk",
    ) -> pl.DataFrame:
        """
        Generate realistic price data for a single ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data generation
            end_date: End date for data generation
            frequency: Data frequency ('D', 'H', '4H')
            base_price: Starting price for the asset
            volatility: Price volatility (defaults to base volatility)
            trend: Daily drift/trend (defaults to base drift)
            pattern: Price pattern ('random_walk', 'trending', 'mean_reverting', 'volatile')

        Returns:
            Polars DataFrame with OHLCV data
        """
        # Parse dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Generate date range based on frequency
        if frequency == "D":
            dates = pl.date_range(start_date, end_date, interval="1d", eager=True)
        elif frequency == "H":
            dates = pl.date_range(start_date, end_date, interval="1h", eager=True)
        elif frequency == "4H":
            dates = pl.date_range(start_date, end_date, interval="4h", eager=True)
        else:
            msg = f"Unsupported frequency: {frequency}"
            raise ValueError(msg)

        n_periods = len(dates)

        # Set parameters
        vol = volatility or self.base_volatility
        drift = trend or self.daily_drift

        # Generate price series based on pattern
        if pattern == "random_walk":
            returns = np.random.normal(drift, vol, n_periods)
        elif pattern == "trending":
            base_returns = np.random.normal(drift * 2, vol * 0.8, n_periods)
            trend_component = np.linspace(0, 0.001, n_periods)
            returns = base_returns + trend_component
        elif pattern == "mean_reverting":
            returns = []
            price = base_price
            for i in range(n_periods):
                # Mean reversion toward base_price
                reversion_force = (base_price - price) / base_price * 0.01
                random_component = np.random.normal(0, vol)
                ret = drift + reversion_force + random_component
                returns.append(ret)
                price *= 1 + ret
            returns = np.array(returns)
        elif pattern == "volatile":
            # Higher volatility with occasional spikes
            base_returns = np.random.normal(drift, vol * 1.5, n_periods)
            spike_probability = 0.05
            spikes = np.random.binomial(
                1,
                spike_probability,
                n_periods,
            ) * np.random.normal(0, vol * 3, n_periods)
            returns = base_returns + spikes
        else:
            returns = np.random.normal(drift, vol, n_periods)

        # Generate OHLC data from returns
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        # Create OHLC from close prices
        opens = prices[:-1] + [prices[-1]]  # Open = previous close (simplified)
        closes = prices

        # Generate realistic high/low based on intraday volatility
        intraday_vol = vol * 0.5  # Intraday volatility is typically lower
        highs = []
        lows = []

        for i in range(n_periods):
            daily_high_factor = 1 + abs(np.random.normal(0, intraday_vol))
            daily_low_factor = 1 - abs(np.random.normal(0, intraday_vol))

            # Ensure high >= max(open, close) and low <= min(open, close)
            base_high = max(opens[i], closes[i])
            base_low = min(opens[i], closes[i])

            high = max(base_high, base_high * daily_high_factor)
            low = min(base_low, base_low * daily_low_factor)

            highs.append(high)
            lows.append(low)

        # Generate volume data
        base_volume = 1_000_000
        volume_volatility = 0.3
        volumes = []
        for i in range(n_periods):
            # Volume tends to be higher on high volatility days
            price_change = abs(returns[i]) if i < len(returns) else 0
            volume_multiplier = (
                1 + (price_change / vol) * 0.5
            )  # Volume increases with price volatility
            volume = (
                base_volume
                * volume_multiplier
                * (1 + np.random.normal(0, volume_volatility))
            )
            volumes.append(max(int(volume), 100_000))  # Minimum volume

        # Create DataFrame
        return pl.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": volumes,
            },
        )

    def create_multi_ticker_data(
        self,
        tickers: list[str],
        start_date: str | datetime = "2023-01-01",
        end_date: str | datetime = "2023-12-31",
        frequency: str = "D",
        base_prices: dict[str, float] | None = None,
        correlations: dict[tuple[str, str], float] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """
        Generate correlated price data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data generation
            end_date: End date for data generation
            frequency: Data frequency
            base_prices: Starting prices for each ticker
            correlations: Pairwise correlations between tickers

        Returns:
            Dictionary mapping tickers to DataFrames
        """
        if not tickers:
            return {}

        base_prices = base_prices or {}
        correlations = correlations or {}

        # Generate independent random series for each ticker
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Generate date range
        if frequency == "D":
            dates = pl.date_range(start_date, end_date, interval="1d", eager=True)
        elif frequency == "H":
            dates = pl.date_range(start_date, end_date, interval="1h", eager=True)
        elif frequency == "4H":
            dates = pl.date_range(start_date, end_date, interval="4h", eager=True)
        else:
            msg = f"Unsupported frequency: {frequency}"
            raise ValueError(msg)

        n_periods = len(dates)
        n_tickers = len(tickers)

        # Generate correlated random returns
        # Create correlation matrix
        corr_matrix = np.eye(n_tickers)
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i != j:
                    key = (
                        (ticker1, ticker2) if ticker1 < ticker2 else (ticker2, ticker1)
                    )
                    corr_matrix[i, j] = correlations.get(key, self.market_correlation)

        # Generate correlated returns using Cholesky decomposition
        independent_returns = np.random.normal(
            0,
            self.base_volatility,
            (n_periods, n_tickers),
        )

        try:
            chol = np.linalg.cholesky(corr_matrix)
            correlated_returns = np.dot(independent_returns, chol.T)
        except np.linalg.LinAlgError:
            # Fallback to independent returns if correlation matrix is not positive definite
            correlated_returns = independent_returns

        # Add drift
        for i in range(n_tickers):
            correlated_returns[:, i] += self.daily_drift

        # Generate individual ticker data
        ticker_data = {}
        for i, ticker in enumerate(tickers):
            base_price = base_prices.get(
                ticker,
                100.0 + i * 10,
            )  # Slight price variation

            # Generate prices from returns
            prices = [base_price]
            for ret in correlated_returns[:, i]:
                prices.append(prices[-1] * (1 + ret))

            # Create OHLC from close prices (simplified approach for testing)
            opens = prices[:-1]
            closes = prices[1:]

            # Generate highs and lows
            highs = []
            lows = []
            intraday_vol = self.base_volatility * 0.5

            for j in range(n_periods):
                high_factor = 1 + abs(np.random.normal(0, intraday_vol))
                low_factor = 1 - abs(np.random.normal(0, intraday_vol))

                base_high = max(opens[j], closes[j])
                base_low = min(opens[j], closes[j])

                high = base_high * high_factor
                low = base_low * low_factor

                highs.append(high)
                lows.append(low)

            # Generate volume
            base_volume = 1_000_000 * (1 + i * 0.2)  # Different base volumes
            volumes = []
            for j in range(n_periods):
                volume_multiplier = (
                    1 + abs(correlated_returns[j, i]) / self.base_volatility * 0.5
                )
                volume = (
                    base_volume * volume_multiplier * (1 + np.random.normal(0, 0.3))
                )
                volumes.append(max(int(volume), 100_000))

            # Create DataFrame for this ticker
            ticker_data[ticker] = pl.DataFrame(
                {
                    "Date": dates,
                    "Open": opens,
                    "High": highs,
                    "Low": lows,
                    "Close": closes,
                    "Volume": volumes,
                },
            )

        return ticker_data

    def create_yfinance_compatible_data(
        self,
        tickers: str | list[str],
        start_date: str | datetime = "2023-01-01",
        end_date: str | datetime = "2023-12-31",
        frequency: str = "D",
    ) -> pd.DataFrame:
        """
        Generate data in yfinance-compatible format with MultiIndex columns.

        Args:
            tickers: Single ticker or list of tickers
            start_date: Start date
            end_date: End date
            frequency: Data frequency

        Returns:
            Pandas DataFrame with MultiIndex columns matching yfinance format
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        # Generate data for all tickers
        ticker_data = self.create_multi_ticker_data(
            tickers,
            start_date,
            end_date,
            frequency,
        )

        if len(tickers) == 1:
            # Single ticker - return with simple column names
            ticker = tickers[0]
            df = ticker_data[ticker].to_pandas()
            df = df.set_index("Date")
            return df
        # Multiple tickers - create MultiIndex columns
        all_data = {}
        dates = None

        for ticker in tickers:
            df = ticker_data[ticker].to_pandas()
            if dates is None:
                dates = df["Date"]

            for col in ["Open", "High", "Low", "Close", "Volume"]:
                all_data[(col, ticker)] = df[col].values

        # Create MultiIndex columns
        result_df = pd.DataFrame(all_data, index=dates)
        result_df.columns = pd.MultiIndex.from_tuples(
            result_df.columns,
            names=[None, None],
        )
        result_df.index.name = "Date"

        return result_df

    def create_strategy_test_data(
        self,
        ticker: str = "AAPL",
        periods: int = 252,  # ~1 year of trading days
        pattern: str = "trending_with_signals",
    ) -> pl.DataFrame:
        """
        Create data specifically designed for strategy testing with clear signals.

        Args:
            ticker: Ticker symbol
            periods: Number of periods to generate
            pattern: Pattern type for clear signal generation

        Returns:
            DataFrame optimized for strategy testing
        """
        # Generate base dates
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(periods)]

        base_price = 100.0

        if pattern == "trending_with_signals":
            # Create data with clear trending phases for MA crossover signals
            prices = []
            current_price = base_price

            for i in range(periods):
                # Create alternating trending phases
                cycle_position = (i // 50) % 4  # Change trend every 50 periods

                if cycle_position == 0:  # Uptrend
                    drift = 0.002
                    vol = 0.015
                elif cycle_position == 1:  # Sideways/consolidation
                    drift = 0.0001
                    vol = 0.008
                elif cycle_position == 2:  # Downtrend
                    drift = -0.0015
                    vol = 0.018
                else:  # Recovery
                    drift = 0.0025
                    vol = 0.012

                # Add some noise
                daily_return = np.random.normal(drift, vol)
                current_price *= 1 + daily_return
                prices.append(current_price)

        else:
            # Default to simple random walk
            returns = np.random.normal(0.0005, 0.02, periods)
            prices = [base_price]
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            prices = prices[1:]  # Remove extra element

        # Generate OHLC
        opens = [base_price] + prices[:-1]
        closes = prices

        # Simple high/low generation
        highs = [
            max(o, c) * (1 + abs(np.random.normal(0, 0.005)))
            for o, c in zip(opens, closes, strict=False)
        ]
        lows = [
            min(o, c) * (1 - abs(np.random.normal(0, 0.005)))
            for o, c in zip(opens, closes, strict=False)
        ]

        # Volume
        volumes = [
            int(1_000_000 * (1 + np.random.normal(0, 0.3))) for _ in range(periods)
        ]
        volumes = [max(v, 100_000) for v in volumes]  # Ensure minimum volume

        return pl.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": volumes,
            },
        )


# Convenience functions for common use cases
def create_stable_price_data(
    ticker: str = "AAPL",
    days: int = 365,
    start_price: float = 100.0,
    volatility: float = 0.02,
    pattern: str = "random_walk",
) -> pl.DataFrame:
    """Create stable price data for testing - convenience function."""
    factory = MarketDataFactory(seed=42)
    end_date = datetime(2023, 1, 1) + timedelta(days=days)

    return factory.create_price_data(
        ticker=ticker,
        start_date="2023-01-01",
        end_date=end_date.strftime("%Y-%m-%d"),
        base_price=start_price,
        volatility=volatility,
        pattern=pattern,
    )


def create_multi_asset_data(
    tickers: list[str],
    days: int = 365,
    correlation: float = 0.6,
) -> dict[str, pl.DataFrame]:
    """Create correlated multi-asset data - convenience function."""
    factory = MarketDataFactory(seed=42)
    end_date = datetime(2023, 1, 1) + timedelta(days=days)

    # Create correlation dict
    correlations = {}
    for i, ticker1 in enumerate(tickers):
        for _j, ticker2 in enumerate(tickers[i + 1 :], i + 1):
            key = (ticker1, ticker2) if ticker1 < ticker2 else (ticker2, ticker1)
            correlations[key] = correlation

    return factory.create_multi_ticker_data(
        tickers=tickers,
        start_date="2023-01-01",
        end_date=end_date.strftime("%Y-%m-%d"),
        correlations=correlations,
    )


def mock_yfinance_download(tickers, start=None, end=None, interval="1d", **kwargs):
    """Mock function to replace yfinance.download calls in tests."""
    factory = MarketDataFactory(seed=42)

    start_date = start or "2023-01-01"
    end_date = end or "2023-12-31"

    # Convert interval to frequency
    freq_map = {"1d": "D", "1h": "H", "4h": "4H"}
    frequency = freq_map.get(interval, "D")

    return factory.create_yfinance_compatible_data(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
    )
