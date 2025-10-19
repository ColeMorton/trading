"""
Fresh Analysis Dispatcher

This module provides automatic fresh strategy analysis when equity export is enabled
but no VectorBT Portfolio objects exist. It dispatches to the appropriate strategy
analysis function based on strategy type and returns Portfolio objects for equity extraction.
"""

from collections.abc import Callable
from typing import Any


def dispatch_fresh_analysis(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: int | None,
    config: dict[str, Any],
    log: Callable[[str, str], None],
) -> Any | None:
    """
    Dispatch fresh strategy analysis to generate VectorBT Portfolio objects.

    This function automatically runs live strategy analysis when equity export
    is enabled but no Portfolio objects exist (e.g., when processing pre-computed
    CSV results). It reuses existing strategy analysis functions.

    Args:
        ticker: Ticker symbol to analyze
        strategy_type: Strategy type (SMA, EMA, MACD)
        fast_period: Fast period parameter
        slow_period: Slow period parameter
        signal_period: Signal period parameter (for MACD)
        config: Configuration dictionary
        log: Logging function

    Returns:
        VectorBT Portfolio object if analysis succeeds, None otherwise
    """
    log(
        f"Triggering fresh {strategy_type} analysis for {ticker} to enable equity export",
        "info",
    )

    try:
        if strategy_type in ["SMA", "EMA"]:
            return _dispatch_ma_analysis(
                ticker, strategy_type, fast_period, slow_period, config, log
            )
        if strategy_type == "MACD":
            return _dispatch_macd_analysis(
                ticker, fast_period, slow_period, signal_period, config, log
            )
        log(
            f"Unsupported strategy type for fresh analysis: {strategy_type}",
            "warning",
        )
        return None

    except Exception as e:
        log(
            f"Failed to execute fresh {strategy_type} analysis for {ticker}: {e!s}",
            "error",
        )
        return None


def _dispatch_ma_analysis(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    config: dict[str, Any],
    log: Callable[[str, str], None],
) -> Any | None:
    """Dispatch fresh MA (SMA/EMA) analysis."""
    try:
        # Import here to avoid circular imports
        from app.tools.backtest_strategy import backtest_strategy
        from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
        from app.tools.get_data import get_data

        # Create fresh analysis config
        fresh_config = config.copy()
        fresh_config.update(
            {
                "STRATEGY_TYPE": strategy_type,
                "FAST_PERIOD": fast_period,
                "SLOW_PERIOD": slow_period,
                "TICKER": ticker,
                "REFRESH": True,  # Force fresh data
                "USE_CURRENT": True,
            }
        )

        log(
            f"Executing fresh {strategy_type} analysis for {ticker} ({fast_period}/{slow_period})",
            "info",
        )

        # Get fresh price data
        data_result = get_data(ticker, fresh_config, log)
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result
            fresh_config["TICKER"] = synthetic_ticker
        else:
            data = data_result

        if data is None:
            log(f"Failed to get price data for fresh analysis: {ticker}", "error")
            return None

        # Calculate signals
        data = calculate_ma_and_signals(
            data, fast_period, slow_period, fresh_config, log, strategy_type
        )

        if data is None:
            log(f"Failed to calculate signals for fresh analysis: {ticker}", "error")
            return None

        # Run backtest to get Portfolio object
        portfolio = backtest_strategy(data, fresh_config, log)

        if portfolio is not None:
            log(
                f"Successfully generated VectorBT Portfolio for {ticker} {strategy_type}",
                "info",
            )

        return portfolio

    except Exception as e:
        log(f"Error in MA fresh analysis for {ticker}: {e!s}", "error")
        return None


def _dispatch_macd_analysis(
    ticker: str,
    fast_period: int,
    slow_period: int,
    signal_period: int | None,
    config: dict[str, Any],
    log: Callable[[str, str], None],
) -> Any | None:
    """Dispatch fresh MACD analysis."""
    try:
        # Import here to avoid circular imports
        from app.strategies.tools.process_strategy_portfolios import (
            process_macd_strategy,
        )

        if signal_period is None:
            log(
                f"Cannot run fresh MACD analysis for {ticker}: missing signal period",
                "error",
            )
            return None

        # Create fresh analysis config
        fresh_config = config.copy()
        fresh_config.update({"REFRESH": True, "USE_CURRENT": True})  # Force fresh data

        log(
            f"Executing fresh MACD analysis for {ticker} ({fast_period}/{slow_period}/{signal_period})",
            "info",
        )

        # Run fresh MACD analysis
        result = process_macd_strategy(
            ticker=ticker,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            config=fresh_config,
            log=log,
        )

        if result:
            portfolio, result_config, signal_data = result
            if portfolio is not None:
                log(
                    f"Successfully generated VectorBT Portfolio for {ticker} MACD",
                    "info",
                )
                return portfolio

        return None

    except Exception as e:
        log(f"Error in MACD fresh analysis for {ticker}: {e!s}", "error")
        return None


def should_trigger_fresh_analysis(
    config: dict[str, Any],
    has_vectorbt_portfolio: bool,
    ticker: str | None = None,
    strategy_type: str | None = None,
    fast_period: int | None = None,
    slow_period: int | None = None,
    signal_period: int | None = None,
) -> bool:
    """
    Determine if fresh analysis should be triggered for equity export.

    Args:
        config: Configuration dictionary
        has_vectorbt_portfolio: Whether VectorBT Portfolio objects exist
        ticker: Ticker symbol (for file existence checking)
        strategy_type: Strategy type (for file existence checking)
        fast_period: Fast period (for file existence checking)
        slow_period: Slow period (for file existence checking)
        signal_period: Signal period (for file existence checking)

    Returns:
        True if fresh analysis should be triggered, False otherwise
    """
    # CRITICAL: Prevent batch analysis during portfolio update operations
    # If we're in a portfolio update context, disable fresh analysis to prevent
    # triggering comprehensive MACD analysis across hundreds of tickers
    if config.get("_PORTFOLIO_UPDATE_MODE", False):
        # Log to help track when this protection is activated
        if ticker and strategy_type:
            # Use a simple print since we don't have access to log function here
            print(
                f"[SAFEGUARD] Blocked fresh analysis for {ticker} {strategy_type} during portfolio update"
            )
        return False

    # Check if equity export is enabled
    if not config.get("EQUITY_DATA", {}).get("EXPORT", False):
        return False

    # Check if we already have Portfolio objects
    if has_vectorbt_portfolio:
        return False

    # Get force fresh analysis setting
    force_fresh = config.get("EQUITY_DATA", {}).get("FORCE_FRESH_ANALYSIS", True)

    # If FORCE_FRESH_ANALYSIS=True, always trigger fresh analysis
    if force_fresh:
        return True

    # If FORCE_FRESH_ANALYSIS=False, check if equity file already exists
    if all(
        param is not None for param in [ticker, strategy_type, fast_period, slow_period]
    ):
        try:
            from app.tools.equity_export import equity_file_exists, get_equity_file_path

            file_exists = equity_file_exists(
                ticker=ticker,
                strategy_type=strategy_type,
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period,
            )

            # If file exists, skip fresh analysis
            if file_exists:
                get_equity_file_path(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                )
                # Note: This log will be added by the calling function for better context
                return False

        except Exception:
            # If file check fails, default to triggering fresh analysis
            pass

    # Default: trigger fresh analysis when equity export is enabled but no Portfolio exists
    return True
