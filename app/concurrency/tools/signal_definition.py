"""
Signal Definition Module.

This module provides different methods for defining and extracting signals
from position data, allowing for consistent signal definition across the system.

Enhanced in Phase 2 to provide standardized signal counting and validation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl


class SignalDefinitionMode(Enum):
    """Enumeration of signal definition modes."""

    POSITION_CHANGE = "position_change"  # Signal on position changes (0→1, 1→0)
    COMPLETE_TRADE = (
        "complete_trade"  # Signal represents complete trades (entry to exit)
    )
    ENTRY_ONLY = "entry_only"  # Signal only on entries (0→1)
    EXIT_ONLY = "exit_only"  # Signal only on exits (1→0)


def extract_signals(
    df: pl.DataFrame,
    mode: SignalDefinitionMode = SignalDefinitionMode.POSITION_CHANGE,
    position_column: str = "Position",
    log: Optional[Callable[[str, str], None]] = None,
) -> pl.DataFrame:
    """Extract signals from position data using the specified mode.

    Args:
        df: DataFrame with position data
        mode: Signal definition mode
        position_column: Name of the position column
        log: Optional logging function

    Returns:
        pl.DataFrame: DataFrame with Date and signal columns
    """
    if position_column not in df.columns:
        if log:
            log(f"Position column '{position_column}' not found in DataFrame", "error")
        return pl.DataFrame({"Date": [], "signal": []})

    # Ensure Date column exists
    if "Date" not in df.columns:
        if log:
            log("Date column not found in DataFrame", "error")
        return pl.DataFrame({"Date": [], "signal": []})

    # Extract signals based on mode
    if mode == SignalDefinitionMode.POSITION_CHANGE:
        # Signal on any position change (standard method)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("signal")
        )

    elif mode == SignalDefinitionMode.COMPLETE_TRADE:
        # Signal represents complete trades (entry to exit)
        # This requires post-processing to match entries with exits
        position_changes = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("change")
        )

        # Extract entries and exits
        entries = position_changes.filter(pl.col("change") > 0)
        exits = position_changes.filter(pl.col("change") < 0)

        # Create trade signals (each trade has entry and exit dates)
        # For compatibility with existing code, we'll still use the position change format
        # but ensure the metadata includes trade information
        signals_df = position_changes.with_columns(
            pl.col("change").alias("signal")
        ).drop("change")

        # Add trade metadata if logging is enabled
        if log:
            log(
                f"Extracted {len(entries)} entries and {len(exits)} exits for complete trades",
                "info",
            )

    elif mode == SignalDefinitionMode.ENTRY_ONLY:
        # Signal only on entries (0→1)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.when(pl.col(position_column).diff() > 0)
            .then(pl.col(position_column).diff())
            .otherwise(0)
            .alias("signal")
        )

    elif mode == SignalDefinitionMode.EXIT_ONLY:
        # Signal only on exits (1→0)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.when(pl.col(position_column).diff() < 0)
            .then(pl.col(position_column).diff())
            .otherwise(0)
            .alias("signal")
        )

    else:
        # Default to position change if mode is invalid
        if log:
            log(
                f"Invalid signal definition mode: {mode}. Using position_change instead.",
                "warning",
            )
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("signal")
        )

    return signals_df


def get_signal_definition_mode(config: Dict[str, Any]) -> SignalDefinitionMode:
    """Get the signal definition mode from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        SignalDefinitionMode: Signal definition mode
    """
    mode_str = config.get("SIGNAL_DEFINITION_MODE", "position_change")

    try:
        return SignalDefinitionMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        return SignalDefinitionMode.POSITION_CHANGE


def align_signal_definitions(
    backtest_signals: np.ndarray,
    implementation_signals: np.ndarray,
    dates: np.ndarray,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, np.ndarray]:
    """Align signal definitions between backtest and implementation.

    This function helps reconcile differences between backtest and implementation
    signal definitions, making it easier to compare performance.

    Args:
        backtest_signals: Signals from backtest
        implementation_signals: Signals from implementation
        dates: Array of dates corresponding to signals
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary with aligned signals
    """
    if len(backtest_signals) != len(implementation_signals) or len(
        backtest_signals
    ) != len(dates):
        if log:
            log("Signal arrays have different lengths and cannot be aligned", "error")
        return {
            "backtest_signals": backtest_signals,
            "implementation_signals": implementation_signals,
            "aligned": False,
        }

    # Convert implementation signals to match backtest format
    # This is a simplified approach - in practice, more sophisticated
    # alignment might be needed based on specific signal definitions
    aligned_implementation = np.zeros_like(implementation_signals)

    # Track active trades in backtest
    active_trade = False
    trade_start_idx = 0

    for i in range(len(backtest_signals)):
        # Detect trade entry in backtest
        if backtest_signals[i] > 0 and not active_trade:
            active_trade = True
            trade_start_idx = i

        # Detect trade exit in backtest
        elif backtest_signals[i] < 0 and active_trade:
            active_trade = False

            # Find corresponding implementation signals during this trade period
            impl_signals_during_trade = implementation_signals[trade_start_idx : i + 1]

            # If implementation had any signals during this period, consider it aligned
            if np.any(impl_signals_during_trade != 0):
                aligned_implementation[
                    trade_start_idx : i + 1
                ] = implementation_signals[trade_start_idx : i + 1]

    if log:
        match_rate = np.mean(
            np.sign(aligned_implementation) == np.sign(backtest_signals)
        )
        log(f"Signal alignment complete. Match rate: {match_rate:.2%}", "info")

    return {
        "backtest_signals": backtest_signals,
        "implementation_signals": implementation_signals,
        "aligned_implementation": aligned_implementation,
        "aligned": True,
    }


# Phase 2 Enhancement: Standardized Signal Processing


@dataclass
class SignalCountingStandards:
    """Standardized signal counting rules to prevent discrepancies."""

    # Method for portfolio-level counting (prevents 17× inflation)
    portfolio_method: SignalDefinitionMode = SignalDefinitionMode.ENTRY_ONLY

    # Method for strategy-level counting (preserves existing behavior)
    strategy_method: SignalDefinitionMode = SignalDefinitionMode.POSITION_CHANGE

    # Validation thresholds
    max_signal_frequency: float = 0.5  # Maximum 50% of periods with signals
    min_signal_count: int = 5  # Minimum signals for valid strategy

    # Column naming standards
    signal_column: str = "signal"
    position_column: str = "Position"
    date_column: str = "Date"


def count_signals_standardized(
    df: pl.DataFrame,
    standards: Optional[SignalCountingStandards] = None,
    level: str = "strategy",  # "strategy" or "portfolio"
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, int]:
    """
    Count signals using standardized methodology to prevent discrepancies.

    This function implements the Phase 2 fix for signal counting issues:
    - Uses entry-only counting for portfolio metrics (prevents inflation)
    - Uses position-change counting for strategy metrics (preserves compatibility)
    - Validates signal frequency and counts

    Args:
        df: DataFrame with position data
        standards: Signal counting standards
        level: "strategy" or "portfolio" counting level
        log: Optional logging function

    Returns:
        Dictionary with signal counts and validation info
    """
    if standards is None:
        standards = SignalCountingStandards()

    if log:
        log(f"Counting signals at {level} level using standardized methodology", "info")

    # Choose counting method based on level
    if level == "portfolio":
        mode = standards.portfolio_method
    else:
        mode = standards.strategy_method

    # Extract signals using the chosen mode
    signals_df = extract_signals(df, mode, standards.position_column, log)

    if len(signals_df) == 0:
        return {"total": 0, "validation_passed": False, "error": "no_signals_extracted"}

    # Count non-zero signals
    signal_count = int(signals_df.filter(pl.col("signal") != 0).height)

    # Validation checks
    validation_passed = True
    validation_issues = []

    # Check signal frequency
    if len(df) > 0:
        signal_frequency = signal_count / len(df)
        if signal_frequency > standards.max_signal_frequency:
            validation_passed = False
            validation_issues.append(
                f"Signal frequency {signal_frequency:.2%} exceeds maximum {standards.max_signal_frequency:.2%}"
            )

    # Check minimum signal count
    if signal_count < standards.min_signal_count:
        validation_passed = False
        validation_issues.append(
            f"Signal count {signal_count} below minimum {standards.min_signal_count}"
        )

    if log and validation_issues:
        for issue in validation_issues:
            log(f"Signal validation issue: {issue}", "warning")

    return {
        "total": signal_count,
        "validation_passed": validation_passed,
        "validation_issues": validation_issues,
        "method": mode.value,
        "level": level,
    }


def calculate_portfolio_unique_signals_v2(
    strategy_dataframes: List[pl.DataFrame],
    standards: Optional[SignalCountingStandards] = None,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """
    Calculate unique portfolio signals using Phase 2 methodology.

    This function fixes the 17× signal inflation by:
    1. Extracting unique signal dates across all strategies
    2. Counting signals at portfolio level vs strategy level
    3. Providing overlap analysis

    Args:
        strategy_dataframes: List of strategy DataFrames
        standards: Signal counting standards
        log: Optional logging function

    Returns:
        Dictionary with portfolio signal metrics
    """
    if standards is None:
        standards = SignalCountingStandards()

    if not strategy_dataframes:
        return {"unique_signals": 0, "total_strategy_signals": 0, "overlap_ratio": 0}

    if log:
        log(
            f"Calculating portfolio unique signals for {len(strategy_dataframes)} strategies",
            "info",
        )

    # Collect all unique signal dates
    all_signal_dates = set()
    total_strategy_signals = 0
    strategy_counts = []

    for i, df in enumerate(strategy_dataframes):
        # Count strategy-level signals
        strategy_counts_result = count_signals_standardized(
            df, standards, level="strategy", log=log
        )
        strategy_signal_count = strategy_counts_result["total"]
        total_strategy_signals += strategy_signal_count
        strategy_counts.append(strategy_signal_count)

        # Extract signal dates for portfolio-level uniqueness
        signals_df = extract_signals(
            df, standards.portfolio_method, standards.position_column, log
        )

        if len(signals_df) > 0:
            # Get dates where signals occur
            signal_dates = (
                signals_df.filter(pl.col("signal") != 0).get_column("Date").to_list()
            )
            all_signal_dates.update(signal_dates)

        if log:
            log(f"Strategy {i+1}: {strategy_signal_count} signals", "info")

    # Calculate portfolio metrics
    unique_signal_count = len(all_signal_dates)
    overlap_ratio = (
        total_strategy_signals / unique_signal_count if unique_signal_count > 0 else 0
    )

    if log:
        log(
            f"Portfolio summary: {total_strategy_signals} total strategy signals, {unique_signal_count} unique signals",
            "info",
        )
        log(
            f"Signal overlap ratio: {overlap_ratio:.2f}× (explains the inflation)",
            "info",
        )

    return {
        "unique_signals": unique_signal_count,
        "total_strategy_signals": total_strategy_signals,
        "overlap_ratio": overlap_ratio,
        "strategy_counts": strategy_counts,
        "unique_signal_dates": sorted(list(all_signal_dates))
        if all_signal_dates
        else [],
        "validation": {
            "strategy_count": len(strategy_dataframes),
            "avg_signals_per_strategy": total_strategy_signals
            / len(strategy_dataframes)
            if strategy_dataframes
            else 0,
            "inflation_factor": overlap_ratio,
        },
    }


def convert_to_pandas_signals(polars_signals: List[pl.DataFrame]) -> List[pd.DataFrame]:
    """
    Convert Polars DataFrames to Pandas for compatibility with existing code.

    Args:
        polars_signals: List of Polars DataFrames with signal data

    Returns:
        List of Pandas DataFrames with signal data
    """
    pandas_signals = []

    for df in polars_signals:
        # Convert to pandas and ensure proper index
        df_pd = df.to_pandas()

        # Set Date as index if it's a column
        if "Date" in df_pd.columns and df_pd.index.name != "Date":
            df_pd = df_pd.set_index("Date")

        pandas_signals.append(df_pd)

    return pandas_signals


def validate_signal_consistency(
    csv_trades: int,
    json_signals: int,
    tolerance: float = 0.1,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """
    Validate signal count consistency between CSV and JSON data.

    Args:
        csv_trades: Number of trades from CSV backtest
        json_signals: Number of signals from JSON metrics
        tolerance: Tolerance for difference (default 10%)
        log: Optional logging function

    Returns:
        Dictionary with validation results
    """
    if csv_trades == 0:
        return {"valid": False, "error": "no_csv_trades"}

    # Calculate difference
    difference = abs(json_signals - csv_trades) / csv_trades
    is_valid = difference <= tolerance

    # Determine issue type
    if json_signals > csv_trades * 2:
        issue_type = "severe_inflation"
    elif json_signals > csv_trades * 1.2:
        issue_type = "moderate_inflation"
    elif json_signals < csv_trades * 0.8:
        issue_type = "undercount"
    else:
        issue_type = "acceptable"

    result = {
        "valid": is_valid,
        "csv_trades": csv_trades,
        "json_signals": json_signals,
        "difference_ratio": difference,
        "issue_type": issue_type,
        "tolerance": tolerance,
    }

    if log:
        if is_valid:
            log(
                f"Signal consistency validation PASSED: {json_signals} signals vs {csv_trades} trades (diff: {difference:.1%})",
                "info",
            )
        else:
            log(
                f"Signal consistency validation FAILED: {json_signals} signals vs {csv_trades} trades (diff: {difference:.1%}, type: {issue_type})",
                "error",
            )

    return result
