"""Portfolio status filtering utilities.

This module provides functions for determining and filtering portfolio status
based on signals and open trades.
"""

from typing import Any, Dict, List


def determine_portfolio_status(portfolio: Dict[str, Any]) -> str:
    """Determine portfolio status based on signals and open trades.

    Args:
        portfolio: Portfolio dictionary containing signal and trade information

    Returns:
        Status string: "Entry", "Exit", "Active", or "Inactive"
    """
    signal_entry = str(portfolio.get("Signal Entry", "")).lower() == "true"
    signal_exit = str(portfolio.get("Signal Exit", "")).lower() == "true"
    total_open_trades = portfolio.get("Total Open Trades")

    if signal_entry:
        return "Entry"
    elif signal_exit:
        return "Exit"
    elif total_open_trades == 1 or (
        isinstance(total_open_trades, str) and total_open_trades == "1"
    ):
        return "Active"
    else:
        return "Inactive"


def filter_entry_strategies(portfolios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter portfolios to only Entry status strategies.

    Args:
        portfolios: List of portfolio dictionaries

    Returns:
        Filtered list containing only Entry status portfolios
    """
    return [p for p in portfolios if determine_portfolio_status(p) == "Entry"]

