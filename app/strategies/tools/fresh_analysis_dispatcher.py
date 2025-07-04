"""
Fresh Analysis Dispatcher

This module provides automatic fresh strategy analysis when equity export is enabled
but no VectorBT Portfolio objects exist. It dispatches to the appropriate strategy
analysis function based on strategy type and returns Portfolio objects for equity extraction.
"""

from typing import Any, Callable, Dict, Optional, Tuple


def dispatch_fresh_analysis(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
) -> Optional[Any]:
    """
    Dispatch fresh strategy analysis to generate VectorBT Portfolio objects.

    This function automatically runs live strategy analysis when equity export
    is enabled but no Portfolio objects exist (e.g., when processing pre-computed
    CSV results). It reuses existing strategy analysis functions.

    Args:
        ticker: Ticker symbol to analyze
        strategy_type: Strategy type (SMA, EMA, MACD)
        short_window: Short window parameter
        long_window: Long window parameter
        signal_window: Signal window parameter (for MACD)
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
                ticker, strategy_type, short_window, long_window, config, log
            )
        elif strategy_type == "MACD":
            return _dispatch_macd_analysis(
                ticker, short_window, long_window, signal_window, config, log
            )
        else:
            log(
                f"Unsupported strategy type for fresh analysis: {strategy_type}",
                "warning",
            )
            return None

    except Exception as e:
        log(
            f"Failed to execute fresh {strategy_type} analysis for {ticker}: {str(e)}",
            "error",
        )
        return None


def _dispatch_ma_analysis(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    config: Dict[str, Any],
    log: Callable[[str, str], None],
) -> Optional[Any]:
    """Dispatch fresh MA (SMA/EMA) analysis."""
    try:
        # Import here to avoid circular imports
        from app.strategies.ma_cross.tools.strategy_execution import (
            execute_single_strategy,
        )
        from app.tools.backtest_strategy import backtest_strategy
        from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
        from app.tools.get_data import get_data

        # Create fresh analysis config
        fresh_config = config.copy()
        fresh_config.update(
            {
                "STRATEGY_TYPE": strategy_type,
                "SHORT_WINDOW": short_window,
                "LONG_WINDOW": long_window,
                "TICKER": ticker,
                "REFRESH": True,  # Force fresh data
                "USE_CURRENT": True,
            }
        )

        log(
            f"Executing fresh {strategy_type} analysis for {ticker} ({short_window}/{long_window})",
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
            data, short_window, long_window, fresh_config, log, strategy_type
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
        log(f"Error in MA fresh analysis for {ticker}: {str(e)}", "error")
        return None


def _dispatch_macd_analysis(
    ticker: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
) -> Optional[Any]:
    """Dispatch fresh MACD analysis."""
    try:
        # Import here to avoid circular imports
        from app.strategies.tools.process_strategy_portfolios import (
            process_macd_strategy,
        )

        if signal_window is None:
            log(
                f"Cannot run fresh MACD analysis for {ticker}: missing signal window",
                "error",
            )
            return None

        # Create fresh analysis config
        fresh_config = config.copy()
        fresh_config.update({"REFRESH": True, "USE_CURRENT": True})  # Force fresh data

        log(
            f"Executing fresh MACD analysis for {ticker} ({short_window}/{long_window}/{signal_window})",
            "info",
        )

        # Run fresh MACD analysis
        result = process_macd_strategy(
            ticker=ticker,
            short_window=short_window,
            long_window=long_window,
            signal_window=signal_window,
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
        log(f"Error in MACD fresh analysis for {ticker}: {str(e)}", "error")
        return None


def should_trigger_fresh_analysis(
    config: Dict[str, Any],
    has_vectorbt_portfolio: bool,
    ticker: str = None,
    strategy_type: str = None,
    short_window: int = None,
    long_window: int = None,
    signal_window: Optional[int] = None,
) -> bool:
    """
    Determine if fresh analysis should be triggered for equity export.

    Args:
        config: Configuration dictionary
        has_vectorbt_portfolio: Whether VectorBT Portfolio objects exist
        ticker: Ticker symbol (for file existence checking)
        strategy_type: Strategy type (for file existence checking)
        short_window: Short window (for file existence checking)
        long_window: Long window (for file existence checking)
        signal_window: Signal window (for file existence checking)

    Returns:
        True if fresh analysis should be triggered, False otherwise
    """
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
        param is not None
        for param in [ticker, strategy_type, short_window, long_window]
    ):
        try:
            from app.tools.equity_export import equity_file_exists, get_equity_file_path

            file_exists = equity_file_exists(
                ticker=ticker,
                strategy_type=strategy_type,
                short_window=short_window,
                long_window=long_window,
                signal_window=signal_window,
            )

            # If file exists, skip fresh analysis
            if file_exists:
                file_path = get_equity_file_path(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    short_window=short_window,
                    long_window=long_window,
                    signal_window=signal_window,
                )
                # Note: This log will be added by the calling function for better context
                return False

        except Exception:
            # If file check fails, default to triggering fresh analysis
            pass

    # Default: trigger fresh analysis when equity export is enabled but no Portfolio exists
    return True
