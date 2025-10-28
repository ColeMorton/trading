"""
Generic Strategy Processing Module

This module provides a unified approach to processing different strategy types
(SMA, EMA, MACD) within the strategies framework. It handles strategy-specific
parameter validation and processing logic. It supports both regular tickers and
synthetic tickers (identified by an underscore).
"""

from collections.abc import Callable
from typing import Any

import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_data import get_data


def process_strategy_portfolios(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: int | None | None = None,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> tuple[pl.DataFrame | None, dict, pl.DataFrame | None] | None:
    """
    Process portfolios for a given ticker based on strategy type.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        strategy_type: Strategy type (SMA, EMA, MACD)
        fast_period: Short/fast window period
        slow_period: Long/slow window period
        signal_period: Signal period (required for MACD)
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
        Returns None if processing fails entirely
    """
    current_ticker = ticker  # Store ticker for error handling

    try:
        # Validate strategy type
        if strategy_type not in ["SMA", "EMA", "MACD"]:
            log(
                f"Unsupported strategy type: {strategy_type} for {current_ticker}",
                "error",
            )
            return None

        # Validate MACD signal period
        if strategy_type == "MACD" and signal_period is None:
            log(
                f"MACD strategy requires signal_period parameter for {current_ticker}",
                "error",
            )
            return None

        # Update config with ticker and strategy settings while preserving other
        # settings
        strategy_config = config.copy() if config else {}
        strategy_config["TICKER"] = current_ticker
        strategy_config["SHORT"] = False  # Long-only strategy by default

        # Set direction from config if available
        if config and "DIRECTION" in config:
            strategy_config["SHORT"] = config["DIRECTION"] == "Short"

        # Get data
        data_result = get_data(current_ticker, strategy_config, log)

        # Handle potential tuple return from get_data for synthetic pairs
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result  # Unpack tuple
            log(f"Received synthetic ticker data for {synthetic_ticker}")
            strategy_config[
                "TICKER"
            ] = synthetic_ticker  # Update config with synthetic ticker
        else:
            data = data_result

        if data is None or len(data) == 0:
            log(f"No data available for {current_ticker}", "error")
            return None

        portfolio = None
        signal_data = None

        # Process based on strategy type
        if strategy_type == "SMA":
            log(
                f"Processing SMA strategy for {current_ticker} with windows {fast_period}/{slow_period}"
            )
            strategy_config["USE_SMA"] = True
            signal_data = calculate_ma_and_signals(
                data.clone(), fast_period, slow_period, strategy_config, log
            )

        elif strategy_type == "EMA":
            log(
                f"Processing EMA strategy for {current_ticker} with windows {fast_period}/{slow_period}"
            )
            strategy_config["USE_SMA"] = False
            signal_data = calculate_ma_and_signals(
                data.clone(), fast_period, slow_period, strategy_config, log
            )

        elif strategy_type == "MACD":
            log(
                f"Processing MACD strategy for {current_ticker} with parameters {fast_period}/{slow_period}/{signal_period}"
            )
            signal_data = calculate_macd_and_signals(
                data.clone(),
                fast_period,
                slow_period,
                signal_period,
                strategy_config,
                log,
            )

        # Backtest the strategy if signals were generated
        if signal_data is not None:
            portfolio = backtest_strategy(signal_data, strategy_config, log)
            if portfolio is None:
                log(
                    f"Failed to backtest {strategy_type} strategy for {current_ticker}",
                    "error",
                )
        else:
            log(
                f"Failed to calculate {strategy_type} signals for {current_ticker}",
                "error",
            )

        # Return results if strategy was processed
        if portfolio is not None:
            return portfolio, strategy_config, signal_data
        log(
            f"No valid {strategy_type} strategy processed for {current_ticker}",
            "error",
        )
        return None

    except Exception as e:
        error_msg = (
            f"Failed to process {strategy_type} strategy for {current_ticker}: {e!s}"
        )
        log(error_msg, "error")
        raise Exception(error_msg) from e


def process_sma_strategy(
    ticker: str,
    fast_period: int,
    slow_period: int,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> tuple[pl.DataFrame | None, dict, pl.DataFrame | None] | None:
    """
    Process SMA strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        fast_period: Fast period
        slow_period: Slow period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="SMA",
        fast_period=fast_period,
        slow_period=slow_period,
        config=config,
        log=log,
    )


def process_ema_strategy(
    ticker: str,
    fast_period: int,
    slow_period: int,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> tuple[pl.DataFrame | None, dict, pl.DataFrame | None] | None:
    """
    Process EMA strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        fast_period: Fast period
        slow_period: Slow period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="EMA",
        fast_period=fast_period,
        slow_period=slow_period,
        config=config,
        log=log,
    )


def process_macd_strategy(
    ticker: str,
    fast_period: int,
    slow_period: int,
    signal_period: int,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> tuple[pl.DataFrame | None, dict, pl.DataFrame | None] | None:
    """
    Process MACD strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line EMA period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="MACD",
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        config=config,
        log=log,
    )
