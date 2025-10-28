"""
Signal Utilities Module

This module provides utilities for working with trading signals,
including functions for checking signal currency and matching signals.
"""

from datetime import date, timedelta
from pathlib import Path

import polars as pl


# Cache for last trading day
_LAST_TRADING_DAY = None


def set_last_trading_day(last_date: date) -> None:
    """Set the cached last trading day.

    Args:
        last_date: The last trading day to cache
    """
    global _LAST_TRADING_DAY
    _LAST_TRADING_DAY = last_date


def get_last_trading_day(today: date = date.today()) -> date:
    """
    Get the last trading day before the given date.

    Args:
        today: The reference date to find the last trading day from

    Returns:
        date: The last trading day
    """
    global _LAST_TRADING_DAY

    # Use cached value if available
    if _LAST_TRADING_DAY is not None:
        return _LAST_TRADING_DAY

    # Fallback to calendar logic
    if today.weekday() == 0:  # Monday
        return today - timedelta(days=3)
    if today.weekday() == 6:  # Sunday
        return today - timedelta(days=2)
    return today - timedelta(days=1)


def is_signal_current(signals: pl.DataFrame, config: dict | None = None) -> bool:
    """
    Check if there is a valid signal on the last trading day.
    A valid signal is when the fast MA is above the slow MA (for longs)
    or below the slow MA (for shorts) on the last trading day.

    Args:
        signals: DataFrame containing Signal, Position, MA_FAST, MA_SLOW and Date/Datetime columns
        config: Configuration dictionary containing direction information

    Returns:
        bool: True if there is a valid signal from the last trading day, False otherwise
    """
    if len(signals) == 0:
        return False

    last_row = signals.tail(1)

    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()

    # Check if we have a valid entry signal in the last row based on direction
    if config and config.get("DIRECTION", "Long") == "Short":
        return signal == -1 and position == 0
    return signal == 1 and position == 0


def is_exit_signal_current(signals: pl.DataFrame, config: dict | None = None) -> bool:
    """
    Check if there is a valid exit signal on the last trading day.
    A valid exit signal is when the fast MA is below the slow MA (for longs)
    or above the slow MA (for shorts) on the last trading day, and there is
    an existing position.

    Args:
        signals: DataFrame containing Signal, Position, MA_FAST, MA_SLOW and Date/Datetime columns
        config: Configuration dictionary containing direction information

    Returns:
        bool: True if there is a valid exit signal from the last trading day, False otherwise
    """
    if len(signals) == 0:
        return False

    last_row = signals.tail(1)

    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()

    # Check if we have a valid exit signal in the last row based on direction
    if config and config.get("DIRECTION", "Long") == "Short":
        return signal == 0 and position == -1
    return signal == 0 and position == 1


def check_signal_match(signals: list[dict], fast_window: int, slow_window: int) -> bool:
    """
    Check if any signal matches the given window combination.

    Args:
        signals: List of signal dictionaries containing window information
        fast_window: Fast window value to match
        slow_window: Slow window value to match

    Returns:
        bool: True if a matching signal is found, False otherwise
    """
    if not signals:
        return False

    return any(
        # Support both new and legacy column names
        (
            signal.get("Fast Period", signal.get("Fast Period")) == fast_window
            and signal.get("Slow Period", signal.get("Slow Period")) == slow_window
        )
        for signal in signals
    )


def calculate_signal_unconfirmed(
    signals: pl.DataFrame,
    config: dict | None = None,
) -> str:
    """
    Calculate what signal would be produced if the current price bar closes at the current price.

    This function analyzes the current moving average positions and determines if a crossover
    signal would be triggered if the current bar closed at the current price.

    Args:
        signals: DataFrame containing MA_FAST, MA_SLOW, Position, and signal data
        config: Configuration dictionary containing direction information

    Returns:
        str: "Entry" if entry signal would be produced, "Exit" if exit signal would be produced, "None" otherwise
    """
    if len(signals) == 0:
        return "None"

    # Get the last row
    last_row = signals.tail(1)

    # Check if we have the required columns
    required_columns = ["MA_FAST", "MA_SLOW", "Position"]
    for col in required_columns:
        if col not in signals.columns:
            return "None"

    try:
        # Check if signals are already confirmed - if so, return None
        if "Signal Entry" in signals.columns:
            signal_entry = last_row.get_column("Signal Entry").item()
            if signal_entry is True:
                return "None"

        if "Signal Exit" in signals.columns:
            signal_exit = last_row.get_column("Signal Exit").item()
            if signal_exit is True:
                return "None"

        # Get current values
        fast_ma = last_row.get_column("MA_FAST").item()
        slow_ma = last_row.get_column("MA_SLOW").item()
        position = last_row.get_column("Position").item()

        # Check for valid MA values
        if fast_ma is None or slow_ma is None:
            return "None"

        # Get direction (default to Long)
        direction = config.get("DIRECTION", "Long") if config else "Long"

        # For Long positions
        if direction == "Long":
            # Entry signal: fast MA crosses above slow MA and no current position
            if fast_ma > slow_ma and position == 0:
                return "Entry"
            # Exit signal: fast MA crosses below slow MA and currently in position
            if fast_ma < slow_ma and position == 1:
                return "Exit"
        # For Short positions
        # Entry signal: fast MA crosses below slow MA and no current position
        elif fast_ma < slow_ma and position == 0:
            return "Entry"
        # Exit signal: fast MA crosses above slow MA and currently in position
        elif fast_ma > slow_ma and position == -1:
            return "Exit"

        return "None"

    except Exception:
        # If any error occurs, return None
        return "None"


