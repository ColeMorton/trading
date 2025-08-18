"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics for various strategy types
including SMA, EMA, and MACD.
"""

from typing import Any, Callable, Dict, List, Optional

import polars as pl

from app.strategies.ma_cross.tools.process_ma_portfolios import process_ma_portfolios
from app.strategies.ma_cross.tools.process_strategy_portfolios import (
    process_macd_strategy,
)
from app.strategies.ma_cross.tools.signal_utils import is_signal_current

# Import export_portfolios inside functions to avoid circular imports
from app.tools.config_service import ConfigService
from app.tools.portfolio_transformation import reorder_columns
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import (
    calculate_signal_unconfirmed,
    calculate_signal_unconfirmed_realtime,
    is_exit_signal_current,
    is_signal_current,
)


def process_ticker_portfolios(
    ticker: str, row: dict, config: Dict[str, Any], log: Callable[[str, str], None]
) -> Optional[List[dict]]:
    """
    Process portfolios for a single ticker based on strategy type.

    Args:
        ticker (str): Ticker symbol
        row (dict): Row data containing strategy parameters
        config (dict): Configuration dictionary including USE_HOURLY setting
        log (Callable): Logging function

    Returns:
        Optional[List[dict]]: List containing valid portfolio statistics
        or None if processing fails
    """
    try:
        portfolios = []

        # Extract strategy parameters - check both top level and nested PORTFOLIO_STATS
        portfolio_stats = row.get("PORTFOLIO_STATS", {})

        # Try original column names first (what we actually have), then standardized/legacy names
        fast_period = (
            row.get("Fast Period")
            or row.get("FAST_PERIOD")
            or portfolio_stats.get("FAST_PERIOD")
            or row.get("FAST_PERIOD")
            or portfolio_stats.get("FAST_PERIOD")
        )

        slow_period = (
            row.get("Slow Period")
            or row.get("SLOW_PERIOD")
            or portfolio_stats.get("SLOW_PERIOD")
            or row.get("SLOW_PERIOD")
            or portfolio_stats.get("SLOW_PERIOD")
        )

        signal_period = (
            row.get("Signal Period")
            or row.get("SIGNAL_PERIOD")
            or portfolio_stats.get("SIGNAL_PERIOD")
            or row.get("SIGNAL_PERIOD")
            or portfolio_stats.get("SIGNAL_PERIOD")
        )

        # Determine strategy type
        strategy_type = row.get("STRATEGY_TYPE")
        use_sma = row.get("USE_SMA", True)

        # Handle legacy portfolios without explicit strategy type
        if not strategy_type:
            # Convert USE_SMA to boolean if it's a string
            if isinstance(use_sma, str):
                use_sma = use_sma.lower() in ["true", "yes", "1"]

            # Set strategy type based on USE_SMA flag
            strategy_type = "SMA" if use_sma else "EMA"
            log(
                f"Using derived strategy type {strategy_type} for {ticker} based on USE_SMA={use_sma}",
                "info",
            )

        # Validate required parameters
        has_windows = fast_period is not None and slow_period is not None
        if not has_windows:
            log(f"Skipping {ticker}: No valid window combinations provided", "error")
            return None

        # Convert window values to integers
        fast_period = int(fast_period)
        slow_period = int(slow_period)
        if signal_period is not None:
            signal_period = int(signal_period)

        # Validate that window values are positive (skip corrupted data)
        if fast_period <= 0 or slow_period <= 0:
            log(
                f"Skipping {ticker}: Invalid window values (short={fast_period}, long={slow_period})",
                "warning",
            )
            return None

        # Process based on strategy type
        result = None

        if strategy_type == "MACD":
            # Validate MACD-specific parameters
            if signal_period is None or signal_period <= 0:
                log(
                    f"Skipping MACD strategy for {ticker}: Invalid signal period parameter (value={signal_period})",
                    "warning",
                )
                return None

            log(
                f"Processing MACD strategy for {ticker} with parameters {fast_period}/{slow_period}/{signal_period}"
            )
            try:
                result = process_macd_strategy(
                    ticker=ticker,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                    config=config,
                    log=log,
                )
            except Exception as e:
                log(f"Failed to process MACD strategy for {ticker}: {str(e)}", "error")
                return None

            if result:
                portfolio, result_config, signal_data = result

                if portfolio is not None and signal_data is not None:
                    try:
                        # Check if there's a current signal
                        current_signal = is_signal_current(signal_data, config)
                        log(
                            f"Current MACD signal for {ticker}: {current_signal}",
                            "info",
                        )

                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(signal_data, config)
                        log(
                            f"Current MACD exit signal for {ticker}: {exit_signal}",
                            "info",
                        )

                        # Get total open trades from portfolio stats
                        portfolio_stats = portfolio.stats()
                        total_open_trades = portfolio_stats.get("Total Open Trades", 0)
                        
                        # Calculate unconfirmed signal using real-time data
                        signal_unconfirmed = calculate_signal_unconfirmed_realtime(
                            ticker=ticker,
                            strategy_type="MACD",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_entry=current_signal,
                            signal_exit=exit_signal,
                            total_open_trades=total_open_trades,
                            config=config,
                            signal_period=signal_period,
                        )
                        log(
                            f"Signal Unconfirmed for {ticker} MACD: {signal_unconfirmed}",
                            "info",
                        )

                        stats = portfolio.stats()
                        stats["Ticker"] = ticker
                        stats["Strategy Type"] = "MACD"
                        stats["Fast Period"] = fast_period
                        stats["Slow Period"] = slow_period
                        stats["Signal Period"] = signal_period

                        # Convert stats with current signal status
                        converted_stats = convert_stats(
                            stats, log, config, current_signal, None, signal_unconfirmed
                        )
                        portfolios.append(converted_stats)
                    except Exception as e:
                        log(
                            f"Failed to process MACD stats for {ticker}: {str(e)}",
                            "error",
                        )

        elif strategy_type in ["SMA", "EMA"]:
            # For backward compatibility, use the existing process_ma_portfolios
            # function
            try:
                # Set SMA or EMA values based on strategy type
                sma_fast = fast_period if strategy_type == "SMA" else None
                sma_slow = slow_period if strategy_type == "SMA" else None
                ema_fast = fast_period if strategy_type == "EMA" else None
                ema_slow = slow_period if strategy_type == "EMA" else None

                legacy_result = process_ma_portfolios(
                    ticker=ticker,
                    sma_fast=sma_fast,
                    sma_slow=sma_slow,
                    ema_fast=ema_fast,
                    ema_slow=ema_slow,
                    config=config,
                    log=log,
                )

                if legacy_result is None:
                    return None

                (
                    sma_portfolio,
                    ema_portfolio,
                    result_config,
                    sma_data,
                    ema_data,
                ) = legacy_result

                # Process SMA stats if portfolio exists
                if (
                    strategy_type == "SMA"
                    and sma_portfolio is not None
                    and sma_data is not None
                ):
                    try:
                        # Check if there's a current signal
                        current_signal = is_signal_current(sma_data, config)
                        log(
                            f"Current SMA signal for {ticker}: {current_signal}", "info"
                        )

                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(sma_data, config)
                        log(
                            f"Current SMA exit signal for {ticker}: {exit_signal}",
                            "info",
                        )

                        # Get total open trades from portfolio stats
                        sma_portfolio_stats = sma_portfolio.stats()
                        total_open_trades = sma_portfolio_stats.get("Total Open Trades", 0)
                        
                        # Calculate unconfirmed signal using real-time data
                        signal_unconfirmed = calculate_signal_unconfirmed_realtime(
                            ticker=ticker,
                            strategy_type="SMA",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_entry=current_signal,
                            signal_exit=exit_signal,
                            total_open_trades=total_open_trades,
                            config=config,
                            signal_period=None,
                        )
                        log(
                            f"Signal Unconfirmed for {ticker} SMA: {signal_unconfirmed}",
                            "info",
                        )

                        sma_stats = sma_portfolio.stats()
                        sma_stats["Ticker"] = ticker
                        sma_stats["Strategy Type"] = "SMA"
                        sma_stats["Fast Period"] = fast_period
                        sma_stats["Slow Period"] = slow_period

                        # Convert stats with current signal status
                        sma_converted_stats = convert_stats(
                            sma_stats,
                            log,
                            config,
                            current_signal,
                            None,
                            signal_unconfirmed,
                        )
                        portfolios.append(sma_converted_stats)
                    except Exception as e:
                        log(
                            f"Failed to process SMA stats for {ticker}: {str(e)}",
                            "error",
                        )

                # Process EMA stats if portfolio exists
                if (
                    strategy_type == "EMA"
                    and ema_portfolio is not None
                    and ema_data is not None
                ):
                    try:
                        # Check if there's a current signal
                        current_signal = is_signal_current(ema_data, config)
                        log(
                            f"Current EMA signal for {ticker}: {current_signal}", "info"
                        )

                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(ema_data, config)
                        log(
                            f"Current EMA exit signal for {ticker}: {exit_signal}",
                            "info",
                        )

                        # Get total open trades from portfolio stats
                        ema_portfolio_stats = ema_portfolio.stats()
                        total_open_trades = ema_portfolio_stats.get("Total Open Trades", 0)
                        
                        # Calculate unconfirmed signal using real-time data
                        signal_unconfirmed = calculate_signal_unconfirmed_realtime(
                            ticker=ticker,
                            strategy_type="EMA",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_entry=current_signal,
                            signal_exit=exit_signal,
                            total_open_trades=total_open_trades,
                            config=config,
                            signal_period=None,
                        )
                        log(
                            f"Signal Unconfirmed for {ticker} EMA: {signal_unconfirmed}",
                            "info",
                        )

                        ema_stats = ema_portfolio.stats()
                        ema_stats["Ticker"] = ticker
                        ema_stats["Strategy Type"] = "EMA"
                        ema_stats["Fast Period"] = fast_period
                        ema_stats["Slow Period"] = slow_period

                        # Convert stats with current signal status
                        ema_converted_stats = convert_stats(
                            ema_stats,
                            log,
                            config,
                            current_signal,
                            None,
                            signal_unconfirmed,
                        )
                        portfolios.append(ema_converted_stats)
                    except Exception as e:
                        log(
                            f"Failed to process EMA stats for {ticker}: {str(e)}",
                            "error",
                        )

            except Exception as e:
                log(
                    f"Failed to process {strategy_type} strategy for {ticker}: {str(e)}",
                    "error",
                )
                return None

        else:
            log(f"Unsupported strategy type: {strategy_type} for {ticker}", "error")
            return None

        return portfolios if portfolios else None

    except Exception as e:
        log(f"Failed to process stats for {ticker}: {str(e)}", "error")
        return None


def export_summary_results(
    portfolios: List[Dict],
    portfolio_name: str,
    log: Callable[[str, str], None],
    config: Optional[Dict] | None = None,
) -> bool:
    """
    Export portfolio summary results to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        portfolio_name (str): Name of the portfolio file
        log (Callable): Logging function
        config (Optional[Dict]): Configuration dictionary including USE_HOURLY setting

    Returns:
        bool: True if export successful, False otherwise
    """
    if portfolios:
        # SAFETY GUARD: Validate portfolios have meaningful data before export
        valid_portfolios = []
        for i, portfolio in enumerate(portfolios):
            # Check if portfolio has valid window parameters
            fast_period = portfolio.get("Fast Period", portfolio.get("FAST_PERIOD", 0))
            slow_period = portfolio.get("Slow Period", portfolio.get("SLOW_PERIOD", 0))

            # Debug: Show all available keys and their values for the first few portfolios
            if i < 3:
                ticker = portfolio.get("Ticker", "Unknown")
                strategy_type = portfolio.get("Strategy Type", "Unknown")
                log(
                    f"DEBUG PORTFOLIO {i+1} ({ticker} {strategy_type}): Keys available: {list(portfolio.keys())[:10]}...",
                    "info",
                )
                log(
                    f"DEBUG PORTFOLIO {i+1}: Fast Period={portfolio.get('Fast Period')}, FAST_PERIOD={portfolio.get('FAST_PERIOD')}, Fast Period={portfolio.get('Fast Period')}, FAST_PERIOD={portfolio.get('FAST_PERIOD')}",
                    "info",
                )

            # For strategies without signal period (SMA/EMA), check if window values are valid
            if fast_period > 0 and slow_period > 0:
                valid_portfolios.append(portfolio)
            else:
                ticker = portfolio.get("Ticker", "Unknown")
                strategy_type = portfolio.get("Strategy Type", "Unknown")
                log(
                    f"SAFETY GUARD: Skipping invalid portfolio {ticker} {strategy_type} "
                    f"(fast={fast_period}, slow={slow_period})",
                    "warning",
                )

        # Prevent export if no valid portfolios found
        if not valid_portfolios:
            log(
                "SAFETY GUARD: Aborting export - no valid portfolios found. "
                "This prevents corruption of input files with invalid data.",
                "error",
            )
            return False

        # Use only valid portfolios for export
        portfolios = valid_portfolios
        log(f"SAFETY GUARD: Proceeding with {len(portfolios)} valid portfolios", "info")

        # Reorder columns for each portfolio
        reordered_portfolios = [reorder_columns(p) for p in portfolios]

        # Use provided config or get default if none provided
        export_config = (
            config if config is not None else ConfigService.process_config({})
        )
        export_config["TICKER"] = None

        # Remove duplicates based on Ticker, Use SMA, Fast Period, Slow Period
        try:
            # Convert to Polars DataFrame for deduplication
            df = pl.DataFrame(reordered_portfolios)

            # Check for duplicate entries
            duplicate_count = (
                len(df)
                - df.unique(
                    subset=["Ticker", "Strategy Type", "Fast Period", "Slow Period"]
                ).height
            )

            if duplicate_count > 0:
                log(
                    f"Found {duplicate_count} duplicate entries. Removing duplicates...",
                    "warning",
                )

                # Keep only unique combinations of the specified columns
                # Use correct column names: Fast Period and Slow Period
                df = df.unique(
                    subset=["Ticker", "Strategy Type", "Fast Period", "Slow Period"],
                    keep="first",
                )
                log(f"After deduplication: {len(df)} unique strategy combinations")

                # Convert back to list of dictionaries
                reordered_portfolios = df.to_dicts()
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")

        # Sort portfolios if SORT_BY is specified in config
        if export_config.get("SORT_BY"):
            try:
                # Convert to Polars DataFrame for sorting
                df = pl.DataFrame(reordered_portfolios)

                # Apply sorting
                sort_by = export_config["SORT_BY"]
                sort_asc = export_config.get("SORT_ASC", False)

                if sort_by in df.columns:
                    # Sort the DataFrame
                    df = df.sort(sort_by, descending=not sort_asc)
                    log(
                        f"Sorted results by {sort_by} ({'ascending' if sort_asc else 'descending'})"
                    )

                    # Convert back to list of dictionaries
                    reordered_portfolios = df.to_dicts()

                    # Ensure the sort order is preserved by setting it in the export_config
                    # This will be used by export_portfolios to maintain the order
                    export_config["_SORTED_PORTFOLIOS"] = reordered_portfolios
                else:
                    log(
                        f"Warning: Sort column '{sort_by}' not found in results",
                        "warning",
                    )
            except Exception as e:
                log(f"Error during sorting: {str(e)}", "warning")

        # Use 'portfolios' for feature_dir to export to /data/raw/portfolios/
        # instead of overwriting input files in /data/raw/strategies/
        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios

        # Pass the export_config which may contain _SORTED_PORTFOLIOS if sorting
        # was applied
        _, success = export_portfolios(
            reordered_portfolios,
            export_config,
            "portfolios",
            portfolio_name,
            log,
            feature_dir="portfolios",
        )
        if not success:
            log("Failed to export portfolios", "error")
            return False

        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
