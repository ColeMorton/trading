"""Signal Metrics Analysis Module for Trading Strategies.

This module provides functionality for calculating signal metrics
to analyze the frequency and distribution of trading signals.
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from app.tools.setup_logging import setup_logging

from .signal_processor import SignalDefinition, SignalProcessor


# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv("USE_FIXED_SIGNAL_PROC", "true").lower() == "true"


def calculate_signal_metrics(
    aligned_data: list[pl.DataFrame],
    log: Callable | None = None,
) -> dict[str, Any]:
    """Calculate signal metrics for all strategies.

    Args:
        aligned_data (List[pl.DataFrame]): List of aligned dataframes with signal data
        log (Optional[callable]): Logging function

    Returns:
        Dict[str, Any]: Dictionary of signal metrics
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "signal_metrics",
            Path("./logs"),
            "signal_metrics.log",
        )

    try:
        log("Calculating signal metrics", "info")

        # Initialize metrics dictionary
        metrics = {}

        # Calculate portfolio-level metrics
        all_signals = []

        # Initialize signal processor
        signal_processor = SignalProcessor(use_fixed=USE_FIXED_SIGNAL_PROC)

        # Process each strategy
        for i, df in enumerate(aligned_data, 1):
            # Convert to pandas for date handling
            df_pd = df.to_pandas()

            # Set Date as index for proper time-based operations
            if "Date" in df_pd.columns:
                df_pd = df_pd.set_index("Date")

            if USE_FIXED_SIGNAL_PROC:
                # Use standardized signal processing
                signal_def = SignalDefinition(
                    signal_column="Signal" if "Signal" in df_pd.columns else "Position",
                    position_column="Position",
                )

                # Get comprehensive signal counts
                signal_processor.get_comprehensive_counts(df_pd, signal_def)

                # Use position signals for time-based analysis (consistent with legacy)
                signal_processor.count_position_signals(df_pd, signal_def)
                _, filtered_signals_df = signal_processor.count_filtered_signals(
                    df_pd,
                    signal_def,
                )

                # Create signals dataframe for monthly analysis
                if len(filtered_signals_df) > 0:
                    signals = filtered_signals_df.copy()
                else:
                    # Fallback to position-based signals
                    df_pd["signal"] = df_pd["Position"].diff().fillna(0)
                    signals = df_pd[df_pd["signal"] != 0].copy()
            else:
                # Legacy signal extraction
                df_pd["signal"] = df_pd["Position"].diff().fillna(0)
                signals = df_pd[df_pd["signal"] != 0].copy()  # Create an explicit copy

            # Add to all signals for portfolio metrics
            all_signals.append(signals)

            # Calculate monthly signal counts
            signals.loc[:, "month"] = signals.index.to_period("M")
            monthly_counts = signals.groupby("month").size()

            # Calculate metrics
            if len(monthly_counts) > 0:
                mean_signals = monthly_counts.mean()
                median_signals = monthly_counts.median()
                signal_volatility = (
                    monthly_counts.std() if len(monthly_counts) > 1 else 0
                )
                max_monthly = monthly_counts.max()
                min_monthly = monthly_counts.min()
                total_signals = len(signals)

                # Store strategy-specific metrics
                metrics[f"strategy_{i}_mean_signals"] = mean_signals
                metrics[f"strategy_{i}_median_signals"] = median_signals
                metrics[f"strategy_{i}_signal_volatility"] = signal_volatility
                metrics[f"strategy_{i}_max_monthly_signals"] = max_monthly
                metrics[f"strategy_{i}_min_monthly_signals"] = min_monthly
                metrics[f"strategy_{i}_total_signals"] = total_signals
            else:
                # No signals for this strategy
                metrics[f"strategy_{i}_mean_signals"] = 0
                metrics[f"strategy_{i}_median_signals"] = 0
                metrics[f"strategy_{i}_signal_volatility"] = 0
                metrics[f"strategy_{i}_max_monthly_signals"] = 0
                metrics[f"strategy_{i}_min_monthly_signals"] = 0
                metrics[f"strategy_{i}_total_signals"] = 0

        # Calculate portfolio-level metrics
        if all_signals:
            # FIXED: Calculate both strategy-level and unique portfolio-level metrics

            # Strategy-level aggregation (original behavior for strategy analysis)
            combined_signals = pd.concat(all_signals).copy()

            # Portfolio-level unique signals (new behavior for portfolio analysis)
            unique_signals = _calculate_unique_portfolio_signals(all_signals, log)

            # Ensure index is properly set for period operations
            if not isinstance(combined_signals.index, pd.DatetimeIndex):
                log("Warning: Combined signals index is not a DatetimeIndex", "warning")
                # Try to recover by using the first Date column found
                for col in combined_signals.columns:
                    if col.lower() == "date":
                        combined_signals = combined_signals.set_index(col)
                        break

            combined_signals.loc[:, "month"] = combined_signals.index.to_period("M")

            # Calculate monthly counts for strategy aggregation
            strategy_monthly_counts = combined_signals.groupby("month").size()

            # Calculate monthly counts for unique portfolio signals
            if len(unique_signals) > 0:
                unique_signals.loc[:, "month"] = unique_signals.index.to_period("M")
                portfolio_monthly_counts = unique_signals.groupby("month").size()
            else:
                portfolio_monthly_counts = pd.Series(dtype="int64")

            # Store both strategy and portfolio metrics
            if len(strategy_monthly_counts) > 0:
                # Strategy-level metrics (for strategy analysis)
                strategy_mean = strategy_monthly_counts.mean()
                strategy_median = strategy_monthly_counts.median()
                strategy_volatility = (
                    strategy_monthly_counts.std()
                    if len(strategy_monthly_counts) > 1
                    else 0
                )
                strategy_max = strategy_monthly_counts.max()
                strategy_min = strategy_monthly_counts.min()
                strategy_total = len(combined_signals)

                # Portfolio-level metrics (for portfolio analysis)
                if len(portfolio_monthly_counts) > 0:
                    portfolio_mean = portfolio_monthly_counts.mean()
                    portfolio_median = portfolio_monthly_counts.median()
                    portfolio_volatility = (
                        portfolio_monthly_counts.std()
                        if len(portfolio_monthly_counts) > 1
                        else 0
                    )
                    portfolio_max = portfolio_monthly_counts.max()
                    portfolio_min = portfolio_monthly_counts.min()
                    portfolio_total = len(unique_signals)
                else:
                    portfolio_mean = portfolio_median = portfolio_volatility = 0
                    portfolio_max = portfolio_min = portfolio_total = 0

                # Calculate standard deviation bounds for both
                strategy_std_below = max(0, strategy_mean - strategy_volatility)
                strategy_std_above = strategy_mean + strategy_volatility
                portfolio_std_below = max(0, portfolio_mean - portfolio_volatility)
                portfolio_std_above = portfolio_mean + portfolio_volatility

                # Store strategy-level metrics (preserving original API)
                metrics["mean_signals"] = strategy_mean
                metrics["median_signals"] = strategy_median
                metrics["signal_volatility"] = strategy_volatility
                metrics["max_monthly_signals"] = strategy_max
                metrics["min_monthly_signals"] = strategy_min
                metrics["total_signals"] = strategy_total
                metrics["std_below_mean"] = strategy_std_below
                metrics["std_above_mean"] = strategy_std_above

                # Store new portfolio-level metrics
                metrics["portfolio_mean_signals"] = portfolio_mean
                metrics["portfolio_median_signals"] = portfolio_median
                metrics["portfolio_signal_volatility"] = portfolio_volatility
                metrics["portfolio_max_monthly_signals"] = portfolio_max
                metrics["portfolio_min_monthly_signals"] = portfolio_min
                metrics["portfolio_total_signals"] = portfolio_total
                metrics["portfolio_std_below_mean"] = portfolio_std_below
                metrics["portfolio_std_above_mean"] = portfolio_std_above

                # Signal overlap analysis
                if portfolio_total > 0:
                    signal_overlap_ratio = strategy_total / portfolio_total
                    metrics["signal_overlap_ratio"] = signal_overlap_ratio
                    log(
                        f"Signal overlap analysis: {strategy_total} strategy signals / {portfolio_total} unique signals = {signal_overlap_ratio:.2f}× overlap",
                        "info",
                    )
                else:
                    metrics["signal_overlap_ratio"] = 0
            else:
                # No signals for the portfolio
                metrics["mean_signals"] = 0
                metrics["median_signals"] = 0
                metrics["signal_volatility"] = 0
                metrics["max_monthly_signals"] = 0
                metrics["min_monthly_signals"] = 0
                metrics["total_signals"] = 0
                metrics["std_below_mean"] = 0
                metrics["std_above_mean"] = 0

        log("Signal metrics calculation completed", "info")
        return metrics

    except Exception as e:
        log(f"Error calculating signal metrics: {e!s}", "error")
        # Return empty metrics on error
        return {
            "mean_signals": 0,
            "median_signals": 0,
            "signal_volatility": 0,
            "max_monthly_signals": 0,
            "min_monthly_signals": 0,
            "total_signals": 0,
            "std_below_mean": 0,
            "std_above_mean": 0,
            "portfolio_total_signals": 0,
            "signal_overlap_ratio": 0,
        }


