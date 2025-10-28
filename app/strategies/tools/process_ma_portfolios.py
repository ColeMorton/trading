"""
Process MA Portfolios Module

This module provides functionality for processing SMA and EMA portfolios
for a given ticker, including data retrieval, signal calculation, and backtesting.
It supports both regular tickers and synthetic tickers (identified by an underscore).
"""

from collections.abc import Callable

import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data


def process_ma_portfolios(
    ticker: str,
    sma_fast: int | None,
    sma_slow: int | None,
    ema_fast: int | None,
    ema_slow: int | None,
    config: dict,
    log: Callable,
) -> (
    tuple[
        pl.DataFrame | None,
        pl.DataFrame | None,
        dict,
        pl.DataFrame | None,
        pl.DataFrame | None,
    ]
    | None
):
    """
    Process SMA and/or EMA portfolios for a given ticker.

    Args:
        ticker: Ticker symbol (can be a regular ticker or a synthetic ticker with underscore)
        sma_fast: Fast SMA window (optional)
        sma_slow: Slow SMA window (optional)
        ema_fast: Fast EMA window (optional)
        ema_slow: Slow EMA window (optional)
        config: Configuration dictionary including USE_HOURLY and USE_SYNTHETIC settings
        log: Logging function for recording events and errors

    Returns:
        Optional tuple of (SMA portfolio DataFrame or None, EMA portfolio DataFrame or None, config,
                          SMA data with signals or None, EMA data with signals or None)
        Returns None if processing fails entirely
    """
    current_ticker = ticker  # Store ticker for error handling

    try:
        # Update config with ticker and strategy settings while preserving USE_HOURLY
        strategy_config = config.copy()
        strategy_config["TICKER"] = current_ticker
        strategy_config["SHORT"] = False  # Long-only strategy

        # Get data - now passing the log parameter
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

        sma_portfolio = None
        ema_portfolio = None
        sma_data = None
        ema_data = None

        # Process SMA if both windows provided
        if sma_fast is not None and sma_slow is not None:
            strategy_config["USE_SMA"] = True
            sma_data = calculate_ma_and_signals(
                data.clone(),
                sma_fast,
                sma_slow,
                strategy_config,
                log,  # Pass the log parameter here
                "SMA",  # Explicitly pass "SMA" as the strategy_type
            )
            if sma_data is not None:
                sma_portfolio = backtest_strategy(sma_data, strategy_config, log)
                if sma_portfolio is None:
                    log(
                        f"Failed to backtest SMA strategy for {current_ticker}", "error"
                    )
            else:
                log(f"Failed to calculate SMA signals for {current_ticker}", "error")

        # Process EMA if both windows provided
        if ema_fast is not None and ema_slow is not None:
            strategy_config["USE_SMA"] = False
            ema_data = calculate_ma_and_signals(
                data.clone(),
                ema_fast,
                ema_slow,
                strategy_config,
                log,  # Pass the log parameter here
                "EMA",  # Explicitly pass "EMA" as the strategy_type
            )
            if ema_data is not None:
                ema_portfolio = backtest_strategy(ema_data, strategy_config, log)
                if ema_portfolio is None:
                    log(
                        f"Failed to backtest EMA strategy for {current_ticker}", "error"
                    )
            else:
                log(f"Failed to calculate EMA signals for {current_ticker}", "error")

        # Return results if at least one strategy was processed
        if sma_portfolio is not None or ema_portfolio is not None:
            return sma_portfolio, ema_portfolio, strategy_config, sma_data, ema_data
        log(f"No valid strategies processed for {current_ticker}", "error")
        return None

    except Exception as e:
        error_msg = f"Failed to process {current_ticker}: {e!s}"
        log(error_msg, "error")
        raise Exception(error_msg) from e
