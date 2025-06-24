"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics for various strategy types
including SMA, EMA, and MACD.
"""

from typing import Any, Callable, Dict, List, Optional

import polars as pl

from app.strategies.tools.process_ma_portfolios import process_ma_portfolios
from app.strategies.tools.process_strategy_portfolios import process_macd_strategy

# Import export_portfolios inside functions to avoid circular imports
from app.tools.get_config import get_config
from app.tools.portfolio_transformation import reorder_columns
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import is_exit_signal_current, is_signal_current


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

        # Debug: log available keys
        all_keys = list(row.keys())
        log(f"Available keys for {ticker}: {all_keys[:10]}...", "debug")

        # Check for date columns specifically
        date_related_keys = [
            k for k in all_keys if "position" in k.lower() or "date" in k.lower()
        ]
        log(f"Date-related keys for {ticker}: {date_related_keys}", "info")

        # Extract strategy parameters - try both uppercase and canonical names
        short_window = row.get("SHORT_WINDOW") or row.get("Short Window")
        long_window = row.get("LONG_WINDOW") or row.get("Long Window")
        signal_window = row.get("SIGNAL_WINDOW") or row.get("Signal Window")

        # Determine strategy type - try both uppercase and canonical names
        strategy_type = row.get("STRATEGY_TYPE") or row.get("Strategy Type")
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
        has_windows = short_window is not None and long_window is not None
        if not has_windows:
            log(f"Skipping {ticker}: No valid window combinations provided", "error")
            return None

        # Convert window values to integers
        short_window = int(short_window)
        long_window = int(long_window)
        if signal_window is not None:
            signal_window = int(signal_window)

        # Process based on strategy type
        result = None

        if strategy_type == "MACD":
            # Validate MACD-specific parameters
            if signal_window is None:
                log(
                    f"Skipping MACD strategy for {ticker}: Missing signal window parameter",
                    "error",
                )
                return None

            log(
                f"Processing MACD strategy for {ticker} with parameters {short_window}/{long_window}/{signal_window}"
            )
            try:
                result = process_macd_strategy(
                    ticker=ticker,
                    short_window=short_window,
                    long_window=long_window,
                    signal_window=signal_window,
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
                        # Check if there's a current entry signal
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

                        stats = portfolio.stats()
                        stats["Ticker"] = ticker
                        stats["Strategy Type"] = "MACD"
                        stats["Short Window"] = short_window
                        stats["Long Window"] = long_window
                        stats["Signal Window"] = signal_window

                        # Add Allocation [%] and Stop Loss [%] columns
                        # Get allocation and stop loss values, checking both naming
                        # conventions
                        allocation = row.get("ALLOCATION", row.get("Allocation [%]"))
                        stop_loss = row.get("STOP_LOSS", row.get("Stop Loss [%]"))
                        # Convert allocation and stop loss values to float, handling
                        # string 'None' values
                        if (
                            allocation is not None
                            and allocation != ""
                            and allocation != "None"
                        ):
                            try:
                                stats["Allocation [%]"] = float(allocation)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid allocation value for {ticker}: {allocation}",
                                    "warning",
                                )
                                stats["Allocation [%]"] = None
                        else:
                            stats["Allocation [%]"] = None

                        if (
                            stop_loss is not None
                            and stop_loss != ""
                            and stop_loss != "None"
                        ):
                            try:
                                stats["Stop Loss [%]"] = float(stop_loss)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid stop loss value for {ticker}: {stop_loss}",
                                    "warning",
                                )
                                stats["Stop Loss [%]"] = None
                        else:
                            stats["Stop Loss [%]"] = None

                        # Preserve Last Position Open Date and Last Position Close Date
                        last_open_date = row.get("Last Position Open Date")
                        if (
                            last_open_date is not None
                            and last_open_date != ""
                            and last_open_date != "None"
                        ):
                            stats["Last Position Open Date"] = last_open_date
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker}: {last_open_date}",
                                "info",
                            )
                        else:
                            stats["Last Position Open Date"] = None
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker} to None (input was: {last_open_date})",
                                "info",
                            )

                        last_close_date = row.get("Last Position Close Date")
                        if (
                            last_close_date is not None
                            and last_close_date != ""
                            and last_close_date != "None"
                        ):
                            stats["Last Position Close Date"] = last_close_date
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker}: {last_close_date}",
                                "info",
                            )
                        else:
                            stats["Last Position Close Date"] = None
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker} to None (input was: {last_close_date})",
                                "info",
                            )

                        # Convert stats with current signal status
                        converted_stats = convert_stats(
                            stats, log, config, current_signal, exit_signal
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
                sma_fast = short_window if strategy_type == "SMA" else None
                sma_slow = long_window if strategy_type == "SMA" else None
                ema_fast = short_window if strategy_type == "EMA" else None
                ema_slow = long_window if strategy_type == "EMA" else None

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
                        # Check if there's a current entry signal
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

                        sma_stats = sma_portfolio.stats()
                        sma_stats["Ticker"] = ticker
                        sma_stats["Strategy Type"] = "SMA"
                        sma_stats["Short Window"] = short_window
                        sma_stats["Long Window"] = long_window

                        # Add Allocation [%] and Stop Loss [%] columns
                        # Get allocation and stop loss values, checking both naming
                        # conventions
                        allocation = row.get("ALLOCATION", row.get("Allocation [%]"))
                        stop_loss = row.get("STOP_LOSS", row.get("Stop Loss [%]"))
                        # Convert allocation and stop loss values to float, handling
                        # string 'None' values
                        if (
                            allocation is not None
                            and allocation != ""
                            and allocation != "None"
                        ):
                            try:
                                sma_stats["Allocation [%]"] = float(allocation)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid allocation value for {ticker}: {allocation}",
                                    "warning",
                                )
                                sma_stats["Allocation [%]"] = None
                        else:
                            sma_stats["Allocation [%]"] = None

                        if (
                            stop_loss is not None
                            and stop_loss != ""
                            and stop_loss != "None"
                        ):
                            try:
                                sma_stats["Stop Loss [%]"] = float(stop_loss)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid stop loss value for {ticker}: {stop_loss}",
                                    "warning",
                                )
                                sma_stats["Stop Loss [%]"] = None
                        else:
                            sma_stats["Stop Loss [%]"] = None

                        # Preserve Last Position Open Date and Last Position Close Date
                        last_open_date = row.get("Last Position Open Date")
                        if (
                            last_open_date is not None
                            and last_open_date != ""
                            and last_open_date != "None"
                        ):
                            sma_stats["Last Position Open Date"] = last_open_date
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker} (SMA): {last_open_date}",
                                "info",
                            )
                        else:
                            sma_stats["Last Position Open Date"] = None
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker} (SMA) to None (input was: {last_open_date})",
                                "info",
                            )

                        last_close_date = row.get("Last Position Close Date")
                        if (
                            last_close_date is not None
                            and last_close_date != ""
                            and last_close_date != "None"
                        ):
                            sma_stats["Last Position Close Date"] = last_close_date
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker} (SMA): {last_close_date}",
                                "info",
                            )
                        else:
                            sma_stats["Last Position Close Date"] = None
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker} (SMA) to None (input was: {last_close_date})",
                                "info",
                            )

                        # Convert stats with current signal status
                        sma_converted_stats = convert_stats(
                            sma_stats, log, config, current_signal, exit_signal
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
                        # Check if there's a current entry signal
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

                        ema_stats = ema_portfolio.stats()
                        ema_stats["Ticker"] = ticker
                        ema_stats["Strategy Type"] = "EMA"
                        ema_stats["Short Window"] = short_window
                        ema_stats["Long Window"] = long_window

                        # Add Allocation [%] and Stop Loss [%] columns
                        # Get allocation and stop loss values, checking both naming
                        # conventions
                        allocation = row.get("ALLOCATION", row.get("Allocation [%]"))
                        stop_loss = row.get("STOP_LOSS", row.get("Stop Loss [%]"))
                        # Convert allocation and stop loss values to float, handling
                        # string 'None' values
                        if (
                            allocation is not None
                            and allocation != ""
                            and allocation != "None"
                        ):
                            try:
                                ema_stats["Allocation [%]"] = float(allocation)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid allocation value for {ticker}: {allocation}",
                                    "warning",
                                )
                                ema_stats["Allocation [%]"] = None
                        else:
                            ema_stats["Allocation [%]"] = None

                        if (
                            stop_loss is not None
                            and stop_loss != ""
                            and stop_loss != "None"
                        ):
                            try:
                                ema_stats["Stop Loss [%]"] = float(stop_loss)
                            except (ValueError, TypeError):
                                log(
                                    f"Invalid stop loss value for {ticker}: {stop_loss}",
                                    "warning",
                                )
                                ema_stats["Stop Loss [%]"] = None
                        else:
                            ema_stats["Stop Loss [%]"] = None

                        # Preserve Last Position Open Date and Last Position Close Date
                        last_open_date = row.get("Last Position Open Date")
                        if (
                            last_open_date is not None
                            and last_open_date != ""
                            and last_open_date != "None"
                        ):
                            ema_stats["Last Position Open Date"] = last_open_date
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker} (EMA): {last_open_date}",
                                "info",
                            )
                        else:
                            ema_stats["Last Position Open Date"] = None
                            log(
                                f"DEBUG: Set Last Position Open Date for {ticker} (EMA) to None (input was: {last_open_date})",
                                "info",
                            )

                        last_close_date = row.get("Last Position Close Date")
                        if (
                            last_close_date is not None
                            and last_close_date != ""
                            and last_close_date != "None"
                        ):
                            ema_stats["Last Position Close Date"] = last_close_date
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker} (EMA): {last_close_date}",
                                "info",
                            )
                        else:
                            ema_stats["Last Position Close Date"] = None
                            log(
                                f"DEBUG: Set Last Position Close Date for {ticker} (EMA) to None (input was: {last_close_date})",
                                "info",
                            )

                        # Convert stats with current signal status
                        ema_converted_stats = convert_stats(
                            ema_stats, log, config, current_signal, exit_signal
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
        # Phase 1 Data Flow Audit: Log initial portfolio data
        log(
            f"📊 PHASE 1 AUDIT: export_summary_results() entry with {len(portfolios)} portfolios",
            "info",
        )

        # Log metric type distribution in input data
        metric_type_counts = {}
        ticker_strategy_configs = {}
        for p in portfolios:
            metric_type = p.get("Metric Type", "Unknown")
            metric_type_counts[metric_type] = metric_type_counts.get(metric_type, 0) + 1

            # Track configurations per ticker+strategy
            key = f"{p.get('Ticker', 'N/A')},{p.get('Strategy Type', 'N/A')},{p.get('Short Window', 'N/A')},{p.get('Long Window', 'N/A')}"
            if key not in ticker_strategy_configs:
                ticker_strategy_configs[key] = []
            ticker_strategy_configs[key].append(metric_type)

        log(f"📊 INPUT METRIC TYPES: {dict(metric_type_counts)}", "info")
        log(
            f"📊 CONFIGURATIONS WITH MULTIPLE METRICS: {len([k for k, v in ticker_strategy_configs.items() if len(v) > 1])}",
            "info",
        )

        # Log CBRE specific data if present
        cbre_configs = {
            k: v for k, v in ticker_strategy_configs.items() if k.startswith("CBRE")
        }
        if cbre_configs:
            log(f"📊 CBRE CONFIGURATIONS: {cbre_configs}", "info")
        # Reorder columns for each portfolio
        reordered_portfolios = [reorder_columns(p) for p in portfolios]

        # Use provided config or get default if none provided
        export_config = config if config is not None else get_config({})
        export_config["TICKER"] = None

        # Remove duplicates based on Ticker, Use SMA, Short Window, Long Window
        try:
            # Convert to Polars DataFrame for deduplication
            df = pl.DataFrame(reordered_portfolios)
            log(f"📊 BEFORE DEDUPLICATION: {len(df)} portfolios in DataFrame", "info")

            # Log metric type distribution before deduplication
            if "Metric Type" in df.columns:
                metric_dist_before = (
                    df.group_by("Metric Type")
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                )
                log(
                    f"📊 METRIC TYPES BEFORE DEDUP: {metric_dist_before.to_dicts()}",
                    "info",
                )

                # Log CBRE specific data before deduplication
                cbre_data = df.filter(pl.col("Ticker") == "CBRE")
                if len(cbre_data) > 0:
                    log(f"📊 CBRE DATA BEFORE DEDUP: {len(cbre_data)} rows", "info")
                    cbre_metrics = cbre_data.select(
                        "Ticker",
                        "Strategy Type",
                        "Short Window",
                        "Long Window",
                        "Metric Type",
                    ).to_dicts()
                    log(f"📊 CBRE METRICS BEFORE: {cbre_metrics}", "info")

            # Phase 2 Fix: Include Metric Type in uniqueness check to preserve all metric types
            uniqueness_columns = [
                "Ticker",
                "Strategy Type",
                "Short Window",
                "Long Window",
            ]

            # If Metric Type column exists, include it in uniqueness check to preserve different metric types
            if "Metric Type" in df.columns:
                uniqueness_columns.append("Metric Type")
                log(f"📊 PHASE 2 FIX: Including Metric Type in uniqueness check", "info")
            else:
                log(
                    f"📊 No Metric Type column found, using standard uniqueness check",
                    "info",
                )

            # Check for duplicate entries using the enhanced uniqueness columns
            duplicate_count = len(df) - df.unique(subset=uniqueness_columns).height

            if duplicate_count > 0:
                log(
                    f"🔧 Found {duplicate_count} duplicate entries using uniqueness columns: {uniqueness_columns}",
                    "info",
                )

                # Keep only unique combinations of the specified columns (now including Metric Type)
                df = df.unique(
                    subset=uniqueness_columns,
                    keep="first",
                )
                log(
                    f"📊 AFTER DEDUPLICATION: {len(df)} unique combinations (Metric Types preserved)",
                    "info",
                )

                # Log metric type distribution after deduplication
                if "Metric Type" in df.columns:
                    metric_dist_after = (
                        df.group_by("Metric Type")
                        .agg(pl.len().alias("count"))
                        .sort("count", descending=True)
                    )
                    log(
                        f"📊 METRIC TYPES AFTER DEDUP: {metric_dist_after.to_dicts()}",
                        "warning",
                    )

                    # Log CBRE specific data after deduplication
                    cbre_data_after = df.filter(pl.col("Ticker") == "CBRE")
                    if len(cbre_data_after) > 0:
                        log(
                            f"📊 CBRE DATA AFTER DEDUP: {len(cbre_data_after)} rows",
                            "info",
                        )
                        cbre_metrics_after = cbre_data_after.select(
                            "Ticker",
                            "Strategy Type",
                            "Short Window",
                            "Long Window",
                            "Metric Type",
                        ).to_dicts()
                        log(f"📊 CBRE METRICS AFTER: {cbre_metrics_after}", "info")

                        # Phase 2 Validation: Check if multiple metric types are preserved for same configuration
                        cbre_configs = {}
                        for row in cbre_metrics_after:
                            config_key = f"{row['Ticker']},{row['Strategy Type']},{row['Short Window']},{row['Long Window']}"
                            if config_key not in cbre_configs:
                                cbre_configs[config_key] = []
                            cbre_configs[config_key].append(row["Metric Type"])

                        for config_key, metrics in cbre_configs.items():
                            if len(metrics) > 1:
                                log(
                                    f"✅ PHASE 2 SUCCESS: {config_key} preserved {len(metrics)} metric types: {metrics}",
                                    "info",
                                )
                            else:
                                log(
                                    f"⚠️ PHASE 2 NOTICE: {config_key} has only {len(metrics)} metric type(s): {metrics}",
                                    "warning",
                                )

                # Convert back to list of dictionaries
                reordered_portfolios = df.to_dicts()
            else:
                log(f"📊 NO DUPLICATES FOUND: {len(df)} portfolios preserved", "info")
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")

        # Filter out portfolios with invalid metrics
        try:
            from app.tools.portfolio.filters import filter_invalid_metrics

            # Apply the filter
            filtered_portfolios = filter_invalid_metrics(reordered_portfolios, log)

            # Update the portfolios list
            reordered_portfolios = filtered_portfolios

            log(
                f"After filtering invalid metrics: {len(reordered_portfolios)} portfolios remain"
            )
        except Exception as e:
            log(f"Error during invalid metrics filtering: {str(e)}", "warning")

        # Check if we have any portfolios left after filtering
        if not reordered_portfolios:
            log("No portfolios remain after filtering invalid metrics", "warning")
            return False

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

        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios

        # Pass the export_config which may contain _SORTED_PORTFOLIOS if sorting was applied
        # Ensure Allocation [%] and Stop Loss [%] columns exist in the DataFrame
        if "Allocation [%]" not in df.columns:
            log(
                "Adding empty Allocation [%] column to ensure Extended Schema format",
                "info",
            )
            # Use pl.Float64 type with None values instead of string "None"
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias("Allocation [%]"))

        if "Stop Loss [%]" not in df.columns:
            log(
                "Adding empty Stop Loss [%] column to ensure Extended Schema format",
                "info",
            )
            # Use pl.Float64 type with None values instead of string "None"
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias("Stop Loss [%]"))

        # Ensure Last Position Open Date and Last Position Close Date columns exist
        if "Last Position Open Date" not in df.columns:
            log(
                "Adding empty Last Position Open Date column to ensure Extended Schema format",
                "info",
            )
            df = df.with_columns(
                pl.lit(None).cast(pl.Utf8).alias("Last Position Open Date")
            )

        if "Last Position Close Date" not in df.columns:
            log(
                "Adding empty Last Position Close Date column to ensure Extended Schema format",
                "info",
            )
            df = df.with_columns(
                pl.lit(None).cast(pl.Utf8).alias("Last Position Close Date")
            )

        # Convert back to list of dictionaries
        reordered_portfolios = df.to_dicts()

        # Phase 1 Data Flow Audit: Log final data before export_portfolios
        log(
            f"📊 FINAL DATA TO export_portfolios(): {len(reordered_portfolios)} portfolios",
            "info",
        )

        # Log final metric type distribution
        final_metric_counts = {}
        final_cbre_data = []
        for p in reordered_portfolios:
            metric_type = p.get("Metric Type", "Unknown")
            final_metric_counts[metric_type] = (
                final_metric_counts.get(metric_type, 0) + 1
            )

            if p.get("Ticker") == "CBRE":
                final_cbre_data.append(
                    {
                        "Ticker": p.get("Ticker"),
                        "Strategy": p.get("Strategy Type"),
                        "Short": p.get("Short Window"),
                        "Long": p.get("Long Window"),
                        "Metric": p.get("Metric Type"),
                    }
                )

        log(f"📊 FINAL METRIC TYPES: {dict(final_metric_counts)}", "info")
        if final_cbre_data:
            log(f"📊 FINAL CBRE DATA: {final_cbre_data}", "info")

        # Note: Allocation distribution will be handled by export_portfolios
        # which uses ensure_allocation_sum_100_percent for all export types

        # Change feature_dir to "strategies" to export to /csv/strategies instead
        # of /csv/portfolios
        _, success = export_portfolios(
            reordered_portfolios,
            export_config,
            "portfolios",
            portfolio_name,
            log,
            feature_dir="strategies",
        )
        if not success:
            log("Failed to export portfolios", "error")
            return False

        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