def _calculate_unique_portfolio_signals(
    all_signals: list[pd.DataFrame],
    log: Callable,
) -> pd.DataFrame:
    """
    Calculate unique portfolio signals by removing duplicates across strategies.

    This function identifies unique trading signals at the portfolio level,
    removing the inflation caused by multiple strategies signaling on the same dates.

    Args:
        all_signals: List of DataFrames containing signal data
        log: Logging function

    Returns:
        DataFrame with unique portfolio signals
    """
    try:
        if not all_signals:
            log("No signals provided for unique calculation", "warning")
            return pd.DataFrame()

        log("Calculating unique portfolio signals", "info")

        # Collect all unique signal dates across all strategies
        unique_signal_dates = set()

        for i, signals_df in enumerate(all_signals):
            if len(signals_df) == 0:
                continue

            # Add signal dates to the set (automatically removes duplicates)
            signal_dates = signals_df.index.tolist()
            unique_signal_dates.update(signal_dates)

            log(f"Strategy {i+1}: {len(signal_dates)} signals", "info")

        # Create DataFrame with unique signal dates
        if unique_signal_dates:
            unique_dates_sorted = sorted(unique_signal_dates)
            unique_signals = pd.DataFrame(
                index=pd.DatetimeIndex(unique_dates_sorted),
                data={"unique_signal": 1},
            )
            log(
                f"Portfolio unique signals: {len(unique_signals)} (from {sum(len(s) for s in all_signals)} total strategy signals)",
                "info",
            )
        else:
            unique_signals = pd.DataFrame()
            log("No unique signals found", "warning")

        return unique_signals

    except Exception as e:
        log(f"Error calculating unique portfolio signals: {e!s}", "error")
        return pd.DataFrame()
