"""
SMA_ATR Signal Generation Module

This module handles the generation of current signals for SMA_ATR strategies,
which combine SMA crossovers for entry signals with ATR trailing stops.
"""

from collections.abc import Callable
from typing import Any

import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data


def generate_current_signals(config: dict[str, Any], log: Callable) -> pl.DataFrame:
    """
    Generate current SMA_ATR signals for configured tickers.

    This function finds all parameter combinations that have current entry signals
    based on SMA crossovers.

    Args:
        config: Configuration dictionary containing:
            - TICKER: Ticker symbol or list of symbols
            - FAST_PERIOD_RANGE: Range for fast SMA periods
            - SLOW_PERIOD_RANGE: Range for slow SMA periods
            - ATR_LENGTH_RANGE: Range for ATR lengths
            - ATR_MULTIPLIER_RANGE: Range for ATR multipliers
            - Other standard config parameters
        log: Logging function

    Returns:
        DataFrame containing current signals with parameter combinations
    """
    try:
        # Get ticker
        ticker = config.get("TICKER", "")
        if isinstance(ticker, list):
            ticker = ticker[0] if ticker else ""

        if not ticker:
            log("No ticker specified for SMA_ATR signal generation", "error")
            return pl.DataFrame()

        # Get price data
        data = get_data(ticker, config, log)
        if data is None:
            log(f"Failed to get price data for {ticker}", "error")
            return pl.DataFrame()

        # Get parameter ranges
        fast_range = config.get("FAST_PERIOD_RANGE", [10, 50])
        slow_range = config.get("SLOW_PERIOD_RANGE", [20, 100])
        atr_length_range = config.get("ATR_LENGTH_RANGE", [10, 20])
        atr_multiplier_range = config.get("ATR_MULTIPLIER_RANGE", [2.0, 3.0])
        atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP", 0.5)

        current_signals = []
        direction = config.get("DIRECTION", "Long")

        log(f"Scanning for current SMA_ATR signals ({direction}) for {ticker}", "info")

        # Check all parameter combinations for current signals
        for fast in range(fast_range[0], fast_range[1] + 1):
            for slow in range(slow_range[0], slow_range[1] + 1):
                if fast >= slow:  # Skip invalid combinations
                    continue

                try:
                    # Calculate SMA signals for this combination
                    param_config = config.copy()
                    param_config.update(
                        {
                            "FAST_PERIOD": fast,
                            "SLOW_PERIOD": slow,
                        }
                    )

                    # Generate SMA signals
                    data_with_signals = calculate_ma_and_signals(
                        data, fast, slow, param_config, log, strategy_type="SMA"
                    )

                    if data_with_signals is None:
                        continue

                    # Check for current entry signal
                    latest_row = data_with_signals.tail(1).to_dicts()[0]
                    signal = latest_row.get("Signal", 0)

                    # Check if we have a current entry signal
                    has_current_signal = False
                    if (direction == "Long" and signal == 1) or (
                        direction == "Short" and signal == -1
                    ):
                        has_current_signal = True

                    if has_current_signal:
                        # For each valid SMA combination with current signal,
                        # create entries for all ATR parameter combinations
                        for atr_length in range(
                            atr_length_range[0], atr_length_range[1] + 1
                        ):
                            multiplier = atr_multiplier_range[0]
                            while multiplier <= atr_multiplier_range[1]:
                                current_signals.append(
                                    {
                                        "TICKER": ticker,
                                        "Strategy Type": "SMA_ATR",
                                        "Fast Period": fast,
                                        "Slow Period": slow,
                                        "ATR Length": atr_length,
                                        "ATR Multiplier": multiplier,
                                        "Signal": signal,
                                        "Direction": direction,
                                    }
                                )
                                multiplier += atr_multiplier_step

                except Exception as e:
                    log(
                        f"Error processing SMA combination {fast}/{slow}: {e}",
                        "warning",
                    )
                    continue

        if current_signals:
            signals_df = pl.DataFrame(current_signals)
            log(
                f"Found {len(current_signals)} current SMA_ATR signal combinations for {ticker}",
                "info",
            )
            return signals_df
        log(f"No current SMA_ATR signals found for {ticker}", "info")
        return pl.DataFrame()

    except Exception as e:
        log(f"Error generating SMA_ATR current signals: {e}", "error")
        return pl.DataFrame()
