"""
Standardized Signal Metrics Module.

This module provides a unified framework for calculating signal metrics,
combining frequency, distribution, and quality metrics in a consistent manner.
This is a refactored version that uses the new unified modules for metrics calculation,
normalization, error handling, and data processing.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from app.tools.data_processing import DataProcessor
from app.tools.error_handling import ErrorHandler, validate_dataframe
from app.tools.metrics_calculation import (
    MetricsCalculator,
    calculate_signal_metrics as calc_metrics,
    calculate_signal_quality_metrics as calc_quality_metrics,
)
from app.tools.normalization import Normalizer
from app.tools.setup_logging import setup_logging


class SignalMetrics:
    """Class for calculating comprehensive signal metrics.

    This class is a wrapper around the new unified modules for metrics calculation,
    normalization, error handling, and data processing. It provides backward compatibility
    with the old API while leveraging the new optimized implementations.
    """

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the SignalMetrics class.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging(
                "signal_metrics",
                Path("./logs"),
                "signal_metrics.log",
            )
        else:
            self.log = log

        # Initialize the component classes
        self.metrics_calculator = MetricsCalculator(log)
        self.normalizer = Normalizer(log)
        self.error_handler = ErrorHandler(log)
        self.data_processor = DataProcessor(log)

    def calculate_frequency_metrics(
        self,
        data: pl.DataFrame | pd.DataFrame,
        signal_column: str = "Signal",
        date_column: str = "Date",
    ) -> dict[str, Any]:
        """Calculate signal frequency metrics.

        Args:
            data: DataFrame containing signal data
            signal_column: Name of the signal column
            date_column: Name of the date column

        Returns:
            Dict[str, Any]: Dictionary of frequency metrics
        """
        try:
            # Validate input data
            validate_dataframe(data, [signal_column], "Signal data")

            # Use the metrics calculator to calculate frequency metrics
            return self.metrics_calculator.calculate_frequency_metrics(
                data,
                signal_column,
                date_column,
            )
        except Exception as e:
            self.log(f"Error calculating signal frequency metrics: {e!s}", "error")
            return self.metrics_calculator._get_empty_frequency_metrics()

    def calculate_quality_metrics(
        self,
        signals_df: pl.DataFrame | pd.DataFrame,
        returns_df: pl.DataFrame | pd.DataFrame,
        strategy_id: str,
        signal_column: str = "signal",
        return_column: str = "return",
        date_column: str = "Date",
    ) -> dict[str, Any]:
        """Calculate signal quality metrics.

        Args:
            signals_df: DataFrame containing signal data
            returns_df: DataFrame containing return data
            strategy_id: Identifier for the strategy
            signal_column: Name of the signal column
            return_column: Name of the return column
            date_column: Name of the date column

        Returns:
            Dict[str, Any]: Dictionary of signal quality metrics
        """
        try:
            # Validate input data
            validate_dataframe(signals_df, [signal_column, date_column], "Signals data")
            validate_dataframe(returns_df, [return_column, date_column], "Returns data")

            # Use the metrics calculator to calculate quality metrics
            metrics = self.metrics_calculator.calculate_signal_quality_metrics(
                signals_df,
                returns_df,
                strategy_id,
                signal_column,
                return_column,
                date_column,
            )

            # Normalize the metrics for consistent scaling
            self.normalizer.normalize_metrics(metrics)

            return metrics
        except Exception as e:
            self.log(
                f"Error calculating signal quality metrics for {strategy_id}: {e!s}",
                "error",
            )
            return {"signal_count": 0, "signal_quality_score": 0.0}

    def calculate_portfolio_metrics(
        self,
        data_list: list[pl.DataFrame | pd.DataFrame],
        strategy_ids: list[str],
        signal_column: str = "Signal",
        date_column: str = "Date",
    ) -> dict[str, Any]:
        """Calculate portfolio-level signal metrics.

        Args:
            data_list: List of DataFrames containing signal data
            strategy_ids: List of strategy identifiers
            signal_column: Name of the signal column
            date_column: Name of the date column

        Returns:
            Dict[str, Any]: Dictionary of portfolio-level metrics
        """
        try:
            # Validate input data
            if not data_list:
                self.log(
                    "Empty data list provided for portfolio metrics calculation",
                    "warning",
                )
                return {}

            # Use the metrics calculator to calculate portfolio metrics
            return self.metrics_calculator.calculate_portfolio_metrics(
                data_list,
                strategy_ids,
                signal_column,
                date_column,
            )
        except Exception as e:
            self.log(
                f"Error calculating portfolio-level signal metrics: {e!s}",
                "error",
            )
            return {
                "portfolio_mean_signals_per_month": 0.0,
                "portfolio_median_signals_per_month": 0.0,
                "portfolio_signal_volatility": 0.0,
                "portfolio_max_monthly_signals": 0,
                "portfolio_min_monthly_signals": 0,
                "portfolio_total_signals": 0,
            }


# Convenience functions for backward compatibility


def calculate_signal_metrics(
    aligned_data: list[pl.DataFrame],
    log: Callable | None | None = None,
) -> dict[str, Any]:
    """Calculate signal metrics for all strategies (legacy function).

    Args:
        aligned_data: List of DataFrames containing signal data
        log: Optional logging function

    Returns:
        Dict[str, Any]: Dictionary of signal metrics
    """
    return calc_metrics(aligned_data, log)


def calculate_signal_quality_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    strategy_id: str,
    log: Callable[[str, str], None],
) -> dict[str, Any]:
    """Calculate signal quality metrics for a strategy (legacy function).

    Args:
        signals_df: DataFrame containing signal data
        returns_df: DataFrame containing return data
        strategy_id: Identifier for the strategy
        log: Logging function

    Returns:
        Dict[str, Any]: Dictionary of signal quality metrics
    """
    return calc_quality_metrics(signals_df, returns_df, strategy_id, log)
