"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics for various strategy types
including SMA, EMA, and MACD.
"""

from typing import Any, Callable, Dict, List, Optional

import polars as pl

# Import fresh analysis dispatcher for automatic equity export
from app.strategies.tools.fresh_analysis_dispatcher import (
    dispatch_fresh_analysis,
    should_trigger_fresh_analysis,
)
from app.strategies.tools.process_ma_portfolios import process_ma_portfolios
from app.strategies.tools.process_strategy_portfolios import process_macd_strategy

# Import configuration validation for Phase 4 integration
from app.tools.config_validation import (
    get_equity_metric_selection,
    get_validated_equity_config,
    is_equity_export_enabled,
    log_configuration_validation,
)

# Import equity data extractor for Phase 2 integration
from app.tools.equity_data_extractor import (
    EquityData,
    MetricType,
    extract_equity_data_from_portfolio,
)

# Import export_portfolios inside functions to avoid circular imports
from app.tools.get_config import get_config
from app.tools.portfolio_transformation import reorder_columns
from app.tools.project_utils import get_project_root
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import is_exit_signal_current, is_signal_current


def _extract_equity_data_if_enabled(
    portfolio: any,
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
) -> Optional[EquityData]:
    """
    Extract equity data from portfolio if equity export is enabled.

    Args:
        portfolio: VectorBT Portfolio object
        ticker: Ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD)
        short_window: Short window parameter
        long_window: Long window parameter
        signal_window: Signal window parameter (optional)
        config: Configuration dictionary
        log: Logging function

    Returns:
        EquityData object if extraction successful, None otherwise
    """
    # Use validated configuration check
    if not is_equity_export_enabled(config):
        log(f"Equity data export disabled for {ticker} {strategy_type}", "debug")
        return None

    try:
        # Get validated metric selection from config
        metric_str = get_equity_metric_selection(config)
        log(f"Using metric '{metric_str}' for {ticker} {strategy_type}", "debug")

        # Convert string to MetricType enum (already validated)
        metric_type = MetricType(metric_str)

        # Extract equity data
        equity_data = extract_equity_data_from_portfolio(
            portfolio=portfolio, metric_type=metric_type, config=config, log=log
        )

        log(
            f"Successfully extracted equity data for {ticker} {strategy_type} using {metric_str} metric",
            "info",
        )
        return equity_data

    except Exception as e:
        log(
            f"Failed to extract equity data for {ticker} {strategy_type}: {str(e)}",
            "warning",
        )
        return None


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
                        # Debug: Log portfolio type for equity extraction troubleshooting
                        log(
                            f"DEBUG: Portfolio type for {ticker}: {type(portfolio)}",
                            "debug",
                        )

                        # Check if this is a VectorBT Portfolio object (required for equity extraction)
                        has_vectorbt_portfolio = hasattr(
                            portfolio, "value"
                        ) and hasattr(portfolio, "stats")
                        log(
                            f"DEBUG: {ticker} has VectorBT Portfolio methods: {has_vectorbt_portfolio}",
                            "debug",
                        )

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

                        # Extract equity data if enabled (with automatic fresh analysis)
                        equity_data = None
                        if has_vectorbt_portfolio:
                            equity_data = _extract_equity_data_if_enabled(
                                portfolio=portfolio,
                                ticker=ticker,
                                strategy_type="MACD",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=signal_window,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="MACD",
                            short_window=short_window,
                            long_window=long_window,
                            signal_window=signal_window,
                        ):
                            log(
                                f"Triggering fresh MACD analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="MACD",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=signal_window,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="MACD",
                                    short_window=short_window,
                                    long_window=long_window,
                                    signal_window=signal_window,
                                    config=config,
                                    log=log,
                                )
                            else:
                                log(
                                    f"Failed to generate fresh Portfolio for {ticker} MACD equity export",
                                    "warning",
                                )
                        else:
                            # Check if we're skipping due to existing file
                            force_fresh = config.get("EQUITY_DATA", {}).get(
                                "FORCE_FRESH_ANALYSIS", True
                            )
                            if not force_fresh:
                                try:
                                    from app.tools.equity_export import (
                                        equity_file_exists,
                                        get_equity_file_path,
                                    )

                                    file_exists = equity_file_exists(
                                        ticker=ticker,
                                        strategy_type="MACD",
                                        short_window=short_window,
                                        long_window=long_window,
                                        signal_window=signal_window,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="MACD",
                                            short_window=short_window,
                                            long_window=long_window,
                                            signal_window=signal_window,
                                        )
                                        log(
                                            f"Skipping equity export for {ticker} MACD: file already exists at {file_path}",
                                            "info",
                                        )
                                    else:
                                        log(
                                            f"Skipping equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                            "debug",
                                        )
                                except:
                                    log(
                                        f"Skipping equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                        "debug",
                                    )
                            else:
                                log(
                                    f"Skipping equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                    "debug",
                                )

                        # Store equity data in stats for later export
                        if equity_data is not None:
                            stats["_equity_data"] = equity_data

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
                        # Debug: Log portfolio type for equity extraction troubleshooting
                        log(
                            f"DEBUG: SMA Portfolio type for {ticker}: {type(sma_portfolio)}",
                            "debug",
                        )

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

                        # Extract equity data if enabled (with automatic fresh analysis)
                        has_sma_vectorbt_portfolio = hasattr(
                            sma_portfolio, "value"
                        ) and hasattr(sma_portfolio, "stats")
                        equity_data = None
                        if has_sma_vectorbt_portfolio:
                            equity_data = _extract_equity_data_if_enabled(
                                portfolio=sma_portfolio,
                                ticker=ticker,
                                strategy_type="SMA",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=None,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_sma_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="SMA",
                            short_window=short_window,
                            long_window=long_window,
                            signal_window=None,
                        ):
                            log(
                                f"Triggering fresh SMA analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="SMA",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=None,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="SMA",
                                    short_window=short_window,
                                    long_window=long_window,
                                    signal_window=None,
                                    config=config,
                                    log=log,
                                )
                            else:
                                log(
                                    f"Failed to generate fresh Portfolio for {ticker} SMA equity export",
                                    "warning",
                                )
                        else:
                            # Check if we're skipping due to existing file
                            force_fresh = config.get("EQUITY_DATA", {}).get(
                                "FORCE_FRESH_ANALYSIS", True
                            )
                            if not force_fresh:
                                try:
                                    from app.tools.equity_export import (
                                        equity_file_exists,
                                        get_equity_file_path,
                                    )

                                    file_exists = equity_file_exists(
                                        ticker=ticker,
                                        strategy_type="SMA",
                                        short_window=short_window,
                                        long_window=long_window,
                                        signal_window=None,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="SMA",
                                            short_window=short_window,
                                            long_window=long_window,
                                            signal_window=None,
                                        )
                                        log(
                                            f"Skipping equity export for {ticker} SMA: file already exists at {file_path}",
                                            "info",
                                        )
                                    else:
                                        log(
                                            f"Skipping SMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                            "debug",
                                        )
                                except:
                                    log(
                                        f"Skipping SMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                        "debug",
                                    )
                            else:
                                log(
                                    f"Skipping SMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                    "debug",
                                )

                        # Store equity data in stats for later export
                        if equity_data is not None:
                            sma_stats["_equity_data"] = equity_data
                            log(
                                f"DEBUG: Stored equity data for {ticker} - type: {type(equity_data)}",
                                "debug",
                            )

                        # Convert stats with current signal status
                        sma_converted_stats = convert_stats(
                            sma_stats, log, config, current_signal, exit_signal
                        )

                        # Debug: Check if equity data survived conversion
                        if "_equity_data" in sma_converted_stats:
                            log(
                                f"DEBUG: After convert_stats, equity data type: {type(sma_converted_stats['_equity_data'])}",
                                "debug",
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

                        # Extract equity data if enabled (with automatic fresh analysis)
                        has_ema_vectorbt_portfolio = hasattr(
                            ema_portfolio, "value"
                        ) and hasattr(ema_portfolio, "stats")
                        equity_data = None
                        if has_ema_vectorbt_portfolio:
                            equity_data = _extract_equity_data_if_enabled(
                                portfolio=ema_portfolio,
                                ticker=ticker,
                                strategy_type="EMA",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=None,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_ema_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="EMA",
                            short_window=short_window,
                            long_window=long_window,
                            signal_window=None,
                        ):
                            log(
                                f"Triggering fresh EMA analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="EMA",
                                short_window=short_window,
                                long_window=long_window,
                                signal_window=None,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="EMA",
                                    short_window=short_window,
                                    long_window=long_window,
                                    signal_window=None,
                                    config=config,
                                    log=log,
                                )
                            else:
                                log(
                                    f"Failed to generate fresh Portfolio for {ticker} EMA equity export",
                                    "warning",
                                )
                        else:
                            # Check if we're skipping due to existing file
                            force_fresh = config.get("EQUITY_DATA", {}).get(
                                "FORCE_FRESH_ANALYSIS", True
                            )
                            if not force_fresh:
                                try:
                                    from app.tools.equity_export import (
                                        equity_file_exists,
                                        get_equity_file_path,
                                    )

                                    file_exists = equity_file_exists(
                                        ticker=ticker,
                                        strategy_type="EMA",
                                        short_window=short_window,
                                        long_window=long_window,
                                        signal_window=None,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="EMA",
                                            short_window=short_window,
                                            long_window=long_window,
                                            signal_window=None,
                                        )
                                        log(
                                            f"Skipping equity export for {ticker} EMA: file already exists at {file_path}",
                                            "info",
                                        )
                                    else:
                                        log(
                                            f"Skipping EMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                            "debug",
                                        )
                                except:
                                    log(
                                        f"Skipping EMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                        "debug",
                                    )
                            else:
                                log(
                                    f"Skipping EMA equity extraction for {ticker}: Not a VectorBT Portfolio object (likely pre-computed results)",
                                    "debug",
                                )

                        # Store equity data in stats for later export
                        if equity_data is not None:
                            ema_stats["_equity_data"] = equity_data

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


def _generate_spds_compatible_entries(
    aggregated_portfolios: List[Dict],
    portfolio_name: str,
    log: Callable[[str, str], None],
) -> List[Dict]:
    """
    Generate SPDS-compatible individual strategy entries from trade history data.

    This function creates individual strategy entries that match the actual positions
    in the trade history, ensuring SPDS can properly analyze each strategy.

    Args:
        aggregated_portfolios: List of aggregated portfolio data
        portfolio_name: Name of the portfolio file
        log: Logging function

    Returns:
        List of individual strategy entries compatible with SPDS
    """
    try:
        # Load trade history data from positions file
        positions_file = get_project_root() / "csv" / "positions" / portfolio_name

        if not positions_file.exists():
            log(
                f"No positions file found at {positions_file}, using aggregated data",
                "warning",
            )
            return aggregated_portfolios

        # Read positions data
        positions_df = pl.read_csv(str(positions_file))

        # Create individual strategy entries from positions
        individual_entries = []

        for row in positions_df.iter_rows(named=True):
            # Extract strategy components from Position_UUID
            # Format: TICKER_STRATEGY_TYPE_SHORT_WINDOW_LONG_WINDOW_SIGNAL_WINDOW_DATE
            position_uuid = row.get("Position_UUID", "")
            ticker = row.get("Ticker", "")
            strategy_type = row.get("Strategy_Type", "")
            short_window = row.get("Short_Window", 0)
            long_window = row.get("Long_Window", 0)
            signal_window = row.get("Signal_Window", 0)
            status = row.get("Status", "")

            # Find matching aggregated data for this strategy
            matching_aggregated = None
            for agg_entry in aggregated_portfolios:
                if (
                    agg_entry.get("Ticker") == ticker
                    and agg_entry.get("Strategy Type") == strategy_type
                    and agg_entry.get("Short Window") == short_window
                    and agg_entry.get("Long Window") == long_window
                ):
                    matching_aggregated = agg_entry
                    break

            # Create individual strategy entry
            if matching_aggregated:
                # Copy the aggregated data as base
                individual_entry = matching_aggregated.copy()

                # Override key fields for SPDS compatibility
                individual_entry["Ticker"] = ticker
                individual_entry["Strategy Type"] = strategy_type
                individual_entry["Short Window"] = short_window
                individual_entry["Long Window"] = long_window
                individual_entry["Signal Window"] = signal_window

                # Set signal status based on position status
                individual_entry["Signal Entry"] = status == "Open"
                individual_entry["Signal Exit"] = status == "Closed"

                # Set trade counts based on position status
                individual_entry["Total Open Trades"] = 1 if status == "Open" else 0

                # Add position-specific data
                individual_entry["Position_UUID"] = position_uuid
                individual_entry["Entry_Timestamp"] = row.get("Entry_Timestamp", "")
                individual_entry["Exit_Timestamp"] = row.get("Exit_Timestamp", "")
                individual_entry["Status"] = status

                individual_entries.append(individual_entry)

            else:
                log(
                    f"No matching aggregated data found for {ticker} {strategy_type} {short_window}/{long_window}",
                    "warning",
                )

        if individual_entries:
            log(
                f"Generated {len(individual_entries)} individual strategy entries for SPDS compatibility",
                "info",
            )
            return individual_entries
        else:
            log(
                "No individual entries generated, falling back to aggregated data",
                "warning",
            )
            return aggregated_portfolios

    except Exception as e:
        log(f"Error generating SPDS-compatible entries: {str(e)}", "error")
        log("Falling back to aggregated data", "warning")
        return aggregated_portfolios


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
    # Phase 4: Validate and log configuration before processing
    if config:
        try:
            validated_config = log_configuration_validation(config, log)
            # Update config with validated values (in-place to preserve references)
            config.update(validated_config)
            log("Configuration validation completed successfully", "info")
        except Exception as e:
            log(f"Configuration validation failed: {str(e)}", "error")
            # Continue with unvalidated config but log the issue
    else:
        log("No configuration provided - using default settings", "warning")

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

        # Generate SPDS-compatible individual strategy entries from trade history
        spds_compatible_portfolios = _generate_spds_compatible_entries(
            reordered_portfolios, portfolio_name, log
        )

        # Change feature_dir to "strategies" to export to /data/raw/strategies instead
        # of legacy /csv/portfolios
        _, success = export_portfolios(
            spds_compatible_portfolios,
            export_config,
            "portfolios",
            portfolio_name,
            log,
            feature_dir="strategies",
        )
        if not success:
            log("Failed to export portfolios", "error")
            return False

        # Export equity data if enabled and available
        try:
            from app.tools.equity_export import export_equity_data_batch

            equity_results = export_equity_data_batch(
                portfolios=reordered_portfolios, log=log, config=export_config
            )

            if equity_results["exported_count"] > 0:
                log(
                    f"Equity data export completed: {equity_results['exported_count']} files exported",
                    "info",
                )
            elif (
                equity_results["total_portfolios"] > 0
                and equity_results["exported_count"] == 0
            ):
                log(
                    "No equity data was exported. This happens when processing pre-computed strategy results from CSV files. "
                    + "Equity export requires live backtesting with VectorBT Portfolio objects. "
                    + "To export equity data, run fresh strategy analysis instead of loading existing results.",
                    "info",
                )

        except ImportError:
            log("Equity export module not available", "warning")
        except Exception as e:
            log(f"Error during equity data export: {str(e)}", "warning")
            # Don't fail the entire export process due to equity export errors

        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
