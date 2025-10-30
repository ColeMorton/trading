"""
Strategy Processing Module.

This module handles the preparation and processing of strategy data for concurrency analysis.
It processes both MACD and MA cross strategies, calculating signals and positions.
"""

from collections.abc import Callable

import pandas as pd
import polars as pl

from app.concurrency.tools.atr_strategy import process_atr_strategy
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.tools.get_data import get_data
from app.tools.portfolio import StrategyConfig
from app.tools.stats_converter import convert_stats
from app.tools.strategy_utils import determine_strategy_type, validate_strategy_config


def process_strategies(
    strategies: list[StrategyConfig],
    log: Callable[[str, str], None],
    main_config: dict | None = None,
) -> tuple[list[pl.DataFrame], list[StrategyConfig]]:
    """Process multiple trading strategies and prepare their data for concurrency analysis.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to process
        log: Callable for logging messages
        main_config: Main configuration dictionary (optional, for global settings like EXPORT_TRADE_HISTORY)

    Returns:
        Tuple[List[pl.DataFrame], List[StrategyConfig]]: Processed data and updated configs

    Raises:
        ValueError: If fewer than two strategies are provided or invalid configuration
        Exception: If processing fails for any strategy
    """
    try:
        # Validate input
        if not strategies:
            log("No strategies provided", "error")
            msg = "Strategies list cannot be empty"
            raise ValueError(msg)

        if len(strategies) < 2:
            log("Insufficient number of strategies", "error")
            msg = "At least two strategies are required for concurrency analysis"
            raise ValueError(
                msg,
            )

        log(f"Processing {len(strategies)} strategies", "info")

        # Validate strategy configurations
        for i, strategy_config in enumerate(strategies, 1):
            log(f"Validating strategy {i} configuration", "info")
            # Normalize field names first (handle both uppercase and lowercase)
            field_mapping = {
                "TICKER": ["ticker", "TICKER"],
                "LENGTH": ["length", "LENGTH"],
                "MULTIPLIER": ["multiplier", "MULTIPLIER"],
                "FAST_PERIOD": ["fast_period", "FAST_PERIOD"],
                "SLOW_PERIOD": ["slow_period", "SLOW_PERIOD"],
                "SIGNAL_PERIOD": ["signal_period", "SIGNAL_PERIOD"],
                "DIRECTION": ["direction", "DIRECTION"],
                "STRATEGY_TYPE": ["type", "STRATEGY_TYPE"],
            }

            # Copy values from lowercase to uppercase keys
            for upper_key, possible_keys in field_mapping.items():
                for key in possible_keys:
                    if key in strategy_config and upper_key not in strategy_config:
                        strategy_config[upper_key] = strategy_config[key]

            # Use the standardized validate_strategy_config function
            validate_strategy_config(strategy_config, i, log)

        strategy_data = []
        for i, strategy_config in enumerate(strategies, 1):
            try:
                log(
                    f"Fetching data for strategy {i}: {strategy_config['TICKER']}",
                    "info",
                )

                # Check if this is a synthetic ticker
                is_synthetic = (
                    strategy_config.get("USE_SYNTHETIC", False)
                    or "_" in strategy_config["TICKER"]
                )

                if is_synthetic:
                    log(
                        f"Detected synthetic ticker: {strategy_config['TICKER']}",
                        "info",
                    )

                    # get_data returns a tuple (data, synthetic_ticker) for synthetic
                    # tickers
                    data_result = get_data(
                        strategy_config["TICKER"],
                        strategy_config,
                        log,
                    )

                    # Check if the result is a tuple (indicating synthetic ticker
                    # processing)
                    if isinstance(data_result, tuple) and len(data_result) == 2:
                        data, synthetic_ticker = data_result
                        log(
                            f"Successfully processed synthetic ticker: {synthetic_ticker}",
                            "info",
                        )
                    else:
                        # If not a tuple, just use the result directly
                        data = data_result
                else:
                    # For regular tickers, just get the data
                    data = get_data(strategy_config["TICKER"], strategy_config, log)

                # Determine if this is a short strategy
                is_short = strategy_config.get("DIRECTION", "Long") == "Short"
                direction = "Short" if is_short else "Long"

                # Process allocation and stop loss values if available
                if (
                    "ALLOCATION" in strategy_config
                    and strategy_config["ALLOCATION"] is not None
                ):
                    allocation = float(strategy_config["ALLOCATION"])
                    log(
                        f"Using allocation {allocation:.2f}% for {strategy_config['TICKER']}",
                        "info",
                    )

                if (
                    "STOP_LOSS" in strategy_config
                    and strategy_config["STOP_LOSS"] is not None
                ):
                    stop_loss = float(strategy_config["STOP_LOSS"])
                    log(
                        f"Using stop loss {stop_loss:.4f} ({stop_loss * 100:.2f}%) for {strategy_config['TICKER']}",
                        "info",
                    )

                # Process based on strategy type using the standardized
                # determine_strategy_type function
                strategy_type = determine_strategy_type(strategy_config)
                is_macd = strategy_type == "MACD"

                # Check if it's an ATR strategy using the standardized
                # determine_strategy_type function
                is_atr = strategy_type == "ATR"

                if is_atr:
                    log(
                        f"Processing {direction} ATR Trailing Stop strategy {i}/{len(strategies)}",
                        "info",
                    )

                    # Process ATR strategy using the dedicated module
                    data = process_atr_strategy(data, strategy_config, log)
                    log(
                        f"ATR signals calculated for {strategy_config['TICKER']}",
                        "info",
                    )

                elif is_macd:
                    log(
                        f"Processing {direction} MACD strategy {i}/{len(strategies)}",
                        "info",
                    )
                    log(
                        f"MACD periods: {strategy_config['FAST_PERIOD']}/"
                        f"{strategy_config['SLOW_PERIOD']}/"
                        f"{strategy_config['SIGNAL_PERIOD']}",
                        "info",
                    )

                    data = calculate_macd(
                        data,
                        fast_period=strategy_config["FAST_PERIOD"],
                        slow_period=strategy_config["SLOW_PERIOD"],
                        signal_period=strategy_config["SIGNAL_PERIOD"],
                    )
                    data = calculate_macd_signals(data, is_short)
                    data = data.with_columns(
                        [pl.col("Signal").shift(1).fill_null(0).alias("Position")],
                    )
                    log(
                        f"MACD signals calculated for {strategy_config['TICKER']}",
                        "info",
                    )

                else:
                    log(
                        f"Processing {direction} MA cross strategy {i}/{len(strategies)}",
                        "info",
                    )
                    log(
                        f"MA windows: {strategy_config['FAST_PERIOD']}/"
                        f"{strategy_config['SLOW_PERIOD']}",
                        "info",
                    )

                    # Calculate MA signals and positions
                    data = calculate_ma_and_signals(
                        data,
                        strategy_config["FAST_PERIOD"],
                        strategy_config["SLOW_PERIOD"],
                        strategy_config,
                        log,
                    )

                    log(
                        f"MA signals calculated and positions set for {strategy_config['TICKER']}",
                        "info",
                    )

                    # Log position statistics for verification
                    positions = data["Position"].to_numpy()
                    position_changes = (positions[1:] != positions[:-1]).sum()
                    log(
                        f"Strategy {i} position changes detected: {position_changes}",
                        "info",
                    )

                # Store ATR-specific columns before backtesting (they might be lost
                # during backtesting)
                atr_columns = {}
                if (
                    strategy_config.get("STRATEGY_TYPE") == "ATR"
                    or strategy_config.get("type") == "ATR"
                ):
                    log(
                        f"Preserving ATR columns for {strategy_config['TICKER']}",
                        "info",
                    )
                    # Check if ATR_Trailing_Stop column exists
                    if "ATR_Trailing_Stop" in data.columns:
                        atr_columns["ATR_Trailing_Stop"] = data.select(
                            ["Date", "ATR_Trailing_Stop"],
                        ).to_pandas()
                        log(
                            f"Preserved ATR_Trailing_Stop column with {atr_columns['ATR_Trailing_Stop']['ATR_Trailing_Stop'].notna().sum()} non-null values",
                            "info",
                        )
                    else:
                        log(
                            f"WARNING: ATR_Trailing_Stop column not found for {strategy_config['TICKER']} ATR strategy",
                            "warning",
                        )

                # Propagate trade history export flag from main config if present
                if main_config and main_config.get("EXPORT_TRADE_HISTORY", False):
                    strategy_config["EXPORT_TRADE_HISTORY"] = True
                    log(
                        f"Trade history export enabled for strategy {i}: {strategy_config['TICKER']}",
                        "info",
                    )

                # Calculate expectancy
                log(f"Running backtest for {strategy_config['TICKER']}", "info")
                portfolio = backtest_strategy(data, strategy_config, log)
                stats = convert_stats(portfolio.stats(), log, strategy_config, None)

                # Restore ATR-specific columns after backtesting
                if atr_columns and "ATR_Trailing_Stop" in atr_columns:
                    try:
                        log(
                            f"Restoring ATR columns for {strategy_config['TICKER']}",
                            "info",
                        )
                        # Get the data from the portfolio
                        data_pd = portfolio._data_pd

                        # Log data shapes and column info for debugging
                        log(
                            f"Portfolio data shape: {data_pd.shape}, columns: {list(data_pd.columns)}",
                            "info",
                        )
                        log(
                            f"ATR data shape: {atr_columns['ATR_Trailing_Stop'].shape}, columns: {list(atr_columns['ATR_Trailing_Stop'].columns)}",
                            "info",
                        )

                        # Check if Date columns are compatible
                        log(
                            f"Portfolio Date column type: {data_pd['Date'].dtype}",
                            "info",
                        )
                        log(
                            f"ATR Date column type: {atr_columns['ATR_Trailing_Stop']['Date'].dtype}",
                            "info",
                        )

                        # Ensure Date columns are the same type
                        if (
                            data_pd["Date"].dtype
                            != atr_columns["ATR_Trailing_Stop"]["Date"].dtype
                        ):
                            log("Converting Date columns to compatible types", "info")
                            # Convert both to datetime for safe merging
                            data_pd["Date"] = pd.to_datetime(data_pd["Date"])
                            atr_columns["ATR_Trailing_Stop"]["Date"] = pd.to_datetime(
                                atr_columns["ATR_Trailing_Stop"]["Date"],
                            )

                        # Merge the ATR columns back into the data
                        data_pd = data_pd.merge(
                            atr_columns["ATR_Trailing_Stop"],
                            on="Date",
                            how="left",
                        )
                        log(
                            f"Restored ATR_Trailing_Stop column with {data_pd['ATR_Trailing_Stop'].notna().sum()} non-null values",
                            "info",
                        )

                        # Update the portfolio's data
                        portfolio._data_pd = data_pd

                        # Convert back to polars and update the strategy data
                        data = pl.from_pandas(data_pd)
                        log(
                            "Successfully restored ATR data to polars DataFrame",
                            "info",
                        )
                    except Exception as e:
                        log(f"Error restoring ATR columns: {e!s}", "error")
                        # Continue without the ATR columns rather than failing
                        log("Continuing without ATR visualization data", "warning")

                # Add expectancy to strategy config
                strategy_config["EXPECTANCY_PER_MONTH"] = stats["Expectancy per Month"]
                strategy_config["EXPECTANCY"] = stats["Expectancy"]
                strategy_config["EXPECTANCY_PER_TRADE"] = stats["Expectancy per Trade"]

                log(
                    f"Expectancy per month for {strategy_config['TICKER']}: "
                    f"{stats['Expectancy per Month']:.4f}",
                    "info",
                )

                # Add all portfolio stats to strategy config
                strategy_config["PORTFOLIO_STATS"] = stats
                log(
                    f"Added portfolio stats to strategy config for {strategy_config['TICKER']}",
                    "info",
                )

                strategy_data.append(data)
                log(
                    f"Successfully processed strategy {i}: {strategy_config['TICKER']}",
                    "info",
                )

            except Exception as e:
                log(
                    f"Error processing strategy {i} ({strategy_config['TICKER']}): {e!s}",
                    "error",
                )
                raise

        log(f"Successfully processed all {len(strategies)} strategies", "info")
        return strategy_data, strategies

    except Exception as e:
        log(f"Error in strategy processing: {e!s}", "error")
        raise
