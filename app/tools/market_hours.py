"""
Market Hours Detection and Trading Session Management.

This module provides market-aware data processing functionality to handle
the differences between 24/7 crypto markets and traditional stock market hours.
"""

from datetime import datetime, time
from enum import Enum
from zoneinfo import ZoneInfo

import pandas as pd
import polars as pl


class MarketType(Enum):
    """Enumeration of different market types with distinct trading characteristics."""

    CRYPTO = "crypto"  # 24/7 cryptocurrency markets
    US_STOCK = "us_stock"  # NYSE/NASDAQ traditional stock markets


class TradingHours:
    """Configuration for market trading hours and sessions."""

    def __init__(
        self, start_time: str, end_time: str, timezone: str, trading_days: list[int]
    ):
        """Initialize trading hours configuration.

        Args:
            start_time: Market open time in HH:MM format
            end_time: Market close time in HH:MM format
            timezone: Market timezone (e.g., 'America/New_York')
            trading_days: List of weekday integers (0=Monday, 6=Sunday)
        """
        self.start_time = time.fromisoformat(start_time)
        self.end_time = time.fromisoformat(end_time)
        self.timezone = ZoneInfo(timezone)
        self.trading_days = trading_days


# Trading hours configuration for different market types
TRADING_HOURS_CONFIG = {
    MarketType.US_STOCK: TradingHours(
        start_time="09:30",
        end_time="16:00",
        timezone="America/New_York",
        trading_days=[0, 1, 2, 3, 4],  # Monday through Friday
    ),
    MarketType.CRYPTO: TradingHours(
        start_time="00:00",
        end_time="23:59",
        timezone="UTC",
        trading_days=[0, 1, 2, 3, 4, 5, 6],  # All days (24/7)
    ),
}


def detect_market_type(ticker: str) -> MarketType:
    """Detect market type based on ticker symbol patterns.

    Args:
        ticker: Stock or cryptocurrency ticker symbol

    Returns:
        MarketType: Detected market type

    Examples:
        >>> detect_market_type("BTC-USD")
        MarketType.CRYPTO
        >>> detect_market_type("AAPL")
        MarketType.US_STOCK
    """
    ticker_upper = ticker.upper()

    # Crypto detection patterns
    if "-USD" in ticker_upper:
        return MarketType.CRYPTO

    # Default to US stock for traditional ticker symbols
    return MarketType.US_STOCK


def get_trading_hours(market_type: MarketType) -> TradingHours:
    """Get trading hours configuration for a market type.

    Args:
        market_type: Type of market to get hours for

    Returns:
        TradingHours: Trading hours configuration
    """
    return TRADING_HOURS_CONFIG[market_type]


def is_trading_hour(dt: datetime, market_type: MarketType) -> bool:
    """Check if a datetime falls within trading hours for the market type.

    Args:
        dt: Datetime to check (should be timezone-aware)
        market_type: Market type to check against

    Returns:
        bool: True if datetime is within trading hours
    """
    trading_hours = get_trading_hours(market_type)

    # Convert to market timezone
    market_dt = dt.astimezone(trading_hours.timezone)

    # Check if it's a trading day
    if market_dt.weekday() not in trading_hours.trading_days:
        return False

    # Check if it's within trading hours
    current_time = market_dt.time()
    return trading_hours.start_time <= current_time <= trading_hours.end_time


def filter_trading_hours_pandas(
    df: pd.DataFrame, market_type: MarketType
) -> pd.DataFrame:
    """Filter pandas DataFrame to only include trading hours data.

    Args:
        df: DataFrame with Date column containing datetime data
        market_type: Market type to filter for

    Returns:
        pd.DataFrame: Filtered DataFrame with only trading hours data
    """
    if market_type == MarketType.CRYPTO:
        # Crypto trades 24/7, return all data
        return df.copy()

    # Convert Date column to datetime if it's not already
    df_copy = df.copy()
    df_copy["Date"] = pd.to_datetime(df_copy["Date"])

    # Create boolean mask for trading hours
    trading_mask = df_copy["Date"].apply(lambda dt: is_trading_hour(dt, market_type))

    return df_copy[trading_mask].reset_index(drop=True)


