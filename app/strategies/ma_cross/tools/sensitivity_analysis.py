import os
from typing import Any, Callable, Dict, List, Optional

import polars as pl

from app.concurrency.tools.signal_processor import SignalDefinition, SignalProcessor
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.portfolio_transformation import reorder_columns
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import is_exit_signal_current, is_signal_current

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv("USE_FIXED_SIGNAL_PROC", "true").lower() == "true"


def analyze_window_combination(
    data: pl.DataFrame, short: int, long: int, config: Dict[str, Any], log: Callable
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single window combination.

    Args:
        data: Price data DataFrame
        short: Short window period
        long: Long window period
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        Optional[Dict]: Portfolio statistics if successful, None if failed
    """
    try:
        data_length = len(data)
        max_window = max(short, long)

        log(f"Analyzing windows - Short: {short}, Long: {long}")
        log(f"Data length: {data_length}, Required length: {max_window}")

        if data_length < max_window:
            log(
                f"Insufficient data for windows {short}, {long} - Need at least {max_window} periods, have {data_length}",
                "warning",
            )
            return None

        # Get strategy type from config or default to SMA
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

        # Calculate MAs and signals
        temp_data = calculate_ma_and_signals(
            data.clone(), short, long, config, log, strategy_type
        )
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for windows {short}, {long}", "warning")
            return None

        # Log signal statistics using standardized processor
        if USE_FIXED_SIGNAL_PROC:
            signal_processor = SignalProcessor(use_fixed=True)
            signal_def = SignalDefinition(
                signal_column="Signal", position_column="Position"
            )
            signal_counts = signal_processor.get_comprehensive_counts(
                temp_data, signal_def
            )
            non_zero_signals = signal_counts.raw_signals
            positions = signal_counts.position_signals
        else:
            # Legacy counting method
            non_zero_signals = (temp_data["Signal"] != 0).sum()
            positions = (temp_data["Position"] != 0).sum()
        log(
            f"Windows {short}, {long}: {positions} positions from {non_zero_signals} signals",
            "info",
        )

        # Check for current entry signal
        current = is_signal_current(temp_data, config)

        # Check for current exit signal
        exit_signal = is_exit_signal_current(temp_data, config)
        log(
            f"Windows {short}, {long}: Entry signal: {current}, Exit signal: {exit_signal}",
            "info",
        )

        portfolio = backtest_strategy(temp_data, config, log)

        stats = portfolio.stats()
        stats["Short Window"] = short
        stats["Long Window"] = long
        stats["Ticker"] = config["TICKER"]  # Add ticker from config
        # Add Strategy Type field
        stats["Strategy Type"] = config.get("STRATEGY_TYPE", "SMA")

        # Add Allocation [%] and Stop Loss [%] fields if they exist in config
        if "ALLOCATION" in config:
            stats["Allocation [%]"] = config["ALLOCATION"]
        if "STOP_LOSS" in config:
            stats["Stop Loss [%]"] = config["STOP_LOSS"]

        # Add signal metrics using standardized processor (reuse counts from above)
        stats["Signal Count"] = non_zero_signals
        stats["Position Count"] = positions

        # Pass both entry and exit signals to convert_stats
        stats = convert_stats(stats, log, config, current, exit_signal)
        stats = reorder_columns(stats)

        return stats

    except Exception as e:
        log(f"Failed to process windows {short}, {long}: {str(e)}", "warning")
        return None


def analyze_parameter_combinations(
    data: pl.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
    config: Dict[str, Any],
    log: Callable,
) -> List[Dict[str, Any]]:
    """
    Analyze all valid parameter combinations.

    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        List[Dict]: List of portfolio statistics for each valid combination
    """
    portfolios = []
    total_combinations = 0
    successful_combinations = 0

    log("Starting analysis of window combinations")
    log(f"Data shape: {data.shape}")
    log(f"Date range: {data['Date'].min()} to {data['Date'].max()}")

    for short in short_windows:
        for long in long_windows:
            if short < long:
                total_combinations += 1
                result = analyze_window_combination(data, short, long, config, log)
                if result is not None:
                    successful_combinations += 1
                    portfolios.append(result)

    success_rate = (
        (successful_combinations / total_combinations * 100)
        if total_combinations > 0
        else 0
    )
    log(
        f"Analysis complete - Successful combinations: {successful_combinations}/{total_combinations} ({success_rate:.2f}%)"
    )

    return portfolios
