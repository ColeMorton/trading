"""
Signal Processing Module

This module provides utilities for processing trading signals and portfolios.
"""

from typing import Callable, Optional

import polars as pl

from app.strategies.ma_cross.tools.sensitivity_analysis import (
    analyze_window_combination,
)
from app.strategies.ma_cross.tools.signal_generation import generate_current_signals
from app.tools.get_data import get_data
from app.tools.portfolio.processing import process_single_ticker
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)
from app.tools.strategy.types import StrategyConfig as Config


def process_current_signals(
    ticker: str, config: Config, log: Callable
) -> Optional[pl.DataFrame]:
    """Process current signals for a ticker.

    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration dictionary
        log: Logging function

    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker

    try:
        # Get strategy type from config or default to SMA
        strategy_type = config_copy.get("STRATEGY_TYPE", "SMA")

        # Generate and validate current signals
        current_signals = generate_current_signals(config_copy, log)
        if len(current_signals) == 0:
            log(f"No current signals found for {ticker} {strategy_type}", "warning")
            return None

        log(f"Current signals for {ticker} {strategy_type}")

        # Get and validate price data
        # Ensure synthetic tickers use underscore format
        formatted_ticker = (
            ticker.replace("/", "_") if isinstance(ticker, str) else ticker
        )
        data_result = get_data(formatted_ticker, config_copy, log)
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result
            config_copy["TICKER"] = (
                synthetic_ticker  # Update config with synthetic ticker
            )
        else:
            data = data_result

        if data is None:
            log(f"Failed to get price data for {config_copy['TICKER']}", "error")
            return None

        # Analyze each window combination
        portfolios = []
        for row in current_signals.iter_rows(named=True):
            result = analyze_window_combination(
                data, row["Short Window"], row["Long Window"], config_copy, log
            )
            if result is not None:
                # Add Allocation [%] and Stop Loss [%] fields if they exist in config
                if "ALLOCATION" in config_copy:
                    result["Allocation [%]"] = config_copy["ALLOCATION"]
                if "STOP_LOSS" in config_copy:
                    result["Stop Loss [%]"] = config_copy["STOP_LOSS"]
                portfolios.append(result)

        if not portfolios:
            return None

        # Convert to DataFrame
        portfolios_df = pl.DataFrame(portfolios)

        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        portfolio_dicts = portfolios_df.to_dicts()
        schema_version = detect_schema_version(portfolio_dicts)
        log(
            f"Detected schema version for current signals: {schema_version.name}",
            "info",
        )

        # Normalize portfolio data
        normalized_portfolios = normalize_portfolio_data(
            portfolio_dicts, schema_version, log
        )

        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_portfolios = ensure_allocation_sum_100_percent(
                normalized_portfolios, log
            )

        return pl.DataFrame(normalized_portfolios)

    except Exception as e:
        log(f"Failed to process current signals: {str(e)}", "error")
        return None


def process_ticker_portfolios(
    ticker: str, config: Config, log: Callable
) -> Optional[pl.DataFrame]:
    """Process portfolios for a single ticker.

    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    try:
        if config.get("USE_CURRENT", False):
            return process_current_signals(ticker, config, log)
        else:
            portfolios = process_single_ticker(ticker, config, log)
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                return None

            # Convert to DataFrame
            portfolios_df = pl.DataFrame(portfolios)

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%]
            # columns
            portfolio_dicts = portfolios_df.to_dicts()
            schema_version = detect_schema_version(portfolio_dicts)
            log(
                f"Detected schema version for ticker portfolios: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data
            normalized_portfolios = normalize_portfolio_data(
                portfolio_dicts, schema_version, log
            )

            # Ensure allocation values sum to 100% if they exist
            if schema_version == SchemaVersion.EXTENDED:
                normalized_portfolios = ensure_allocation_sum_100_percent(
                    normalized_portfolios, log
                )

            strategy_type = config.get("STRATEGY_TYPE", "SMA")
            # Use the ticker from config which may contain the synthetic ticker
            actual_ticker = config.get("TICKER", ticker)
            log(f"Results for {actual_ticker} {strategy_type}")

            return pl.DataFrame(normalized_portfolios)

    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        return None