def filter_trading_hours_polars(
    df: pl.DataFrame, market_type: MarketType
) -> pl.DataFrame:
    """Filter polars DataFrame to only include trading hours data.

    Args:
        df: DataFrame with Date column containing datetime data
        market_type: Market type to filter for

    Returns:
        pl.DataFrame: Filtered DataFrame with only trading hours data
    """
    if market_type == MarketType.CRYPTO:
        # Crypto trades 24/7, return all data
        return df.clone()

    trading_hours = get_trading_hours(market_type)

    # Convert to market timezone and filter
    filtered_df = (
        df.with_columns(
            [
                pl.col("Date")
                .dt.convert_time_zone(str(trading_hours.timezone))
                .alias("MarketTime")
            ]
        )
        .filter(
            # Filter by trading days (Monday=1, Sunday=7 in Polars)
            pl.col("MarketTime")
            .dt.weekday()
            .is_in([d + 1 for d in trading_hours.trading_days])
            &
            # Filter by trading hours
            (pl.col("MarketTime").dt.hour() > trading_hours.start_time.hour)
            | (
                (pl.col("MarketTime").dt.hour() == trading_hours.start_time.hour)
                & (pl.col("MarketTime").dt.minute() >= trading_hours.start_time.minute)
            )
            & (pl.col("MarketTime").dt.hour() < trading_hours.end_time.hour)
            | (
                (pl.col("MarketTime").dt.hour() == trading_hours.end_time.hour)
                & (pl.col("MarketTime").dt.minute() <= trading_hours.end_time.minute)
            )
        )
        .drop("MarketTime")
    )

    return filtered_df


def filter_trading_hours(
    df: pd.DataFrame | pl.DataFrame, market_type: MarketType
) -> pd.DataFrame | pl.DataFrame:
    """Filter DataFrame to only include trading hours data (supports both pandas and polars).

    Args:
        df: DataFrame with Date column containing datetime data
        market_type: Market type to filter for

    Returns:
        DataFrame: Filtered DataFrame with only trading hours data (same type as input)
    """
    if isinstance(df, pd.DataFrame):
        return filter_trading_hours_pandas(df, market_type)
    if isinstance(df, pl.DataFrame):
        return filter_trading_hours_polars(df, market_type)
    raise TypeError(f"Unsupported DataFrame type: {type(df)}")


def validate_4hour_bars(
    df: pd.DataFrame | pl.DataFrame, market_type: MarketType
) -> dict[str, bool | int | str]:
    """Validate that 4-hour bars are appropriate for the market type.

    Args:
        df: DataFrame with 4-hour OHLC data
        market_type: Market type to validate against

    Returns:
        Dict with validation results including bar count, alignment, and recommendations
    """
    results = {
        "is_valid": True,
        "bar_count": 0,
        "expected_bars_per_day": 0,
        "alignment_check": "passed",
        "recommendation": "data_is_valid",
        "issues": [],
    }

    if isinstance(df, pl.DataFrame):
        bar_count = len(df)
    else:
        bar_count = len(df)

    results["bar_count"] = bar_count

    if market_type == MarketType.CRYPTO:
        # Crypto: 24/7 trading, expect 6 bars per day (24 hours / 4 hours)
        results["expected_bars_per_day"] = 6
        results["recommendation"] = "optimal_for_crypto_analysis"

    elif market_type == MarketType.US_STOCK:
        # Stocks: ~6.5 hours trading day, expect ~1.6 bars per day
        # (9:30 AM - 4:00 PM = 6.5 hours / 4 hours = 1.625 bars)
        results["expected_bars_per_day"] = 1.6

        # Check for potential volume/signal quality issues
        if bar_count > 0:
            # For stocks, recommend checking volume patterns
            results["recommendation"] = "validate_volume_patterns"
            results["issues"].append(
                "Stock 4-hour bars may include after-hours data - validate volume consistency"
            )

            # Additional validation could be added here to check actual bar timestamps
            # against trading hours

    return results


def get_market_session_boundaries(market_type: MarketType) -> list[time]:
    """Get 4-hour session boundaries for a market type.

    Args:
        market_type: Market type to get session boundaries for

    Returns:
        List[time]: List of session boundary times
    """
    if market_type == MarketType.CRYPTO:
        # Standard 4-hour UTC boundaries for crypto
        return [
            time(0, 0),  # 00:00
            time(4, 0),  # 04:00
            time(8, 0),  # 08:00
            time(12, 0),  # 12:00
            time(16, 0),  # 16:00
            time(20, 0),  # 20:00
        ]
    # US_STOCK
    # Trading-hour aligned boundaries for stocks (ET)
    return [
        time(9, 30),  # 09:30 (market open)
        time(13, 30),  # 13:30 (4-hour mark)
        time(16, 0),  # 16:00 (market close)
    ]


