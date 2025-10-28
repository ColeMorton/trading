"""
Strategy Execution Module

This module handles the execution of the Range High Break trading strategy,
including portfolio processing, filtering, and best portfolio selection.
"""

from collections.abc import Callable
from typing import Any

import numpy as np
import polars as pl

from app.range.config_types import PortfolioConfig
from app.range.tools.export_portfolios import export_portfolios
from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.stats_converter import convert_stats


def process_single_ticker(
    ticker: str,
    config: PortfolioConfig,
    log: Callable,
) -> list[dict[str, Any]] | None:
    """Process a single ticker through the portfolio analysis pipeline.

    Args:
        ticker (str): The ticker symbol to process
        config (PortfolioConfig): Configuration for the analysis
        log (Callable): Logging function

    Returns:
        Optional[List[Dict[str, Any]]]: List of portfolio results if successful, None otherwise
    """
    # Create a config copy with single ticker
    ticker_config = config.copy()
    ticker_config["TICKER"] = ticker

    try:
        # Get price data
        data = get_data(ticker, ticker_config, log)
        if data is None:
            log(f"Failed to get data for {ticker}", "error")
            return None

        # Create parameter ranges
        range_lengths = np.arange(2, 35)  # 2 to 34
        candle_lookbacks = np.arange(1, 22)  # 1 to 21

        portfolios = []

        # Test all combinations
        for range_length in range_lengths:
            for candle_lookback in candle_lookbacks:
                log(
                    f"Testing range_length={range_length}, candle_lookback={candle_lookback}",
                )

                # Calculate signals for this combination
                signals_data = calculate_range_signals(
                    data.clone(),
                    range_length,
                    candle_lookback,
                    ticker_config,
                    log,
                )
                if signals_data is None:
                    continue

                # Run backtest
                portfolio = backtest_strategy(signals_data, ticker_config, log)
                if portfolio is None:
                    continue

                # Get portfolio stats and convert them to proper format
                stats = portfolio.stats()
                stats["Ticker"] = ticker
                stats["Range Length"] = range_length
                stats["Candle Lookback"] = candle_lookback

                # Convert stats to proper format for CSV export
                converted_stats = convert_stats(stats, log, ticker_config, None)
                portfolios.append(converted_stats)

        if not portfolios:
            log(f"No valid portfolios generated for {ticker}", "warning")
            return None

        # Export all portfolios using portfolio export functionality
        _, success = export_portfolios(
            portfolios=portfolios,
            config=ticker_config,
            export_type="portfolios",
            log=log,
        )

        if not success:
            log(f"Failed to export results for {ticker}", "error")
            return None

        return portfolios

    except Exception as e:
        log(f"Failed to process {ticker}: {e!s}", "error")
        return None


def calculate_range_signals(
    data: pl.DataFrame,
    range_length: int,
    candle_lookback: int,
    config: dict[str, Any],
    log: Callable,
) -> pl.DataFrame | None:
    """Calculate Range High Break signals.

    Args:
        data (pl.DataFrame): Price data
        range_length (int): Period length for calculating range high
        candle_lookback (int): Lookback period for exit condition
        config (Dict[str, Any]): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Optional[pl.DataFrame]: DataFrame with signals or None if calculation fails
    """
    try:
        # Calculate range high
        data = data.with_columns(
            [pl.col("High").rolling_max(range_length).alias("Range_High")],
        )

        # Generate entry signals
        # Entry: Price close is greater than Range X High 1 candle ago
        data = data.with_columns(
            [
                (pl.col("Close") > pl.col("Range_High").shift(1))
                .cast(pl.Int32)
                .alias("Signal"),
            ],
        )

        # Generate exit signals
        # Exit: Price close is NOT greater than Range X High Y candles ago
        data = data.with_columns(
            [
                (~(pl.col("Close") > pl.col("Range_High").shift(candle_lookback)))
                .cast(pl.Int32)
                .alias("Exit"),
            ],
        )

        # Combine signals
        return data.with_columns(
            [
                pl.when(pl.col("Exit") == 1)
                .then(0)
                .otherwise(pl.col("Signal"))
                .alias("Signal"),
            ],
        )

    except Exception as e:
        log(f"Failed to calculate range signals: {e!s}", "error")
        return None


def execute_strategy(
    config: PortfolioConfig,
    strategy_type: str,
    log: Callable,
) -> list[dict[str, Any]]:
    """Execute the Range High Break strategy for all tickers.

    Args:
        config (PortfolioConfig): Configuration for the analysis
        strategy_type (str): Must be "RANGE" for Range High Break strategy
        log (Callable): Logging function

    Returns:
        List[Dict[str, Any]]: List of best portfolios found
    """
    if strategy_type != "RANGE":
        log(f"Invalid strategy type: {strategy_type}. Must be 'RANGE'", "error")
        return []

    best_portfolios = []
    tickers = (
        [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
    )

    for ticker in tickers:
        log(f"Processing Range High Break strategy for ticker: {ticker}")
        ticker_config = config.copy()
        ticker_config["TICKER"] = ticker
        portfolios = process_single_ticker(ticker, ticker_config, log)
        if portfolios:
            # Find best portfolio based on Score
            sorted_portfolios = sorted(
                portfolios,
                key=lambda x: float(x.get("Score", 0)),
                reverse=True,
            )
            best_portfolios.append(sorted_portfolios[0])

    return best_portfolios
