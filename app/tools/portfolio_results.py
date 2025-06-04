"""Portfolio result processing utilities.

This module provides utilities for processing and displaying portfolio results.
"""

from typing import Any, Dict, List, Optional


def sort_portfolios(
    portfolios: List[Dict[str, Any]], sort_by: str = "Score", ascending: bool = False
) -> List[Dict[str, Any]]:
    """Sort portfolios by a specified field.

    Args:
        portfolios: List of portfolio dictionaries
        sort_by: Field to sort by
        ascending: Whether to sort in ascending order

    Returns:
        Sorted list of portfolio dictionaries
    """
    if not portfolios:
        return []

    return sorted(portfolios, key=lambda x: x.get(sort_by, 0), reverse=not ascending)


def filter_open_trades(
    portfolios: List[Dict[str, Any]], log_func=None
) -> List[Dict[str, Any]]:
    """Filter portfolios to only include open trades.

    Args:
        portfolios: List of portfolio dictionaries
        log_func: Optional logging function

    Returns:
        Filtered list of portfolio dictionaries
    """
    if not portfolios:
        return []

    # List strategies where Total Open Trades = 1 AND Signal Entry = false (to
    # avoid duplicates)
    open_trades = [
        p
        for p in portfolios
        if (
            p.get("Total Open Trades") == 1
            or (
                isinstance(p.get("Total Open Trades"), str)
                and p.get("Total Open Trades") == "1"
            )
        )
        and str(p.get("Signal Entry", "")).lower() != "true"
    ]

    # Sort open trades by Score
    open_trades = sort_portfolios(open_trades, "Score", False)

    if log_func:
        if open_trades:
            log_func("\n=== Open Trades ===")
            log_func(
                "Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score"
            )
            for p in open_trades:
                ticker = p.get("Ticker", "Unknown")
                strategy_type = p.get("Strategy Type", "Unknown")
                short_window = p.get("Short Window", "N/A")
                long_window = p.get("Long Window", "N/A")
                signal_window = p.get("Signal Window", "N/A")
                score = p.get("Score", 0)
                log_func(
                    f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}"
                )
        else:
            log_func("\n=== No Open Trades found ===")

    return open_trades


def filter_signal_entries(
    portfolios: List[Dict[str, Any]],
    open_trades: Optional[List[Dict[str, Any]]] = None,
    log_func=None,
) -> List[Dict[str, Any]]:
    """Filter portfolios to only include signal entries.

    Args:
        portfolios: List of portfolio dictionaries
        open_trades: Optional list of open trades for counting
        log_func: Optional logging function

    Returns:
        Filtered list of portfolio dictionaries
    """
    if not portfolios:
        return []

    # List strategies where Signal Entry = true
    signal_entries = [
        p for p in portfolios if str(p.get("Signal Entry", "")).lower() == "true"
    ]

    # Count strategies per ticker if open_trades is provided
    if open_trades:
        ticker_counts: Dict[str, int] = {}
        for p in open_trades:
            ticker = p.get("Ticker", "Unknown")
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        # Add the count to each strategy
        for p in signal_entries:
            ticker = p.get("Ticker", "Unknown")
            p["open_trade_count"] = ticker_counts.get(ticker, 0)

    # Sort signal entry strategies by Score
    signal_entries = sort_portfolios(signal_entries, "Score", False)

    if log_func:
        if signal_entries:
            log_func("\n=== Signal Entries ===")
            log_func(
                "Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score, Total Open Trades"
            )
            for p in signal_entries:
                ticker = p.get("Ticker", "Unknown")
                strategy_type = p.get("Strategy Type", "Unknown")
                short_window = p.get("Short Window", "N/A")
                long_window = p.get("Long Window", "N/A")
                signal_window = p.get("Signal Window", "N/A")
                score = p.get("Score", 0)
                open_trade_count = p.get("open_trade_count", 0)
                log_func(
                    f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}, {open_trade_count}"
                )
        else:
            log_func("\n=== No Signal Entries found ===")

    return signal_entries


def calculate_breadth_metrics(
    portfolios: List[Dict[str, Any]],
    open_trades: Optional[List[Dict[str, Any]]] = None,
    signal_entries: Optional[List[Dict[str, Any]]] = None,
    log_func=None,
) -> Dict[str, float]:
    """Calculate breadth metrics for a set of portfolios.

    Args:
        portfolios: List of portfolio dictionaries
        open_trades: Optional list of open trades
        signal_entries: Optional list of signal entries
        log_func: Optional logging function

    Returns:
        Dictionary of breadth metrics
    """
    if not portfolios:
        return {}

    # Get total number of strategies
    total_strategies = len(portfolios)

    # Count open trades
    total_open_trades = (
        len(open_trades)
        if open_trades is not None
        else len(
            [
                p
                for p in portfolios
                if (
                    p.get("Total Open Trades") == 1
                    or (
                        isinstance(p.get("Total Open Trades"), str)
                        and p.get("Total Open Trades") == "1"
                    )
                )
                and str(p.get("Signal Entry", "")).lower() != "true"
            ]
        )
    )

    # Count signal entries
    total_signal_entries = (
        len(signal_entries)
        if signal_entries is not None
        else len(
            [p for p in portfolios if str(p.get("Signal Entry", "")).lower() == "true"]
        )
    )

    # Count signal exits
    signal_exit_strategies = [
        p for p in portfolios if str(p.get("Signal Exit", "")).lower() == "true"
    ]
    total_signal_exits = len(signal_exit_strategies)

    # Calculate breadth ratio (open trades to total strategies)
    breadth_ratio = total_open_trades / total_strategies if total_strategies > 0 else 0

    # Calculate signal entry ratio
    signal_entry_ratio = (
        total_signal_entries / total_strategies if total_strategies > 0 else 0
    )

    # Calculate signal exit ratio
    signal_exit_ratio = (
        total_signal_exits / total_strategies if total_strategies > 0 else 0
    )

    # Calculate breadth momentum (signal entry ratio / signal exit ratio)
    breadth_momentum = (
        signal_entry_ratio / signal_exit_ratio
        if signal_exit_ratio > 0
        else float("inf")
    )

    metrics = {"total_strategies": total_strategies,
        "total_open_trades": total_open_trades,
        "total_signal_entries": total_signal_entries,
        "total_signal_exits": total_signal_exits,
        "breadth_ratio": breadth_ratio,
        "signal_entry_ratio": signal_entry_ratio,
        "signal_exit_ratio": signal_exit_ratio,
        "breadth_momentum": breadth_momentum,
    }

    if log_func:
        log_func("\n=== Breadth Metrics ===")
        log_func(f"Total Strategies: {total_strategies}")
        log_func(f"Total Open Trades: {total_open_trades}")
        log_func(f"Total Signal Entries: {total_signal_entries}")
        log_func(f"Total Signal Exits: {total_signal_exits}")
        log_func(f"Breadth Ratio: {breadth_ratio:.4f} (Open Trades / Total Strategies)")
        log_func(
            f"Signal Entry Ratio: {signal_entry_ratio:.4f} (Signal Entries / Total Strategies)"
        )
        log_func(
            f"Signal Exit Ratio: {signal_exit_ratio:.4f} (Signal Exits / Total Strategies)"
        )
        log_func(
            f"Breadth Momentum: {breadth_momentum:.4f} (Signal Entry Ratio / Signal Exit Ratio)"
        )

    return metrics