def validate_market_hours_data(
    df: pd.DataFrame | pl.DataFrame, market_type: MarketType
) -> dict[str, bool | int | float]:
    """Validate that DataFrame contains appropriate market hours data.

    Args:
        df: DataFrame with Date column containing datetime data
        market_type: Market type to validate against

    Returns:
        Dict[str, Union[bool, int, float]]: Validation results with various checks
    """
    results = {
        "has_after_hours": False,
        "has_weekend_data": False,
        "has_appropriate_volume": True,
        "timezone_consistent": True,
        "total_records": 0,
        "trading_hours_records": 0,
        "after_hours_percentage": 0.0,
        "weekend_percentage": 0.0,
        "validation_passed": True,
    }

    if isinstance(df, pl.DataFrame):
        total_records = len(df)
        results["total_records"] = total_records

        if total_records == 0:
            results["validation_passed"] = False
            return results

        # Convert Date column to datetime if needed
        try:
            df_datetime = df.with_columns(
                [pl.col("Date").str.to_datetime().alias("Date_dt")]
            )
        except Exception:
            # Assume it's already datetime
            df_datetime = df.with_columns([pl.col("Date").alias("Date_dt")])
    else:  # pandas DataFrame
        total_records = len(df)
        results["total_records"] = total_records

        if total_records == 0:
            results["validation_passed"] = False
            return results

        df_copy = df.copy()
        df_copy["Date_dt"] = pd.to_datetime(df_copy["Date"])

    if market_type == MarketType.US_STOCK:
        get_trading_hours(market_type)

        if isinstance(df, pl.DataFrame):
            # Check for weekend data (Saturday=6, Sunday=7 in polars weekday)
            weekend_mask = df_datetime.with_columns(
                [pl.col("Date_dt").dt.weekday().is_in([6, 7]).alias("is_weekend")]
            )
            weekend_count = weekend_mask.filter(pl.col("is_weekend")).height

            # Check for after-hours data (convert to ET first)
            et_data = df_datetime.with_columns(
                [
                    pl.col("Date_dt")
                    .dt.convert_time_zone("America/New_York")
                    .alias("Date_et")
                ]
            )

            # Check for data outside trading hours (9:30 AM - 4:00 PM ET)
            after_hours_mask = et_data.with_columns(
                [
                    (
                        (pl.col("Date_et").dt.hour() < 9)
                        | (
                            (pl.col("Date_et").dt.hour() == 9)
                            & (pl.col("Date_et").dt.minute() < 30)
                        )
                        | (pl.col("Date_et").dt.hour() >= 16)
                    ).alias("is_after_hours")
                ]
            )
            after_hours_count = after_hours_mask.filter(pl.col("is_after_hours")).height

            # Calculate trading hours records
            trading_hours_count = total_records - weekend_count - after_hours_count

        else:  # pandas DataFrame
            # Convert to ET timezone
            df_copy["Date_et"] = df_copy["Date_dt"].dt.tz_convert("America/New_York")

            # Check for weekend data
            weekend_mask = df_copy["Date_et"].dt.weekday >= 5  # Saturday=5, Sunday=6
            weekend_count = weekend_mask.sum()

            # Check for after-hours data
            after_hours_mask = (
                (df_copy["Date_et"].dt.hour < 9)
                | (
                    (df_copy["Date_et"].dt.hour == 9)
                    & (df_copy["Date_et"].dt.minute < 30)
                )
                | (df_copy["Date_et"].dt.hour >= 16)
            )
            after_hours_count = after_hours_mask.sum()

            # Calculate trading hours records
            trading_hours_count = total_records - weekend_count - after_hours_count

        # Update results
        results["has_weekend_data"] = weekend_count > 0
        results["has_after_hours"] = after_hours_count > 0
        results["trading_hours_records"] = trading_hours_count
        results["weekend_percentage"] = (
            (weekend_count / total_records) * 100 if total_records > 0 else 0
        )
        results["after_hours_percentage"] = (
            (after_hours_count / total_records) * 100 if total_records > 0 else 0
        )

        # Validation fails if more than 10% of data is after-hours for stocks
        if results["after_hours_percentage"] > 10.0:
            results["validation_passed"] = False

    else:  # CRYPTO - 24/7 trading, all data should be valid
        results["trading_hours_records"] = total_records
        results["validation_passed"] = True

    return results
