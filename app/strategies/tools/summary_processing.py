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

# Import data normalization functions
from app.tools.portfolio.processing import (
    get_portfolio_schema,
    normalize_portfolio_data,
)
from app.tools.portfolio_transformation import reorder_columns
from app.tools.project_utils import get_project_root
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import (
    calculate_signal_unconfirmed,
    calculate_signal_unconfirmed_realtime,
    is_exit_signal_current,
    is_signal_current,
)


def _extract_equity_data_if_enabled(
    portfolio: any,
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: Optional[int],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
) -> Optional[EquityData]:
    """
    Extract equity data from portfolio if equity export is enabled.

    Args:
        portfolio: VectorBT Portfolio object
        ticker: Ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD)
        fast_period: Fast period parameter
        slow_period: Slow period parameter
        signal_period: Signal period parameter (optional)
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

        # Extract strategy parameters - check both top level and nested PORTFOLIO_STATS
        portfolio_stats = row.get("PORTFOLIO_STATS", {})

        # Debug: Log the actual data structure being processed
        log(f"Row keys for {ticker}: {list(row.keys())[:10]}...", "info")
        log(
            f"PORTFOLIO_STATS keys for {ticker}: {list(portfolio_stats.keys())[:10] if portfolio_stats else 'None'}...",
            "info",
        )
        log(
            f"Direct access for {ticker}: FAST_PERIOD={row.get('FAST_PERIOD')}, SLOW_PERIOD={row.get('SLOW_PERIOD')}, SIGNAL_PERIOD={row.get('SIGNAL_PERIOD')}",
            "info",
        )
        log(
            f"Portfolio stats access for {ticker}: FAST_PERIOD={portfolio_stats.get('FAST_PERIOD')}, SLOW_PERIOD={portfolio_stats.get('SLOW_PERIOD')}, SIGNAL_PERIOD={portfolio_stats.get('SIGNAL_PERIOD')}",
            "info",
        )

        # Try original column names first (what we actually have), then standardized/legacy names
        # Enhanced debugging to track parameter extraction step by step
        short_window_checks = [
            ("Fast Period", row.get("Fast Period")),
            ("FAST_PERIOD", row.get("FAST_PERIOD")),
            (
                "PORTFOLIO_STATS.FAST_PERIOD",
                portfolio_stats.get("FAST_PERIOD") if portfolio_stats else None,
            ),
            ("FAST_PERIOD", row.get("FAST_PERIOD")),
            (
                "PORTFOLIO_STATS.FAST_PERIOD",
                portfolio_stats.get("FAST_PERIOD") if portfolio_stats else None,
            ),
            ("Fast Period", row.get("Fast Period")),
        ]

        log(
            f"DEBUG {ticker} fast_period extraction checks: {short_window_checks}",
            "info",
        )

        fast_period = (
            row.get("Fast Period")
            or row.get("FAST_PERIOD")
            or (portfolio_stats.get("FAST_PERIOD") if portfolio_stats else None)
            or row.get("FAST_PERIOD")
            or (portfolio_stats.get("FAST_PERIOD") if portfolio_stats else None)
            or row.get("Fast Period")
        )

        slow_period = (
            row.get("Slow Period")
            or row.get("SLOW_PERIOD")
            or (portfolio_stats.get("SLOW_PERIOD") if portfolio_stats else None)
            or row.get("SLOW_PERIOD")
            or (portfolio_stats.get("SLOW_PERIOD") if portfolio_stats else None)
            or row.get("Slow Period")
        )

        signal_period = (
            row.get("Signal Period")
            or row.get("SIGNAL_PERIOD")
            or (portfolio_stats.get("SIGNAL_PERIOD") if portfolio_stats else None)
            or row.get("SIGNAL_PERIOD")
            or (portfolio_stats.get("SIGNAL_PERIOD") if portfolio_stats else None)
            or row.get("Signal Period")
        )

        log(
            f"Final extracted values for {ticker}: fast_period={fast_period}, slow_period={slow_period}, signal_period={signal_period}",
            "info",
        )

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
                            f"Signal Unconfirmed for {ticker}: {signal_unconfirmed}",
                            "info",
                        )

                        stats = portfolio.stats()
                        stats["Ticker"] = ticker
                        stats["Strategy Type"] = "MACD"
                        stats["Fast Period"] = fast_period
                        stats["Slow Period"] = slow_period
                        stats["Signal Period"] = signal_period

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
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=signal_period,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="MACD",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_period=signal_period,
                        ):
                            log(
                                f"Triggering fresh MACD analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="MACD",
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=signal_period,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="MACD",
                                    fast_period=fast_period,
                                    slow_period=slow_period,
                                    signal_period=signal_period,
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
                                        fast_period=fast_period,
                                        slow_period=slow_period,
                                        signal_period=signal_period,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="MACD",
                                            fast_period=fast_period,
                                            slow_period=slow_period,
                                            signal_period=signal_period,
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
                            stats,
                            log,
                            config,
                            current_signal,
                            exit_signal,
                            signal_unconfirmed,
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

                        # Get total open trades from portfolio stats
                        sma_portfolio_stats = sma_portfolio.stats()
                        total_open_trades = sma_portfolio_stats.get(
                            "Total Open Trades", 0
                        )

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
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=None,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_sma_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="SMA",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_period=None,
                        ):
                            log(
                                f"Triggering fresh SMA analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="SMA",
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=None,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="SMA",
                                    fast_period=fast_period,
                                    slow_period=slow_period,
                                    signal_period=None,
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
                                        fast_period=fast_period,
                                        slow_period=slow_period,
                                        signal_period=None,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="SMA",
                                            fast_period=fast_period,
                                            slow_period=slow_period,
                                            signal_period=None,
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
                            sma_stats,
                            log,
                            config,
                            current_signal,
                            exit_signal,
                            signal_unconfirmed,
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

                        # Get total open trades from portfolio stats
                        ema_portfolio_stats = ema_portfolio.stats()
                        total_open_trades = ema_portfolio_stats.get(
                            "Total Open Trades", 0
                        )

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
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=None,
                                config=config,
                                log=log,
                            )
                        elif should_trigger_fresh_analysis(
                            config,
                            has_ema_vectorbt_portfolio,
                            ticker=ticker,
                            strategy_type="EMA",
                            fast_period=fast_period,
                            slow_period=slow_period,
                            signal_period=None,
                        ):
                            log(
                                f"Triggering fresh EMA analysis for {ticker} to enable equity export",
                                "info",
                            )
                            # Dispatch fresh analysis to get VectorBT Portfolio object
                            fresh_portfolio = dispatch_fresh_analysis(
                                ticker=ticker,
                                strategy_type="EMA",
                                fast_period=fast_period,
                                slow_period=slow_period,
                                signal_period=None,
                                config=config,
                                log=log,
                            )

                            if fresh_portfolio is not None:
                                equity_data = _extract_equity_data_if_enabled(
                                    portfolio=fresh_portfolio,
                                    ticker=ticker,
                                    strategy_type="EMA",
                                    fast_period=fast_period,
                                    slow_period=slow_period,
                                    signal_period=None,
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
                                        fast_period=fast_period,
                                        slow_period=slow_period,
                                        signal_period=None,
                                    )
                                    if file_exists:
                                        file_path = get_equity_file_path(
                                            ticker=ticker,
                                            strategy_type="EMA",
                                            fast_period=fast_period,
                                            slow_period=slow_period,
                                            signal_period=None,
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
                            ema_stats,
                            log,
                            config,
                            current_signal,
                            exit_signal,
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
            fast_period = row.get("Fast_Period", 0)
            slow_period = row.get("Slow_Period", 0)
            signal_period = row.get("Signal_Period", 0)
            status = row.get("Status", "")

            # Find matching aggregated data for this strategy
            matching_aggregated = None
            for agg_entry in aggregated_portfolios:
                if (
                    agg_entry.get("Ticker") == ticker
                    and agg_entry.get("Strategy Type") == strategy_type
                    and agg_entry.get("Fast Period") == fast_period
                    and agg_entry.get("Slow Period") == slow_period
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
                individual_entry["Fast Period"] = fast_period
                individual_entry["Slow Period"] = slow_period
                individual_entry["Signal Period"] = signal_period

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
                    f"No matching aggregated data found for {ticker} {strategy_type} {fast_period}/{slow_period}",
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


def update_strategy_files(
    portfolios: List[Dict],
    portfolio_name: str,
    log: Callable[[str, str], None],
    config: Optional[Dict] | None = None,
) -> bool:
    """
    Update existing strategy files with processed portfolio data.

    This function updates strategy files in /data/raw/strategies/ directory,
    NOT creating new exports in portfolios directories.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        portfolio_name (str): Name of the portfolio file
        log (Callable): Logging function
        config (Optional[Dict]): Configuration dictionary

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        # Phase 4: Validate and log configuration before processing
        if config:
            try:
                validated_config = log_configuration_validation(config, log)
                config.update(validated_config)
                log("Configuration validation completed successfully", "info")
            except Exception as e:
                log(f"Configuration validation failed: {str(e)}", "error")
        else:
            log("No configuration provided - using default settings", "warning")

        if not portfolios:
            log("No portfolios data provided for strategy file update", "warning")
            return False

        log(
            f"📊 STRATEGY UPDATE: Updating strategy files with {len(portfolios)} portfolios",
            "info",
        )

        # DIRECTORY VALIDATION: Ensure we're NOT exporting to portfolios directories
        from pathlib import Path

        project_root = get_project_root()

        # Check that we're targeting strategies directory, not portfolios
        expected_strategies_dir = Path(project_root) / "data" / "raw" / "strategies"
        portfolios_dirs = [
            Path(project_root) / "data" / "raw" / "portfolios",
            Path(project_root) / "data" / "raw" / "portfolios_best",
            Path(project_root) / "data" / "raw" / "portfolios_filtered",
            Path(project_root) / "data" / "raw" / "portfolios_metrics",
        ]

        # Fail fast if any portfolios directory would be targeted
        for portfolio_dir in portfolios_dirs:
            if portfolio_dir.exists():
                log(
                    f"🔒 VALIDATION: Portfolios directory exists at {portfolio_dir} - ensuring no exports there",
                    "info",
                )

        # Ensure strategies directory exists
        if not expected_strategies_dir.exists():
            log(
                f"❌ VALIDATION FAILED: Strategies directory does not exist at {expected_strategies_dir}",
                "error",
            )
            return False

        log(
            f"✅ VALIDATION PASSED: Will update strategy files in {expected_strategies_dir}",
            "info",
        )

        # PHASE 1: Pre-processing validation of strategy parameters
        log(f"🔍 PHASE 1: Validating {len(portfolios)} input portfolios", "info")
        for i, portfolio in enumerate(portfolios):
            ticker = portfolio.get("Ticker", "Unknown")
            strategy_type = portfolio.get("Strategy Type", "Unknown")

            # Check for strategy parameter integrity
            fast_period = (
                portfolio.get("Fast Period")
                or portfolio.get("Fast Period")
                or portfolio.get("FAST_PERIOD")
            )
            slow_period = (
                portfolio.get("Slow Period")
                or portfolio.get("Slow Period")
                or portfolio.get("SLOW_PERIOD")
            )
            signal_period = (
                portfolio.get("Signal Period")
                or portfolio.get("Signal Period")
                or portfolio.get("SIGNAL_PERIOD")
            )

            log(
                f"📋 Portfolio {i+1}: {ticker} {strategy_type} - Fast: {fast_period}, Slow: {slow_period}, Signal: {signal_period}",
                "info",
            )

            # Fail fast on invalid strategy parameters
            if fast_period is None or slow_period is None:
                log(
                    f"❌ CRITICAL: Portfolio {i+1} ({ticker} {strategy_type}) has None parameters",
                    "error",
                )
                return False
            if fast_period <= 0 or slow_period <= 0:
                log(
                    f"❌ CRITICAL: Portfolio {i+1} ({ticker} {strategy_type}) has invalid parameters (fast={fast_period}, slow={slow_period})",
                    "error",
                )
                return False

        # Apply same data processing as export_summary_results
        log(
            f"🔄 PHASE 2: Applying column reordering to {len(portfolios)} portfolios",
            "info",
        )
        reordered_portfolios = [reorder_columns(p) for p in portfolios]
        export_config = config if config is not None else get_config({})
        export_config["TICKER"] = None

        # PHASE 2: Post-reordering validation
        log(
            f"🔍 PHASE 2: Validating {len(reordered_portfolios)} reordered portfolios",
            "info",
        )
        for i, portfolio in enumerate(reordered_portfolios):
            ticker = portfolio.get("Ticker", "Unknown")
            strategy_type = portfolio.get("Strategy Type", "Unknown")
            fast_period = portfolio.get("Fast Period")
            slow_period = portfolio.get("Slow Period")
            signal_period = portfolio.get("Signal Period")

            log(
                f"📋 Reordered Portfolio {i+1}: {ticker} {strategy_type} - Fast: {fast_period}, Slow: {slow_period}, Signal: {signal_period}",
                "info",
            )

            # Detect corruption after reordering
            if fast_period == 0 or slow_period == 0:
                log(
                    f"❌ CRITICAL: Column reordering corrupted Portfolio {i+1} ({ticker} {strategy_type}) - parameters became 0,0,0",
                    "error",
                )
                return False

        # Remove duplicates and apply filtering with enhanced logging
        try:
            # Normalize data to fix schema inference issues
            log("📊 Normalizing portfolio data to fix mixed data types", "debug")
            normalized_portfolios = normalize_portfolio_data(reordered_portfolios)

            # Create DataFrame with explicit schema to prevent type inference conflicts
            schema = get_portfolio_schema()

            # Filter schema to only include columns present in the data
            if normalized_portfolios:
                available_columns = set(normalized_portfolios[0].keys())
                filtered_schema = {
                    k: v for k, v in schema.items() if k in available_columns
                }
                log(
                    f"📊 Using explicit schema for {len(filtered_schema)} columns",
                    "debug",
                )
            else:
                filtered_schema = schema

            df = pl.DataFrame(normalized_portfolios, schema=filtered_schema)
            log(f"📊 BEFORE DEDUPLICATION: {len(df)} portfolios in DataFrame", "info")
            log(f"📊 DataFrame columns: {df.columns}", "debug")

            # Dynamic column detection for robustness
            available_columns = df.columns
            uniqueness_columns = []

            # Map standard deduplication columns to available columns
            column_mapping = {
                "Ticker": ["Ticker", "TICKER"],
                "Strategy Type": ["Strategy Type", "STRATEGY_TYPE"],
                "Fast Period": ["Fast Period", "Fast Period", "FAST_PERIOD"],
                "Slow Period": ["Slow Period", "Slow Period", "SLOW_PERIOD"],
            }

            for standard_name, possible_names in column_mapping.items():
                found_column = None
                for possible_name in possible_names:
                    if possible_name in available_columns:
                        found_column = possible_name
                        break

                if found_column:
                    uniqueness_columns.append(found_column)
                    log(
                        f"📊 Mapped '{standard_name}' to column '{found_column}'", "info"
                    )
                else:
                    log(
                        f"⚠️ WARNING: Could not find column for '{standard_name}' in {available_columns}",
                        "warning",
                    )

            if "Metric Type" in df.columns:
                uniqueness_columns.append("Metric Type")

            log(f"📊 Using uniqueness columns: {uniqueness_columns}", "info")

            # Log actual data before deduplication for debugging
            for i, row in enumerate(df.iter_rows(named=True)):
                if i < 3:  # Log first 3 rows for debugging
                    log(f"📊 Row {i+1} data: {dict(row)}", "debug")

            duplicate_count = len(df) - df.unique(subset=uniqueness_columns).height
            if duplicate_count > 0:
                log(
                    f"🔧 Found {duplicate_count} duplicate entries using columns: {uniqueness_columns}",
                    "info",
                )

                # Before removing duplicates, check if this seems wrong
                if (
                    duplicate_count >= len(df) * 0.7
                ):  # More than 70% duplicates seems suspicious
                    log(
                        f"⚠️ WARNING: Suspiciously high duplicate count ({duplicate_count}/{len(df)})",
                        "warning",
                    )

                df = df.unique(subset=uniqueness_columns, keep="first")
                log(f"📊 AFTER DEDUPLICATION: {len(df)} unique combinations", "info")

                # Log remaining data after deduplication
                for i, row in enumerate(df.iter_rows(named=True)):
                    log(f"📊 Remaining Row {i+1}: {dict(row)}", "debug")

            reordered_portfolios = df.to_dicts()
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")
            log("Attempting fallback without DataFrame operations", "info")

            # Fallback: use original data without deduplication if DataFrame operations fail
            reordered_portfolios = (
                normalized_portfolios
                if "normalized_portfolios" in locals()
                else reordered_portfolios
            )
            log(f"Using fallback data: {len(reordered_portfolios)} portfolios", "info")

        # Filter out portfolios with invalid metrics
        try:
            from app.tools.portfolio.filters import filter_invalid_metrics

            filtered_portfolios = filter_invalid_metrics(reordered_portfolios, log)
            reordered_portfolios = filtered_portfolios
            log(
                f"After filtering invalid metrics: {len(reordered_portfolios)} portfolios remain"
            )
        except Exception as e:
            log(f"Error during invalid metrics filtering: {str(e)}", "warning")
            log("Continuing with unfiltered portfolios due to filtering error", "info")

        if not reordered_portfolios:
            log("No portfolios remain after filtering", "warning")
            return False

        # Import export_csv for direct strategy file updates
        from pathlib import Path

        from app.tools.export_csv import export_csv

        # Update strategy files directly in /data/raw/strategies/ directory
        strategies_dir = Path(export_config["BASE_DIR"]) / "data" / "raw" / "strategies"
        strategies_dir.mkdir(parents=True, exist_ok=True)

        # Clean data for CSV export - remove non-serializable columns
        csv_ready_portfolios = []
        for portfolio in reordered_portfolios:
            # Create a copy without non-serializable columns
            clean_portfolio = {}
            for key, value in portfolio.items():
                # Skip non-serializable data like EquityData objects
                if key.startswith("_") or key in ["_equity_data"]:
                    continue
                # Convert complex objects to strings for CSV compatibility
                if value is not None and not isinstance(value, (str, int, float, bool)):
                    try:
                        clean_portfolio[key] = str(value)
                    except:
                        log(
                            f"Skipping non-serializable field {key} for CSV export",
                            "debug",
                        )
                        continue
                else:
                    clean_portfolio[key] = value
            csv_ready_portfolios.append(clean_portfolio)

        # Convert to DataFrame for export with schema normalization
        normalized_csv_portfolios = normalize_portfolio_data(csv_ready_portfolios)

        # Use explicit schema for consistent DataFrame creation
        schema = get_portfolio_schema()
        if normalized_csv_portfolios:
            available_columns = set(normalized_csv_portfolios[0].keys())
            filtered_schema = {
                k: v for k, v in schema.items() if k in available_columns
            }
        else:
            filtered_schema = schema

        try:
            df = pl.DataFrame(normalized_csv_portfolios, schema=filtered_schema)
            log(
                f"Created DataFrame for CSV export with {len(normalized_csv_portfolios)} portfolios",
                "debug",
            )
        except Exception as e:
            log(
                f"Error creating DataFrame with schema, falling back to auto-inference: {str(e)}",
                "warning",
            )
            df = pl.DataFrame(normalized_csv_portfolios)

        # Sort DataFrame according to configuration before CSV export
        if config:
            sort_by = config.get("SORT_BY", "Score")
            sort_asc = config.get("SORT_ASC", False)

            # Ensure sort column exists - if sorting by Score but column doesn't exist, use Total Return [%] as fallback
            if sort_by == "Score" and "Score" not in df.columns:
                if "Total Return [%]" in df.columns:
                    try:
                        # Create Score column from Total Return [%]
                        df = df.with_columns(
                            pl.col("Total Return [%]").cast(pl.Float64).alias("Score")
                        )
                        log(
                            f"Created Score column from Total Return [%] for sorting",
                            "info",
                        )
                    except Exception:
                        # Use the original Total Return [%] column
                        sort_by = "Total Return [%]"
                        log(
                            f"Using Total Return [%] for sorting instead of Score",
                            "info",
                        )
                else:
                    # Fall back to first available numeric column
                    numeric_cols = [
                        col
                        for col in df.columns
                        if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]
                    ]
                    sort_by = numeric_cols[0] if numeric_cols else df.columns[0]
                    log(f"Falling back to {sort_by} for sorting", "info")

            # Apply sorting if column exists
            if sort_by in df.columns:
                try:
                    df = df.sort(sort_by, descending=not sort_asc)
                    log(
                        f"Sorted CSV export by {sort_by} ({'ascending' if sort_asc else 'descending'})",
                        "info",
                    )
                except Exception as e:
                    log(f"Error sorting by {sort_by}: {str(e)}", "warning")
            else:
                log(
                    f"Warning: Sort column '{sort_by}' not found in DataFrame columns: {df.columns}",
                    "warning",
                )
        else:
            log("No config provided - exporting without sorting", "warning")

        # Export directly to strategies directory using the original portfolio filename
        output_path = strategies_dir / portfolio_name
        log(f"📊 UPDATING STRATEGY FILE: {output_path}", "info")

        # Write CSV directly to strategy file location
        try:
            df.write_csv(str(output_path), separator=",")
            success = True
            log(f"✅ STRATEGY FILE UPDATED: {output_path}", "info")
        except Exception as e:
            log(f"❌ FAILED TO UPDATE STRATEGY FILE: {str(e)}", "error")
            success = False

        if not success:
            log("Failed to update strategy files", "error")
            return False

        # POST-EXECUTION VALIDATION: Verify no files were created in portfolios directories
        portfolios_files_created = []
        for portfolio_dir in portfolios_dirs:
            if portfolio_dir.exists():
                # Check for any recently created files in portfolios directories
                import time

                current_time = time.time()
                recent_threshold = 60  # Files created in last 60 seconds

                for file_path in portfolio_dir.rglob("*.csv"):
                    if current_time - file_path.stat().st_mtime < recent_threshold:
                        portfolios_files_created.append(str(file_path))

        if portfolios_files_created:
            log(
                f"❌ VALIDATION FAILED: Files were created in portfolios directories: {portfolios_files_created}",
                "error",
            )
            log("❌ This indicates the export routing is still broken", "error")
            return False

        log(
            "✅ POST-EXECUTION VALIDATION PASSED: No files created in portfolios directories",
            "info",
        )
        log("Strategy files updated successfully", "info")
        return True

    except Exception as e:
        log(f"Error updating strategy files: {str(e)}", "error")
        return False


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
            key = f"{p.get('Ticker', 'N/A')},{p.get('Strategy Type', 'N/A')},{p.get('Fast Period', 'N/A')},{p.get('Slow Period', 'N/A')}"
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
        # SAFETY GUARD: Validate portfolios have meaningful data before export
        valid_portfolios = []
        for i, portfolio in enumerate(portfolios):
            # Check if portfolio has valid window parameters
            # Look for values in the correct columns where they're actually stored
            fast_period = (
                portfolio.get("Fast Period")
                or portfolio.get("Fast Period")
                or portfolio.get("FAST_PERIOD")
                or 0
            )
            slow_period = (
                portfolio.get("Slow Period")
                or portfolio.get("Slow Period")
                or portfolio.get("SLOW_PERIOD")
                or 0
            )

            # Debug: Show all available keys and their values for the first few portfolios
            if i < 3:
                ticker = portfolio.get("Ticker", "Unknown")
                strategy_type = portfolio.get("Strategy Type", "Unknown")
                log(
                    f"DEBUG MAIN PORTFOLIO {i+1} ({ticker} {strategy_type}): Keys available: {list(portfolio.keys())[:15]}...",
                    "info",
                )
                log(
                    f"DEBUG MAIN PORTFOLIO {i+1}: Fast Period={portfolio.get('Fast Period')}, FAST_PERIOD={portfolio.get('FAST_PERIOD')}, Fast Period={portfolio.get('Fast Period')}, FAST_PERIOD={portfolio.get('FAST_PERIOD')}",
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
        export_config = config if config is not None else get_config({})
        export_config["TICKER"] = None

        # Remove duplicates based on Ticker, Use SMA, Fast Period, Slow Period
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
                        "Fast Period",
                        "Slow Period",
                        "Metric Type",
                    ).to_dicts()
                    log(f"📊 CBRE METRICS BEFORE: {cbre_metrics}", "info")

            # Phase 2 Fix: Include Metric Type in uniqueness check to preserve all metric types
            # Use correct column names: Fast Period and Slow Period (not Short/Slow Period)
            uniqueness_columns = [
                "Ticker",
                "Strategy Type",
                "Fast Period",
                "Slow Period",
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
                            "Fast Period",
                            "Slow Period",
                            "Metric Type",
                        ).to_dicts()
                        log(f"📊 CBRE METRICS AFTER: {cbre_metrics_after}", "info")

                        # Phase 2 Validation: Check if multiple metric types are preserved for same configuration
                        cbre_configs = {}
                        for row in cbre_metrics_after:
                            config_key = f"{row['Ticker']},{row['Strategy Type']},{row['Fast Period']},{row['Slow Period']}"
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
                        "Short": p.get("Fast Period"),
                        "Long": p.get("Slow Period"),
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

        # Export to /data/raw/portfolios to avoid overwriting input strategy files
        # Input strategy definitions remain safe in /data/raw/strategies/
        _, success = export_portfolios(
            spds_compatible_portfolios,
            export_config,
            "portfolios",
            portfolio_name,
            log,
            feature_dir="portfolios",
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