def calculate_signal_unconfirmed_realtime(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_entry: bool,
    signal_exit: bool,
    total_open_trades: int,
    config: dict | None = None,
    signal_period: int | None = None,
) -> str:
    """
    Calculate what signal would be produced if the current price bar closes at the current price.

    This function uses real-time price data to calculate current MA values and determine
    if a crossover signal would be triggered.

    Args:
        ticker: Trading symbol (e.g., "SOL-USD")
        strategy_type: Strategy type ("SMA", "EMA", or "MACD")
        fast_period: Fast MA period
        slow_period: Slow MA period
        signal_entry: Whether entry signal is already confirmed
        signal_exit: Whether exit signal is already confirmed
        total_open_trades: Number of currently open trades
        config: Configuration dictionary containing direction information
        signal_period: Signal period for MACD strategies (ignored for SMA/EMA)

    Returns:
        str: "Entry" if entry signal would be produced, "Exit" if exit signal would be produced, "None" otherwise
    """
    try:
        # Check if signals are already confirmed - if so, return None
        if signal_entry or signal_exit:
            return "None"

        # Get current price data
        price_data_path = Path(f"data/raw/prices/{ticker}_D.csv")
        if not price_data_path.exists():
            return "None"

        # Read price data
        price_data = pl.read_csv(price_data_path)
        if len(price_data) < max(fast_period, slow_period):
            return "None"

        # Calculate current MA values based on strategy type
        if strategy_type == "SMA":
            current_data = price_data.with_columns(
                [
                    pl.col("Close")
                    .cast(pl.Float64)
                    .rolling_mean(window_size=fast_period)
                    .alias("MA_FAST"),
                    pl.col("Close")
                    .cast(pl.Float64)
                    .rolling_mean(window_size=slow_period)
                    .alias("MA_SLOW"),
                ],
            )
        elif strategy_type == "EMA":
            current_data = price_data.with_columns(
                [
                    pl.col("Close")
                    .cast(pl.Float64)
                    .ewm_mean(span=fast_period, adjust=False)
                    .alias("MA_FAST"),
                    pl.col("Close")
                    .cast(pl.Float64)
                    .ewm_mean(span=slow_period, adjust=False)
                    .alias("MA_SLOW"),
                ],
            )
        elif strategy_type == "MACD":
            # For MACD, use provided signal_period or default to 9
            actual_signal_period = signal_period if signal_period is not None else 9

            # Calculate MACD components
            current_data = (
                price_data.with_columns(
                    [
                        # Fast and Slow EMAs
                        pl.col("Close")
                        .cast(pl.Float64)
                        .ewm_mean(span=fast_period, adjust=False)
                        .alias("EMA_FAST"),
                        pl.col("Close")
                        .cast(pl.Float64)
                        .ewm_mean(span=slow_period, adjust=False)
                        .alias("EMA_SLOW"),
                    ],
                )
                .with_columns(
                    [
                        # MACD Line = Fast EMA - Slow EMA
                        (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
                    ],
                )
                .with_columns(
                    [
                        # Signal Line = EMA of MACD Line
                        pl.col("MACD_LINE")
                        .ewm_mean(span=actual_signal_period, adjust=False)
                        .alias("MACD_SIGNAL"),
                    ],
                )
                .with_columns(
                    [
                        # For consistency with MA logic, use MACD line as MA_FAST and Signal line as MA_SLOW
                        pl.col("MACD_LINE").alias("MA_FAST"),
                        pl.col("MACD_SIGNAL").alias("MA_SLOW"),
                    ],
                )
            )
        else:
            # For other strategies, return None
            return "None"

        # Get the latest MA values (current bar)
        last_row = current_data.tail(1)
        fast_ma = last_row.get_column("MA_FAST").item()
        slow_ma = last_row.get_column("MA_SLOW").item()

        # Check for valid MA values
        if fast_ma is None or slow_ma is None:
            return "None"

        # Determine current position from total_open_trades
        position = 1 if total_open_trades > 0 else 0

        # Get direction (default to Long)
        direction = config.get("DIRECTION", "Long") if config else "Long"

        # For Long positions
        if direction == "Long":
            # Entry signal: fast MA crosses above slow MA and no current position
            if fast_ma > slow_ma and position == 0:
                return "Entry"
            # Exit signal: fast MA crosses below slow MA and currently in position
            if fast_ma < slow_ma and position == 1:
                return "Exit"
        # For Short positions
        # Entry signal: fast MA crosses below slow MA and no current position
        elif fast_ma < slow_ma and position == 0:
            return "Entry"
        # Exit signal: fast MA crosses above slow MA and currently in position
        elif fast_ma > slow_ma and position == -1:
            return "Exit"

        return "None"

    except Exception:
        # If any error occurs, return None
        return "None"
