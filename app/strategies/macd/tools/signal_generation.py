"""
Signal Generation Module

This module handles the generation of trading signals based on
MACD cross strategy parameters.
"""

from typing import Callable, Dict, Optional

import polars as pl

from app.tools.export_csv import export_csv
from app.tools.get_data import get_data


def calculate_macd(
    data: pl.DataFrame, fast_period: int, slow_period: int, signal_period: int
) -> pl.DataFrame:
    """Calculate MACD and Signal line values.

    Args:
        data: Price data DataFrame
        fast_period: Fast-term EMA period
        slow_period: Slow-term EMA period
        signal_period: Signal line EMA period

    Returns:
        DataFrame with MACD indicators added
    """
    # MACD calculation logging removed for performance

    # Calculate EMAs
    data = data.with_columns(
        [
            pl.col("Close").ewm_mean(span=fast_period).alias("EMA_short"),
            pl.col("Close").ewm_mean(span=slow_period).alias("EMA_long"),
        ]
    )

    # Count valid EMA points
    valid_short_ema = data.select(pl.col("EMA_short").is_not_null()).sum().item()
    valid_long_ema = data.select(pl.col("EMA_long").is_not_null()).sum().item()
    # EMA validation logging removed for performance

    # Calculate MACD line
    data = data.with_columns([(pl.col("EMA_short") - pl.col("EMA_long")).alias("MACD")])

    # Calculate Signal line
    data = data.with_columns(
        [pl.col("MACD").ewm_mean(span=signal_period).alias("Signal_Line")]
    )

    # Count valid MACD and Signal Line points
    valid_macd = data.select(pl.col("MACD").is_not_null()).sum().item()
    valid_signal = data.select(pl.col("Signal_Line").is_not_null()).sum().item()
    # MACD validation logging removed for performance

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

        fast_period = config.get("fast_period", config.get("fast_period", 12))
        slow_period = config.get("slow_period", config.get("slow_period", 26))
        signal_period = config.get("signal_period", config.get("signal_period", 9))
        direction = config.get("DIRECTION", "Long").lower()

        # Analysis parameters logging removed for performance

        # Calculate MACD indicators
        data = calculate_macd(data, fast_period, slow_period, signal_period)

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
                    .otherwise(
                        None
                    )  # Use None instead of pl.col("Signal") so forward_fill works
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
                    .otherwise(
                        None
                    )  # Use None instead of pl.col("Signal") so forward_fill works
                    .alias("Signal")
                ]
            )

        # Forward fill signals between crossovers
        data = data.with_columns(
            [pl.col("Signal").forward_fill().fill_null(0).alias("Signal")]
        )

        # Log signal conversion statistics
        non_zero_signals = data.filter(pl.col("Signal") != 0).height
        # Signal generation logging removed for performance

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

        # Signal status logging removed for performance

        # Convert signals to positions using the standardized function
        from app.tools.signal_conversion import convert_signals_to_positions

        # Create a simple log function if not provided
        def simple_log(message, level="debug"):
            pass  # Suppress logging for performance

        data = convert_signals_to_positions(data, config, simple_log)

        return data

    except Exception as e:
        # Error logging removed for performance
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

        # Check if specific windows are provided
        specific_short = config.get("fast_period")
        specific_long = config.get("slow_period")
        specific_signal = config.get("signal_period")

        if (
            specific_short is not None
            and specific_long is not None
            and specific_signal is not None
        ):
            # Use specific windows from config
            parameter_combinations = [(specific_short, specific_long, specific_signal)]
        else:
            # Generate parameter combinations with STEP (for full analysis)
            step = config.get("STEP", 1)  # Default to 1 for faster testing

            # Use the specific config parameters with reduced testing defaults
            short_window_start = config.get("SHORT_WINDOW_START", 8)
            short_window_end = config.get("SHORT_WINDOW_END", 12)
            long_window_start = config.get("LONG_WINDOW_START", 21)
            long_window_end = config.get("LONG_WINDOW_END", 26)
            signal_window_start = config.get("SIGNAL_WINDOW_START", 9)
            signal_window_end = config.get("SIGNAL_WINDOW_END", 9)

            parameter_combinations = []
            for fast_period in range(short_window_start, short_window_end + 1, step):
                for slow_period in range(long_window_start, long_window_end + 1, step):
                    if slow_period <= fast_period:
                        continue
                    for signal_period in range(
                        signal_window_start, signal_window_end + 1, step
                    ):
                        parameter_combinations.append(
                            (fast_period, slow_period, signal_period)
                        )

        for fast_period, slow_period, signal_period in parameter_combinations:
            try:
                temp_config = config.copy()
                temp_config.update(
                    {
                        "fast_period": fast_period,
                        "slow_period": slow_period,
                        "signal_period": signal_period,
                    }
                )

                temp_data = generate_macd_signals(data.clone(), temp_config)

                if temp_data is not None and len(temp_data) > 0:
                    last_signal = temp_data.tail(1).select("Signal").item()
                    if last_signal != 0:  # If there's an active signal
                        signals.append(
                            {
                                "Fast Period": fast_period,
                                "Slow Period": slow_period,
                                "Signal Period": signal_period,
                                "Signal": last_signal,
                            }
                        )

            except Exception as e:
                log(
                    f"Failed to process parameters {fast_period}/{slow_period}/{signal_period}: {str(e)}",
                    "warning",
                )
                continue

        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(signals)
        return pl.DataFrame(
            schema={
                "Fast Period": pl.Int32,
                "Slow Period": pl.Int32,
                "Signal Period": pl.Int32,
                "Signal": pl.Int32,
            }
        )

    except Exception as e:
        log(f"Failed to get current signals: {str(e)}", "error")
        return pl.DataFrame(
            schema={
                "Fast Period": pl.Int32,
                "Slow Period": pl.Int32,
                "Signal Period": pl.Int32,
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
        # Config is already processed by PortfolioOrchestrator
        data_result = get_data(config["TICKER"], config, log)
        if isinstance(data_result, tuple):
            data, _ = data_result
        else:
            data = data_result
        if data is None:
            log("Failed to get price data", "error")
            return pl.DataFrame(
                schema={
                    "Fast Period": pl.Int32,
                    "Slow Period": pl.Int32,
                    "Signal Period": pl.Int32,
                    "Signal": pl.Int32,
                }
            )

        current_signals = get_current_signals(data, config, log)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "macd_cross", config, "current_signals")

            if len(current_signals) == 0:
                # No signals logging removed for performance
                pass

        return current_signals

    except Exception as e:
        log(f"Failed to generate current signals: {str(e)}", "error")
        return pl.DataFrame(
            schema={
                "Fast Period": pl.Int32,
                "Slow Period": pl.Int32,
                "Signal Period": pl.Int32,
                "Signal": pl.Int32,
            }
        )
