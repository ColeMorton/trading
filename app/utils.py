"""
Core Utility Functions Module

This module provides core utility functions for data processing,
visualization, and analysis.
"""

import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import polars as pl
import vectorbt as vbt


def calculate_metrics(
    trades: List[Tuple[float, float]], short: bool
) -> Tuple[float, float, float]:
    """Calculate performance metrics from a list of trades.

    Args:
        trades: List of (entry_price, exit_price) tuples
        short: Whether trades are short positions

    Returns:
        Tuple of (total_return_pct, win_rate_pct, expectancy)
    """
    if not trades:
        return 0, 0, 0

    returns = [
        (exit_price / entry_price - 1) * (-1 if short else 1)
        for entry_price, exit_price in trades
    ]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(returns)

    average_win = (
        np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    )
    average_loss = (
        np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    )
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))

    return total_return * 100, win_rate * 100, expectancy


def find_prominent_peaks(
    x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10
) -> np.ndarray:
    """Find prominent peaks in a dataset.

    Args:
        x: X-axis values
        y: Y-axis values
        prominence: Required prominence of peaks
        distance: Required distance between peaks

    Returns:
        Array of peak indices
    """
    from scipy.signal import find_peaks

    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks


def add_peak_labels(
    ax: Any, x: np.ndarray, y: np.ndarray, peaks: np.ndarray, fmt: str = ".2f"
) -> None:
    """Add labels to peaks in a plot.

    Args:
        ax: Matplotlib axis object
        x: X-axis values
        y: Y-axis values
        peaks: Array of peak indices
        fmt: Number format string
    """
    for peak in peaks:
        ax.annotate(
            f"({x[peak]:.2f}, {y[peak]:{fmt}})",
            (x[peak], y[peak]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.5", fc="cyan", alpha=0.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )


def backtest_strategy(
    data: pl.DataFrame, config: Dict[str, Any], log: Callable[[str, str], None]
) -> Optional[vbt.Portfolio]:
    """Backtest the MA cross strategy.

    Args:
        data: Price data DataFrame
        config: Configuration dictionary

    Returns:
        Portfolio object or None if backtest fails

    Raises:
        Exception: If backtest fails
    """
    try:
        freq = "h" if config.get("USE_HOURLY", False) else "D"

        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()

        if config.get("SHORT", False):
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd["Close"],
                short_entries=data_pd["Signal"] == 1,
                short_exits=data_pd["Signal"] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq,
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd["Close"],
                entries=data_pd["Signal"] == 1,
                exits=data_pd["Signal"] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq,
            )

        log("Backtest completed successfully", "info")
        return portfolio

    except Exception as e:
        log(f"Backtest failed: {e}", "error")
        raise


def get_filename(type: str, config: Dict[str, Any], path: str = "") -> str:
    """Generate filename based on configuration.

    Args:
        type: File type/extension
        config: Configuration dictionary
        path: Optional path to determine if datetime should be included

    Returns:
        str: Generated filename
    """
    # Handle TICKER which can be str or List[str]
    ticker_prefix = ""
    if config.get("TICKER", False):
        if isinstance(config["TICKER"], str):
            ticker_prefix = f"{config['TICKER']}_"
        elif isinstance(config["TICKER"], list) and len(config["TICKER"]) == 1:
            ticker_prefix = f"{config['TICKER'][0]}_"

    # Only include datetime if path contains portfolios_best
    include_datetime = (
        path and "portfolios_best" in path and config.get("SHOW_LAST", False)
    )

    components = [
        ticker_prefix,
        "H" if config.get("USE_HOURLY", False) else "D",
        "_SMA" if config.get("USE_SMA", False) else "_EMA",
        "_GBM" if config.get("USE_GBM", False) else "",
        f"_{datetime.now().strftime('%Y%m%d')}" if include_datetime else "",
    ]

    return f"{''.join(components)}.{type}"


def get_path(
    type: str, feature1: str, config: Dict[str, Any], feature2: str = ""
) -> str:
    """Generate path based on configuration.

    Args:
        type: Directory type (e.g., 'csv', 'png')
        feature1: First feature directory
        config: Configuration dictionary
        feature2: Secondary feature directory (optional)

    Returns:
        str: Generated path
    """
    path_components = [config["BASE_DIR"], type, feature1]

    if feature2:
        path_components.append(feature2)

    # Only add date subdirectory for portfolios_best
    path = os.path.join(*path_components)
    if "portfolios_best" in path and config.get("USE_CURRENT", False):
        today = datetime.now().strftime("%Y%m%d")
        path_components.append(today)

    return os.path.join(*path_components)
