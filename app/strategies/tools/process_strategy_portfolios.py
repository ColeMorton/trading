"""
Generic Strategy Processing Module

This module provides a unified approach to processing different strategy types
(SMA, EMA, MACD) within the strategies framework. It handles strategy-specific
parameter validation and processing logic. It supports both regular tickers and
synthetic tickers (identified by an underscore).
"""

from typing import Any, Callable, Dict, Optional, Tuple

import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_data import get_data


def process_strategy_portfolios(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int] = None,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[Tuple[Optional[pl.DataFrame], dict, Optional[pl.DataFrame]]]:
    """
    Process portfolios for a given ticker based on strategy type.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        strategy_type: Strategy type (SMA, EMA, MACD)
        short_window: Short/fast window period
        long_window: Long/slow window period
        signal_window: Signal window period (required for MACD)
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

        # Validate MACD signal window
        if strategy_type == "MACD" and signal_window is None:
            log(
                f"MACD strategy requires signal_window parameter for {current_ticker}",
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
                f"Processing SMA strategy for {current_ticker} with windows {short_window}/{long_window}"
            )
            strategy_config["USE_SMA"] = True
            signal_data = calculate_ma_and_signals(
                data.clone(), short_window, long_window, strategy_config, log
            )

        elif strategy_type == "EMA":
            log(
                f"Processing EMA strategy for {current_ticker} with windows {short_window}/{long_window}"
            )
            strategy_config["USE_SMA"] = False
            signal_data = calculate_ma_and_signals(
                data.clone(), short_window, long_window, strategy_config, log
            )

        elif strategy_type == "MACD":
            log(
                f"Processing MACD strategy for {current_ticker} with parameters {short_window}/{long_window}/{signal_window}"
            )
            signal_data = calculate_macd_and_signals(
                data.clone(),
                short_window,
                long_window,
                signal_window,
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
        else:
            log(
                f"No valid {strategy_type} strategy processed for {current_ticker}",
                "error",
            )
            return None

    except Exception as e:
        error_msg = (
            f"Failed to process {strategy_type} strategy for {current_ticker}: {str(e)}"
        )
        log(error_msg, "error")
        raise Exception(error_msg) from e


def process_sma_strategy(
    ticker: str,
    short_window: int,
    long_window: int,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[Tuple[Optional[pl.DataFrame], dict, Optional[pl.DataFrame]]]:
    """
    Process SMA strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        short_window: Short window period
        long_window: Long window period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="SMA",
        short_window=short_window,
        long_window=long_window,
        config=config,
        log=log,
    )


def process_ema_strategy(
    ticker: str,
    short_window: int,
    long_window: int,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[Tuple[Optional[pl.DataFrame], dict, Optional[pl.DataFrame]]]:
    """
    Process EMA strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        short_window: Short window period
        long_window: Long window period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="EMA",
        short_window=short_window,
        long_window=long_window,
        config=config,
        log=log,
    )


def process_macd_strategy(
    ticker: str,
    short_window: int,
    long_window: int,
    signal_window: int,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[Tuple[Optional[pl.DataFrame], dict, Optional[pl.DataFrame]]]:
    """
    Process MACD strategy for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        short_window: Fast EMA period
        long_window: Slow EMA period
        signal_window: Signal line EMA period
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function

    Returns:
        Optional tuple of (portfolio DataFrame or None, config, data with signals or None)
    """
    return process_strategy_portfolios(
        ticker=ticker,
        strategy_type="MACD",
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        config=config,
        log=log,
    )
