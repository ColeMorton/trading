"""
Signal Generation Module

This module handles the generation of trading signals based on
MACD cross strategy parameters.
"""

from typing import Callable, Dict, Optional

import polars as pl

from app.tools.export_csv import export_csv
from app.tools.get_config import get_config
from app.tools.get_data import get_data


def calculate_macd(
    data: pl.DataFrame, short_window: int, long_window: int, signal_window: int
) -> pl.DataFrame:
    """Calculate MACD and Signal line values.

    Args:
        data: Price data DataFrame
        short_window: Short-term EMA period
        long_window: Long-term EMA period
        signal_window: Signal line EMA period

    Returns:
        DataFrame with MACD indicators added
    """
    print(
        f"Calculating MACD with short EMA {short_window}, long EMA {long_window}, signal EMA {signal_window}"
    )

    # Calculate EMAs
    data = data.with_columns(
        [
            pl.col("Close").ewm_mean(span=short_window).alias("EMA_short"),
            pl.col("Close").ewm_mean(span=long_window).alias("EMA_long"),
        ]
    )

    # Count valid EMA points
    valid_short_ema = data.select(pl.col("EMA_short").is_not_null()).sum().item()
    valid_long_ema = data.select(pl.col("EMA_long").is_not_null()).sum().item()
    print(f"Valid EMA points - Short: {valid_short_ema}, Long: {valid_long_ema}")

    # Calculate MACD line
    data = data.with_columns([(pl.col("EMA_short") - pl.col("EMA_long")).alias("MACD")])

    # Calculate Signal line
    data = data.with_columns(
        [pl.col("MACD").ewm_mean(span=signal_window).alias("Signal_Line")]
    )

    # Count valid MACD and Signal Line points
    valid_macd = data.select(pl.col("MACD").is_not_null()).sum().item()
    valid_signal = data.select(pl.col("Signal_Line").is_not_null()).sum().item()
    print(f"Valid MACD points: {valid_macd}, Valid Signal Line points: {valid_signal}")

    return data


