"""
ATR Signal Processing Module for MA Cross Strategy

This module provides hybrid signal generation combining MA Cross entry signals
with ATR Trailing Stop exit signals, enabling optimization of exit timing
while preserving proven MA Cross entry strategies.
"""

from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from app.tools.calculate_atr import calculate_atr, calculate_atr_trailing_stop
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals


def calculate_sma_signals(
    data: pd.DataFrame,
    ma_config: dict[str, Any],
) -> pd.DataFrame:
    """
    Calculate SMA signals for MA Cross strategy.

    This is a lightweight wrapper around calculate_ma_and_signals that provides
    a dedicated interface for SMA signal generation, as expected by test suites.

    Args:
        data: Price data DataFrame with OHLCV columns
        ma_config: MA configuration with FAST_PERIOD, SLOW_PERIOD, USE_SMA

    Returns:
        DataFrame with MA signals and position columns added
    """
    if data is None or data.empty:
        return None

    try:
        # Ensure data is in the right format for calculate_ma_and_signals
        if not isinstance(data, pl.DataFrame):
            # Convert pandas to polars for the calculation
            data_pl = pl.from_pandas(
                data.reset_index() if hasattr(data, "index") else data,
            )
        else:
            data_pl = data

        # Extract strategy type from config
        strategy_type = "SMA" if ma_config.get("USE_SMA", True) else "EMA"

        # Use existing calculate_ma_and_signals function
        result_pl = calculate_ma_and_signals(
            data_pl,
            ma_config["FAST_PERIOD"],
            ma_config["SLOW_PERIOD"],
            ma_config,
            lambda msg, level="info": None,  # Simple logger for wrapper
            strategy_type,
        )

        if result_pl is None:
            return None

        # Convert back to pandas if that's what was passed in
        if isinstance(data, pd.DataFrame):
            result = result_pl.to_pandas()
            # Restore index if original had one
            if hasattr(data, "index") and "Date" in result.columns:
                result = result.set_index("Date")
            return result
        return result_pl

    except Exception:
        # For testing purposes, if this function fails, return None gracefully
        return None


def generate_hybrid_ma_atr_signals(
    data: pd.DataFrame,
    ma_config: dict[str, Any],
    atr_length: int,
    atr_multiplier: float,
    log: callable,
) -> pd.DataFrame:
    """
    Generate hybrid signals combining MA Cross entries with ATR Trailing Stop exits.

    Signal Logic:
    1. Entry: MA Cross (short MA crosses above long MA for long positions)
    2. Exit: ATR Trailing Stop OR opposite MA Cross (whichever occurs first)
    3. Position Management: Enter on MA cross, exit on ATR stop breach

    Args:
        data: Price data DataFrame with OHLCV columns
        ma_config: MA configuration with FAST_PERIOD, SLOW_PERIOD, USE_SMA
        atr_length: ATR calculation period (2-21)
        atr_multiplier: ATR multiplier for stop distance (1.5-10.0)
        log: Logging function

    Returns:
        DataFrame with hybrid signals and ATR trailing stop levels
    """
    log(
        f"Generating hybrid MA+ATR signals: MA({ma_config['FAST_PERIOD']}/{ma_config['SLOW_PERIOD']}) + ATR({atr_length}, {atr_multiplier})",
    )

    # Validate input data
    if data is None:
        log("Input data is None", "error")
        return None

    if data.empty:
        log("Input data is empty", "error")
        return None

    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Create working copy
    data = data.copy()

    # Ensure proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        if "Date" in data.columns:
            data = data.set_index("Date")
        else:
            data.index = pd.date_range(start="2000-01-01", periods=len(data), freq="D")
            log("Created dummy DatetimeIndex for data", "warning")

    # Step 1: Generate MA Cross signals for entries using the wrapper function
    data = calculate_sma_signals(data, ma_config)

    if data is None or len(data) == 0:
        log("MA signal generation failed", "error")
        return None

    # Step 2: Calculate ATR and apply trailing stop logic
    atr_values = calculate_atr(data, atr_length)
    if atr_values is None:
        log("ATR calculation failed", "error")
        return None
    data["ATR"] = atr_values

    # Initialize ATR-specific columns
    data["ATR_Trailing_Stop"] = pd.Series(np.full(len(data), np.nan), index=data.index)
    data["Highest_Since_Entry"] = pd.Series(
        np.full(len(data), np.nan),
        index=data.index,
    )
    data["ATR_Signal"] = pd.Series(np.zeros(len(data)), index=data.index)

    # Step 3: Combine MA entry and ATR exit signals
    data = _combine_ma_entry_atr_exit_signals(data, atr_length, atr_multiplier, log)

    log(f"Generated hybrid signals for {len(data)} data points")
    return data


