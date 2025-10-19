"""
Equity Data Extractor Module

This module provides functionality for extracting and calculating equity curve data
from VectorBT Portfolio objects. It supports comprehensive equity metrics including
cumulative equity, drawdowns, MFE/MAE calculations, and bar-by-bar analysis.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt

from app.tools.exceptions import TradingSystemError


class MetricType(Enum):
    """Supported metric types for backtest selection."""

    MEAN = "mean"
    MEDIAN = "median"
    BEST = "best"
    WORST = "worst"


@dataclass
class EquityData:
    """
    Structured equity data container with comprehensive metrics.

    Attributes:
        timestamp: Date/time index for the equity curve
        equity: Cumulative nominal equity value (indexed starting at 0)
        equity_pct: Cumulative equity change percentage from initial value
        equity_change: Bar-to-bar equity change (non-cumulative)
        equity_change_pct: Bar-to-bar equity change percentage (non-cumulative)
        drawdown: Current drawdown from peak equity
        drawdown_pct: Current drawdown percentage from peak equity
        peak_equity: Running maximum equity value
        mfe: Maximum Favorable Excursion (cumulative best equity from entry)
        mae: Maximum Adverse Excursion (cumulative worst equity from entry)
    """

    timestamp: pd.Index
    equity: np.ndarray
    equity_pct: np.ndarray
    equity_change: np.ndarray
    equity_change_pct: np.ndarray
    drawdown: np.ndarray
    drawdown_pct: np.ndarray
    peak_equity: np.ndarray
    mfe: np.ndarray
    mae: np.ndarray

    def to_dataframe(self) -> pd.DataFrame:
        """Convert EquityData to pandas DataFrame for export."""
        return pd.DataFrame(
            {
                "timestamp": self.timestamp,
                "equity": self.equity,
                "equity_pct": self.equity_pct,
                "equity_change": self.equity_change,
                "equity_change_pct": self.equity_change_pct,
                "drawdown": self.drawdown,
                "drawdown_pct": self.drawdown_pct,
                "peak_equity": self.peak_equity,
                "mfe": self.mfe,
                "mae": self.mae,
            }
        )

    def to_polars(self) -> pl.DataFrame:
        """Convert EquityData to polars DataFrame for export."""
        return pl.DataFrame(
            {
                "timestamp": self.timestamp.to_list(),
                "equity": self.equity.tolist(),
                "equity_pct": self.equity_pct.tolist(),
                "equity_change": self.equity_change.tolist(),
                "equity_change_pct": self.equity_change_pct.tolist(),
                "drawdown": self.drawdown.tolist(),
                "drawdown_pct": self.drawdown_pct.tolist(),
                "peak_equity": self.peak_equity.tolist(),
                "mfe": self.mfe.tolist(),
                "mae": self.mae.tolist(),
            }
        )


class EquityDataExtractor:
    """
    Core equity data extraction and calculation engine.

    This class handles the extraction of equity curve data from VectorBT Portfolio
    objects and calculates comprehensive equity metrics for strategy analysis.
    """

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """
        Initialize the equity data extractor.

        Args:
            log: Optional logging function for recording events and errors
        """
        self.log = log or self._default_log

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def extract_equity_data(
        self,
        portfolio: "vbt.Portfolio",
        metric_type: MetricType = MetricType.MEAN,
        config: dict[str, Any] | None = None,
    ) -> EquityData:
        """
        Extract comprehensive equity data from VectorBT Portfolio.

        Args:
            portfolio: VectorBT Portfolio object from backtesting
            metric_type: Which metric to select for equity calculation
            config: Optional configuration dictionary

        Returns:
            EquityData object with all calculated metrics

        Raises:
            TradingSystemError: If equity extraction fails
        """
        try:
            self.log(
                f"Extracting equity data with metric type: {metric_type.value}", "info"
            )

            # Extract base equity curve from portfolio
            equity_curve = self._extract_base_equity_curve(portfolio, metric_type)
            timestamp_index = self._extract_timestamp_index(portfolio)

            # Validate data consistency
            if len(equity_curve) != len(timestamp_index):
                raise TradingSystemError(
                    f"Equity curve length ({len(equity_curve)}) doesn't match timestamp length ({len(timestamp_index)})"
                )

            # Calculate all equity metrics
            equity_metrics = self._calculate_equity_metrics(equity_curve)

            # Calculate drawdown metrics
            drawdown_metrics = self._calculate_drawdown_metrics(equity_curve)

            # Calculate MFE/MAE metrics
            mfe_mae_metrics = self._calculate_mfe_mae_metrics(portfolio, equity_curve)

            # Combine all metrics into EquityData object
            equity_data = EquityData(
                timestamp=timestamp_index,
                equity=equity_metrics["equity"],
                equity_pct=equity_metrics["equity_pct"],
                equity_change=equity_metrics["equity_change"],
                equity_change_pct=equity_metrics["equity_change_pct"],
                drawdown=drawdown_metrics["drawdown"],
                drawdown_pct=drawdown_metrics["drawdown_pct"],
                peak_equity=drawdown_metrics["peak_equity"],
                mfe=mfe_mae_metrics["mfe"],
                mae=mfe_mae_metrics["mae"],
            )

            self.log(
                f"Successfully extracted equity data with {len(equity_curve)} data points",
                "info",
            )
            return equity_data

        except Exception as e:
            error_msg = f"Failed to extract equity data: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _extract_base_equity_curve(
        self, portfolio: "vbt.Portfolio", metric_type: MetricType
    ) -> np.ndarray:
        """
        Extract the base equity curve from portfolio based on metric type.

        Args:
            portfolio: VectorBT Portfolio object
            metric_type: Type of metric to extract

        Returns:
            Numpy array of equity values
        """
        try:
            # Get portfolio value (equity curve)
            portfolio_value = portfolio.value()

            # Handle different return types from VectorBT
            if hasattr(portfolio_value, "values"):
                # If it's a pandas Series/DataFrame
                if portfolio_value.ndim > 1:
                    # Multiple columns - apply metric selection
                    equity_curve = self._apply_metric_selection(
                        portfolio_value.values, metric_type
                    )
                else:
                    # Single column
                    equity_curve = portfolio_value.values
            # If it's already a numpy array
            elif portfolio_value.ndim > 1:
                equity_curve = self._apply_metric_selection(
                    portfolio_value, metric_type
                )
            else:
                equity_curve = portfolio_value

            # Ensure we have a 1D array
            if equity_curve.ndim > 1:
                equity_curve = equity_curve.flatten()

            # Convert to numpy array and ensure float type
            equity_curve = np.asarray(equity_curve, dtype=np.float64)

            self.log(
                f"Extracted base equity curve with {len(equity_curve)} points", "debug"
            )
            return equity_curve

        except Exception as e:
            raise TradingSystemError(
                f"Failed to extract base equity curve: {e!s}"
            ) from e

    def _extract_timestamp_index(self, portfolio: "vbt.Portfolio") -> pd.Index:
        """
        Extract timestamp index from portfolio.

        Args:
            portfolio: VectorBT Portfolio object

        Returns:
            Pandas Index with timestamps
        """
        try:
            # Try to get index from portfolio wrapper
            if hasattr(portfolio, "wrapper") and hasattr(portfolio.wrapper, "index"):
                return portfolio.wrapper.index

            # Try to get from portfolio value
            portfolio_value = portfolio.value()
            if hasattr(portfolio_value, "index"):
                return portfolio_value.index

            # Try to get from portfolio close prices
            if hasattr(portfolio, "close") and hasattr(portfolio.close, "index"):
                return portfolio.close.index

            # Fallback to range index
            equity_curve = self._extract_base_equity_curve(portfolio, MetricType.MEAN)
            self.log("Using range index as timestamp fallback", "warning")
            return pd.RangeIndex(len(equity_curve))

        except Exception as e:
            raise TradingSystemError(f"Failed to extract timestamp index: {e!s}") from e

    def _apply_metric_selection(
        self, data: np.ndarray, metric_type: MetricType
    ) -> np.ndarray:
        """
        Apply metric selection to multi-dimensional data.

        Args:
            data: Multi-dimensional numpy array
            metric_type: Type of metric to apply

        Returns:
            1D numpy array with selected metric
        """
        if data.ndim == 1:
            return data

        # For 2D data, apply metric across columns (different backtests)
        if metric_type == MetricType.MEAN:
            return np.mean(data, axis=1)
        if metric_type == MetricType.MEDIAN:
            return np.median(data, axis=1)
        if metric_type == MetricType.BEST:
            # Best = highest final value
            final_values = data[-1, :]
            best_column = np.argmax(final_values)
            return data[:, best_column]
        if metric_type == MetricType.WORST:
            # Worst = lowest final value
            final_values = data[-1, :]
            worst_column = np.argmin(final_values)
            return data[:, worst_column]
        self.log(f"Unknown metric type: {metric_type}, using mean", "warning")
        return np.mean(data, axis=1)

    def _calculate_equity_metrics(
        self, equity_curve: np.ndarray
    ) -> dict[str, np.ndarray]:
        """
        Calculate basic equity metrics.

        Args:
            equity_curve: Base equity curve array

        Returns:
            Dictionary with equity metrics
        """
        # Index equity at 0 (subtract initial value)
        initial_value = equity_curve[0] if len(equity_curve) > 0 else 1000.0
        indexed_equity = equity_curve - initial_value

        # Calculate cumulative percentage change (handle divide by zero)
        if initial_value != 0:
            equity_pct = ((equity_curve / initial_value) - 1.0) * 100.0
        else:
            equity_pct = np.zeros_like(equity_curve)

        # Calculate bar-to-bar changes
        equity_change = np.diff(equity_curve, prepend=equity_curve[0])
        equity_change[0] = 0.0  # First bar has no change

        # Calculate bar-to-bar percentage changes
        equity_change_pct = np.zeros_like(equity_curve)
        for i in range(1, len(equity_curve)):
            if equity_curve[i - 1] != 0:
                equity_change_pct[i] = (
                    (equity_curve[i] / equity_curve[i - 1]) - 1.0
                ) * 100.0

        return {
            "equity": indexed_equity,
            "equity_pct": equity_pct,
            "equity_change": equity_change,
            "equity_change_pct": equity_change_pct,
        }

    def _calculate_drawdown_metrics(
        self, equity_curve: np.ndarray
    ) -> dict[str, np.ndarray]:
        """
        Calculate drawdown metrics including running peaks.

        Args:
            equity_curve: Base equity curve array

        Returns:
            Dictionary with drawdown metrics
        """
        # Calculate running maximum (peak equity)
        peak_equity = np.maximum.accumulate(equity_curve)

        # Calculate absolute drawdown
        drawdown = peak_equity - equity_curve

        # Calculate percentage drawdown
        drawdown_pct = np.zeros_like(equity_curve)
        non_zero_peaks = peak_equity != 0
        drawdown_pct[non_zero_peaks] = (
            drawdown[non_zero_peaks] / peak_equity[non_zero_peaks]
        ) * 100.0

        return {
            "drawdown": drawdown,
            "drawdown_pct": drawdown_pct,
            "peak_equity": peak_equity,
        }

    def _calculate_mfe_mae_metrics(
        self, portfolio: "vbt.Portfolio", equity_curve: np.ndarray
    ) -> dict[str, np.ndarray]:
        """
        Calculate Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE).

        Args:
            portfolio: VectorBT Portfolio object
            equity_curve: Base equity curve array

        Returns:
            Dictionary with MFE/MAE metrics
        """
        try:
            # Initialize MFE/MAE arrays
            mfe = np.zeros_like(equity_curve)
            mae = np.zeros_like(equity_curve)

            # Try to get trade information from portfolio
            if hasattr(portfolio, "trades"):
                trades = portfolio.trades

                # Get entry and exit indices
                if hasattr(trades, "entry_idx") and hasattr(trades, "exit_idx"):
                    entry_indices = (
                        trades.entry_idx.values
                        if hasattr(trades.entry_idx, "values")
                        else trades.entry_idx
                    )
                    exit_indices = (
                        trades.exit_idx.values
                        if hasattr(trades.exit_idx, "values")
                        else trades.exit_idx
                    )

                    # Handle potential NaN values
                    entry_indices = entry_indices[~np.isnan(entry_indices)]
                    exit_indices = exit_indices[~np.isnan(exit_indices)]

                    # Calculate MFE/MAE for each trade
                    for _i, (entry_idx, exit_idx) in enumerate(
                        zip(entry_indices, exit_indices, strict=False)
                    ):
                        entry_idx = int(entry_idx)
                        exit_idx = int(exit_idx)

                        if entry_idx < len(equity_curve) and exit_idx < len(
                            equity_curve
                        ):
                            trade_equity = equity_curve[entry_idx : exit_idx + 1]
                            entry_equity = equity_curve[entry_idx]

                            # Calculate excursions relative to entry point
                            excursions = trade_equity - entry_equity

                            # Update MFE/MAE for the trade period
                            for j in range(entry_idx, min(exit_idx + 1, len(mfe))):
                                period_excursions = (
                                    equity_curve[entry_idx : j + 1] - entry_equity
                                )
                                mfe[j] = max(
                                    mfe[j],
                                    (
                                        np.max(period_excursions)
                                        if len(period_excursions) > 0
                                        else 0.0
                                    ),
                                )
                                mae[j] = min(
                                    mae[j],
                                    (
                                        np.min(period_excursions)
                                        if len(period_excursions) > 0
                                        else 0.0
                                    ),
                                )

            # If no trade data available, calculate cumulative excursions
            if np.all(mfe == 0) and np.all(mae == 0):
                self.log(
                    "No trade data available, calculating cumulative MFE/MAE", "warning"
                )
                initial_equity = equity_curve[0] if len(equity_curve) > 0 else 0.0
                excursions = equity_curve - initial_equity

                # Cumulative maximum favorable excursion
                mfe = np.maximum.accumulate(excursions)

                # Cumulative maximum adverse excursion (minimum)
                mae = np.minimum.accumulate(excursions)

            return {"mfe": mfe, "mae": mae}

        except Exception as e:
            self.log(f"Failed to calculate MFE/MAE, using zeros: {e!s}", "warning")
            return {
                "mfe": np.zeros_like(equity_curve),
                "mae": np.zeros_like(equity_curve),
            }


def extract_equity_data_from_portfolio(
    portfolio: "vbt.Portfolio",
    metric_type: str | MetricType = MetricType.MEAN,
    config: dict[str, Any] | None = None,
    log: Callable[[str, str], None] | None = None,
) -> EquityData:
    """
    Convenience function for extracting equity data from a VectorBT Portfolio.

    Args:
        portfolio: VectorBT Portfolio object from backtesting
        metric_type: Which metric to select ("mean", "median", "best", "worst" or MetricType enum)
        config: Optional configuration dictionary
        log: Optional logging function

    Returns:
        EquityData object with all calculated metrics

    Raises:
        TradingSystemError: If extraction fails or invalid metric type provided
    """
    # Convert string metric type to enum
    if isinstance(metric_type, str):
        try:
            metric_type = MetricType(metric_type.lower())
        except ValueError:
            if log:
                log(f"Invalid metric type '{metric_type}', using 'mean'", "warning")
            metric_type = MetricType.MEAN

    # Create extractor and extract data
    extractor = EquityDataExtractor(log=log)
    return extractor.extract_equity_data(portfolio, metric_type, config)


def validate_equity_data(
    equity_data: EquityData, log: Callable[[str, str], None] | None = None
) -> bool:
    """
    Validate EquityData object for consistency and correctness.

    Args:
        equity_data: EquityData object to validate
        log: Optional logging function

    Returns:
        True if validation passes, False otherwise
    """
    if log is None:

        def log(msg, level):
            return print(f"[{level.upper()}] {msg}")

    try:
        # Check all arrays have same length
        arrays = [
            equity_data.equity,
            equity_data.equity_pct,
            equity_data.equity_change,
            equity_data.equity_change_pct,
            equity_data.drawdown,
            equity_data.drawdown_pct,
            equity_data.peak_equity,
            equity_data.mfe,
            equity_data.mae,
        ]

        lengths = [len(arr) for arr in arrays]
        if len(set(lengths)) > 1:
            log(f"Array length mismatch: {lengths}", "error")
            return False

        # Check timestamp length matches
        if len(equity_data.timestamp) != lengths[0]:
            log(
                f"Timestamp length ({len(equity_data.timestamp)}) doesn't match data length ({lengths[0]})",
                "error",
            )
            return False

        # Check for NaN values
        for i, arr in enumerate(arrays):
            if np.any(np.isnan(arr)):
                array_names = [
                    "equity",
                    "equity_pct",
                    "equity_change",
                    "equity_change_pct",
                    "drawdown",
                    "drawdown_pct",
                    "peak_equity",
                    "mfe",
                    "mae",
                ]
                log(f"NaN values found in {array_names[i]} array", "warning")

        # Check drawdown consistency
        if not np.all(equity_data.drawdown >= 0):
            log("Negative drawdown values found", "warning")

        # Check peak equity is non-decreasing
        if not np.all(np.diff(equity_data.peak_equity) >= 0):
            log("Peak equity is not non-decreasing", "warning")

        log("Equity data validation passed", "info")
        return True

    except Exception as e:
        log(f"Equity data validation failed: {e!s}", "error")
        return False