def generate_macd_signals(data: pl.DataFrame, config: Dict) -> Optional[pl.DataFrame]:
    """Generate trading signals based on MACD cross strategy parameters.

    Args:
        data: Price data DataFrame
        config: Configuration dictionary with strategy parameters

    Returns:
        DataFrame with added signal columns or None if calculation fails
    """
    try:
        if data is None or len(data) == 0:
            return None

        short_window = config.get("short_window", 12)
        long_window = config.get("long_window", 26)
        signal_window = config.get("signal_window", 9)
        direction = config.get("DIRECTION", "Long").lower()

        # Log analysis parameters
        print(
            f"Analyzing windows - Short: {short_window}, Long: {long_window}, Signal: {signal_window}"
        )
        print(
            f"Data length: {len(data)}, Required length: {max(short_window, long_window, signal_window)}"
        )
        print(
            f"Calculating {direction.capitalize()} MACD signals with short window {short_window}, long window {long_window}, and signal window {signal_window}"
        )
        print(f"Input data shape: {data.shape}")

        # Calculate MACD indicators
        data = calculate_macd(data, short_window, long_window, signal_window)

        # Initialize Signal column
        data = data.with_columns([pl.lit(0).cast(pl.Int32).alias("Signal")])

        # Generate signals based on direction
        if direction == "long":
            # Long: Enter when MACD crosses above Signal Line
            data = data.with_columns(
                [
                    pl.when(
                        (pl.col("MACD") > pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                    )
                    .then(1)  # Enter long
                    .when(
                        (pl.col("MACD") < pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
                    )
                    .then(0)  # Exit long
                    .otherwise(pl.col("Signal"))
                    .alias("Signal")
                ]
            )
        else:
            # Short: Enter when MACD crosses below Signal Line
            data = data.with_columns(
                [
                    pl.when(
                        (pl.col("MACD") < pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
                    )
                    .then(-1)  # Enter short
                    .when(
                        (pl.col("MACD") > pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                    )
                    .then(0)  # Exit short
                    .otherwise(pl.col("Signal"))
                    .alias("Signal")
                ]
            )

        # Forward fill signals between crossovers
        data = data.with_columns(
            [pl.col("Signal").forward_fill().fill_null(0).alias("Signal")]
        )

        # Log signal conversion statistics
        non_zero_signals = data.filter(pl.col("Signal") != 0).height
        print(
            f"Windows {short_window}, {long_window}, {signal_window}: {non_zero_signals} signals generated"
        )

        # Check if there's a current entry or exit signal
        last_row = data.tail(1)
        current_signal = last_row.select("Signal").item() != 0

        # Determine if there's an exit signal (MACD crossing Signal Line in
        # opposite direction)
        if direction == "long":
            exit_signal = (
                last_row.select("MACD").item() < last_row.select("Signal_Line").item()
                and data.tail(2).head(1).select("MACD").item()
                >= data.tail(2).head(1).select("Signal_Line").item()
            )
        else:
            exit_signal = (
                last_row.select("MACD").item() > last_row.select("Signal_Line").item()
                and data.tail(2).head(1).select("MACD").item()
                <= data.tail(2).head(1).select("Signal_Line").item()
            )

        print(
            f"Windows {short_window}, {long_window}, {signal_window}: Entry signal: {current_signal}, Exit signal: {exit_signal}"
        )

        return data

    except Exception as e:
        print(f"Signal generation error: {str(e)}")
        return None


def get_current_signals(
    data: pl.DataFrame, config: Dict, log: Callable
) -> pl.DataFrame:
    """Get current signals for MACD parameter combinations.

    Args:
        data: Price data DataFrame
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame containing parameter combinations with current signals
    """
    try:
        signals = []

        # Generate parameter combinations with STEP
        step = config.get("STEP", 2)  # Default to 2 if not specified

        # Use the specific config parameters with appropriate defaults
        short_window_start = config.get("SHORT_WINDOW_START", 2)
        short_window_end = config.get("SHORT_WINDOW_END", 18)
        long_window_start = config.get("LONG_WINDOW_START", 4)
        long_window_end = config.get("LONG_WINDOW_END", 36)
        signal_window_start = config.get("SIGNAL_WINDOW_START", 2)
        signal_window_end = config.get("SIGNAL_WINDOW_END", 18)

        for short_window in range(short_window_start, short_window_end + 1, step):
            for long_window in range(long_window_start, long_window_end + 1, step):
                if long_window <= short_window:
                    continue

                for signal_window in range(
                    signal_window_start, signal_window_end + 1, step
                ):
                    try:
                        temp_config = config.copy()
                        temp_config.update(
                            {
                                "short_window": short_window,
                                "long_window": long_window,
                                "signal_window": signal_window,
                            }
                        )

                        temp_data = generate_macd_signals(data.clone(), temp_config)

                        if temp_data is not None and len(temp_data) > 0:
                            last_signal = temp_data.tail(1).select("Signal").item()
                            if last_signal != 0:  # If there's an active signal
                                signals.append(
                                    {
                                        "Short Window": short_window,
                                        "Long Window": long_window,
                                        "Signal Window": signal_window,
                                        "Signal": last_signal,
                                    }
                                )

                    except Exception as e:
                        log(
                            f"Failed to process parameters {short_window}/{long_window}/{signal_window}: {str(e)}",
                            "warning",
                        )
                        continue

        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(signals)
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32,
                "Signal Window": pl.Int32,
                "Signal": pl.Int32,
            }
        )

    except Exception as e:
        log(f"Failed to get current signals: {str(e)}", "error")
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32,
                "Signal Window": pl.Int32,
                "Signal": pl.Int32,
            }
        )


def generate_current_signals(config: Dict, log: Callable) -> pl.DataFrame:
    """Generate current trading signals based on MACD parameters.

    Args:
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame containing current signals with parameters
    """
    try:
        config = get_config(config)

        data = get_data(config["TICKER"], config, log)
        if data is None:
            log("Failed to get price data", "error")
            return pl.DataFrame(
                schema={
                    "Short Window": pl.Int32,
                    "Long Window": pl.Int32,
                    "Signal Window": pl.Int32,
                    "Signal": pl.Int32,
                }
            )

        current_signals = get_current_signals(data, config, log)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "macd_cross", config, "current_signals")

            if len(current_signals) == 0:
                print("No signals found for today")

        return current_signals

    except Exception as e:
        log(f"Failed to generate current signals: {str(e)}", "error")
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32,
                "Signal Window": pl.Int32,
                "Signal": pl.Int32,
            }
        )