def _combine_ma_entry_atr_exit_signals(
    data: pd.DataFrame,
    atr_length: int,
    atr_multiplier: float,
    log: callable,
) -> pd.DataFrame:
    """
    Combine MA Cross entry signals with ATR trailing stop exit logic.

    Args:
        data: DataFrame with MA signals and ATR calculated
        atr_length: ATR calculation period
        atr_multiplier: ATR multiplier for stop distance
        log: Logging function

    Returns:
        DataFrame with combined hybrid signals
    """
    # Get MA signals (entry logic)
    ma_entries = data.get("Signal", data.get("signal", pd.Series(np.zeros(len(data)))))

    # Initialize hybrid signal tracking
    hybrid_signal = pd.Series(np.zeros(len(data)), index=data.index)
    in_position = False

    # Process each bar for hybrid signal generation
    for i in range(1, len(data)):
        current_close = float(data["Close"].iloc[i])
        current_atr = float(data["ATR"].iloc[i])
        ma_signal = float(ma_entries.iloc[i])

        if not in_position:
            # Check for MA Cross entry signal
            if ma_signal == 1 and float(ma_entries.iloc[i - 1]) != 1:
                # MA Cross entry detected
                hybrid_signal.iloc[i] = 1
                data.loc[data.index[i], "ATR_Trailing_Stop"] = current_close - (
                    current_atr * atr_multiplier
                )
                data.loc[data.index[i], "Highest_Since_Entry"] = current_close
                in_position = True
                log(
                    f"Entry signal at {data.index[i]}: Close={current_close:.2f}, ATR Stop={current_close - (current_atr * atr_multiplier):.2f}",
                )
        else:
            # In position - manage ATR trailing stop
            prev_highest = float(data["Highest_Since_Entry"].iloc[i - 1])
            current_highest = max(prev_highest, current_close)
            data.loc[data.index[i], "Highest_Since_Entry"] = current_highest

            # Calculate new trailing stop
            prev_stop = float(data["ATR_Trailing_Stop"].iloc[i - 1])
            new_stop = calculate_atr_trailing_stop(
                current_close,
                current_atr,
                atr_multiplier,
                current_highest,
                prev_stop,
            )
            data.loc[data.index[i], "ATR_Trailing_Stop"] = new_stop

            # Check exit conditions
            exit_signal = False

            # ATR trailing stop exit
            if current_close < new_stop:
                exit_signal = True
                log(
                    f"ATR exit signal at {data.index[i]}: Close={current_close:.2f} < Stop={new_stop:.2f}",
                )

            # MA Cross exit (opposite signal)
            elif ma_signal == 0 and float(ma_entries.iloc[i - 1]) == 1:
                exit_signal = True
                log(f"MA exit signal at {data.index[i]}: MA Cross reversal")

            if exit_signal:
                hybrid_signal.iloc[i] = -1  # Exit signal should be -1, not 0
                in_position = False
            else:
                hybrid_signal.iloc[i] = 1

    # Update the main signal column with hybrid logic
    data["Signal"] = hybrid_signal
    data["Position"] = hybrid_signal.shift(1).fillna(0)

    return data


def create_atr_parameter_combinations(
    atr_length_range: tuple = (2, 22),  # 2 to 21 inclusive
    atr_multiplier_range: tuple = (1.5, 10.0),  # 1.5 to 10.0
    atr_multiplier_step: float = 0.2,
) -> list:
    """
    Generate ATR parameter combinations for sensitivity analysis.

    Args:
        atr_length_range: Tuple of (min, max) for ATR length (max is exclusive)
        atr_multiplier_range: Tuple of (min, max) for ATR multiplier (max is exclusive)
        atr_multiplier_step: Step size for ATR multiplier range

    Returns:
        List of (atr_length, atr_multiplier) tuples
    """
    # Length range is always exclusive upper bound
    atr_lengths = list(range(atr_length_range[0], atr_length_range[1]))

    # For multipliers, use exclusive upper bound for consistency
    # Handle edge case where min == max (single value)
    if atr_multiplier_range[0] == atr_multiplier_range[1]:
        atr_multipliers = [atr_multiplier_range[0]]
    else:
        # Calculate number of steps (exclusive of upper bound)
        # Add 1 to handle cases where steps don't divide evenly
        num_steps = (
            int(
                (atr_multiplier_range[1] - atr_multiplier_range[0])
                / atr_multiplier_step
            )
            + 1
        )

        # Generate multipliers manually to avoid float precision issues with np.arange
        # Filter to ensure all values are strictly less than max (exclusive upper bound)
        atr_multipliers = [
            round(atr_multiplier_range[0] + i * atr_multiplier_step, 1)
            for i in range(num_steps)
            if round(atr_multiplier_range[0] + i * atr_multiplier_step, 1)
            < atr_multiplier_range[1]
        ]

    combinations = []
    for length in atr_lengths:
        for multiplier in atr_multipliers:
            combinations.append((length, multiplier))

    return combinations


def validate_atr_parameters(
    atr_length: int,
    atr_multiplier: float,
) -> tuple[bool, str | None]:
    """
    Validate ATR parameters for signal generation.

    Args:
        atr_length: ATR calculation period
        atr_multiplier: ATR multiplier for stop distance

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(atr_length, int) or atr_length < 1:
        return False, "ATR length must be a positive integer"

    if atr_length > 100:
        return False, "ATR length too large (may reduce signal frequency)"

    if not isinstance(atr_multiplier, int | float) or atr_multiplier <= 0:
        return False, "ATR multiplier must be positive"

    if atr_multiplier > 20:
        return False, "ATR multiplier too large (may result in very wide stops)"

    return True, None


def convert_polars_to_pandas_for_atr(polars_data: pl.DataFrame) -> pd.DataFrame:
    """
    Convert Polars DataFrame to Pandas for ATR signal processing.

    Args:
        polars_data: Polars DataFrame with price data

    Returns:
        Pandas DataFrame ready for ATR processing
    """
    # Convert to pandas
    pandas_data = polars_data.to_pandas()

    # Ensure Date column handling
    if "Date" in pandas_data.columns:
        pandas_data["Date"] = pd.to_datetime(pandas_data["Date"])

    # Ensure numeric columns are proper types
    numeric_columns = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_columns:
        if col in pandas_data.columns:
            pandas_data[col] = pd.to_numeric(pandas_data[col], errors="coerce")

    return pandas_data
