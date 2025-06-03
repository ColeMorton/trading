"""ATR (Average True Range) calculation and signal generation.

This module provides functions for calculating ATR indicators and generating
trading signals based on ATR Trailing Stop strategy.
"""

import logging
from typing import Callable

import numpy as np
import pandas as pd


def calculate_atr(data: pd.DataFrame, length: int) -> pd.Series:
    """Calculate Average True Range (ATR) using vectorized operations.

    Args:
        data (pd.DataFrame): Price data with High, Low, Close columns
        length (int): ATR period length

    Returns:
        pd.Series: ATR values
    """
    # Vectorized calculation of true range components
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())

    # Create a DataFrame with the three components
    ranges = pd.DataFrame(
        {"HL": high_low, "HC": high_close, "LC": low_close}, index=data.index
    )

    # Calculate the true range as the maximum of the three components
    true_range = ranges.max(axis=1)

    # Use pandas rolling mean for the ATR calculation
    atr = true_range.rolling(window=length).mean()

    # Ensure the result has the same index as the input data
    return pd.Series(atr.values, index=data.index)


def calculate_atr_trailing_stop(
    close: float,
    atr: float,
    multiplier: float,
    highest_since_entry: float,
    previous_stop: float,
) -> float:
    """Calculate ATR Trailing Stop.

    Args:
        close (float): Current close price
        atr (float): Current ATR value
        multiplier (float): ATR multiplier
        highest_since_entry (float): Highest price since entry
        previous_stop (float): Previous stop level

    Returns:
        float: New trailing stop level
    """
    potential_stop: float = close - (atr * multiplier)
    if np.isnan(previous_stop):
        return potential_stop
    new_stop: float = highest_since_entry - (atr * multiplier)
    return max(new_stop, previous_stop)


def calculate_atr_signals(
    data: pd.DataFrame,
    atr_length: int,
    atr_multiplier: float,
    log: Callable[[str, str], None] = None,
) -> pd.DataFrame:
    """Generate trading signals based on ATR Trailing Stop.

    Args:
        data (pd.DataFrame): Price data with Open, High, Low, Close columns
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier
        log (Callable, optional): Logging function. Defaults to None.

    Returns:
        pd.DataFrame: Data with signals and positions
    """
    # Create a copy to avoid modifying the original
    data = data.copy()

    # Set up default logger if none provided
    if log is None:

        def log(msg, level="info"):
            if level == "error":
                logging.error(msg)
            elif level == "warning":
                logging.warning(msg)
            else:
                logging.info(msg)

    # Calculate ATR
    data["ATR"] = calculate_atr(data, atr_length)

    # Initialize columns
    data["Signal"] = 0
    data["ATR_Trailing_Stop"] = np.nan
    data["Highest_Since_Entry"] = np.nan

    # Log initial data shape and columns
    log(
        f"Initializing ATR calculation with data shape {data.shape} and columns {list(data.columns)}",
        "info",
    )
    # Process rows iteratively
    in_position = False

    # Process rows iteratively based on ATR strategy logic
    for i in range(1, len(data)):
        current_close = float(data["Close"].iloc[i])
        current_atr = float(data["ATR"].iloc[i])

        if not in_position:
            # Calculate ATR Stop
            atr_stop = current_close - (current_atr * atr_multiplier)

            # Entry condition: Price close greater than or equal to ATR Stop
            if current_close >= atr_stop:
                data.loc[data.index[i], "Signal"] = 1
                data.loc[data.index[i], "ATR_Trailing_Stop"] = atr_stop
                data.loc[data.index[i], "Highest_Since_Entry"] = current_close
                in_position = True
                log(
                    f"Entry signal at index {i}, price {current_close}, ATR stop {atr_stop}",
                    "info",
                )
        else:
            # Update highest price since entry
            prev_highest = float(data["Highest_Since_Entry"].iloc[i - 1])
            current_highest = max(prev_highest, current_close)
            data.loc[data.index[i], "Highest_Since_Entry"] = current_highest

            # Get previous stop
            prev_stop = float(data["ATR_Trailing_Stop"].iloc[i - 1])

            # Calculate new trailing stop
            new_stop = max(current_highest - (current_atr * atr_multiplier), prev_stop)
            data.loc[data.index[i], "ATR_Trailing_Stop"] = new_stop

            # Exit condition: Price close less than ATR Stop
            if current_close < new_stop:
                data.loc[data.index[i], "Signal"] = 0
                in_position = False
                log(
                    f"Exit signal at index {i}, price {current_close}, ATR stop {new_stop}",
                    "info",
                )
            else:
                data.loc[data.index[i], "Signal"] = 1

    # Calculate position column
    data["Position"] = data["Signal"].shift(1).fillna(0).astype(int)

    # Log summary of ATR calculation results
    signal_count = data["Signal"].sum()
    position_count = data["Position"].sum()
    atr_stop_count = data["ATR_Trailing_Stop"].notna().sum()

    log(
        f"ATR calculation complete: {signal_count} signals, {position_count} position days, "
        f"{atr_stop_count} ATR stop values",
        "info",
    )

    # Log sample of ATR trailing stop values for debugging
    if atr_stop_count > 0:
        sample = data[data["ATR_Trailing_Stop"].notna()].head(5)
        log(
            f"Sample of ATR trailing stop values: {sample['ATR_Trailing_Stop'].tolist()}",
            "info",
        )
    else:
        log("WARNING: No ATR trailing stop values were calculated", "warning")

    return data
