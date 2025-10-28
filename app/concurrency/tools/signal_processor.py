#!/usr/bin/env python3
"""
Standardized signal processing module to fix 90% variance in signal counts.

This module provides consistent signal counting, filtering, and processing
methodologies across all trading modules to eliminate discrepancies.
"""

from dataclasses import dataclass
from enum import Enum
import os

import numpy as np
import pandas as pd
import polars as pl


# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv("USE_FIXED_SIGNAL_PROC", "true").lower() == "true"


class SignalType(Enum):
    """Enumeration for different types of signals."""

    RAW = "raw"  # All detected crossovers/triggers
    FILTERED = "filtered"  # After applying filters (RSI, volume, etc.)
    POSITION = "position"  # Actual position changes (1-day shifted)
    TRADE = "trade"  # Completed trade signals


@dataclass
class SignalCounts:
    """Container for different signal count types."""

    raw_signals: int = 0
    filtered_signals: int = 0
    position_signals: int = 0
    trade_signals: int = 0

    # Additional metadata
    filter_efficiency: float = 0.0  # filtered/raw ratio
    execution_efficiency: float = 0.0  # positions/filtered ratio
    trade_efficiency: float = 0.0  # trades/positions ratio

    def __post_init__(self):
        """Calculate efficiency ratios."""
        if self.raw_signals > 0:
            self.filter_efficiency = self.filtered_signals / self.raw_signals
        if self.filtered_signals > 0:
            self.execution_efficiency = self.position_signals / self.filtered_signals
        if self.position_signals > 0:
            self.trade_efficiency = self.trade_signals / self.position_signals


@dataclass
class SignalDefinition:
    """Definition of signal detection criteria."""

    signal_column: str = "Signal"
    position_column: str = "Position"
    price_column: str = "Close"
    volume_column: str = "Volume"

    # Filter criteria
    min_volume: float | None | None = None
    rsi_column: str | None | None = None
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    volatility_threshold: float | None | None = None

    # Position shift (signals -> positions)
    position_shift: int = 1


class SignalProcessor:
    """
    Standardized signal processor that provides consistent counting
    and filtering methodologies across all modules.
    """

    def __init__(self, use_fixed: bool | None = None):
        """
        Initialize signal processor.

        Args:
            use_fixed: Whether to use fixed signal processing.
                      If None, uses environment variable.
        """
        self.use_fixed = use_fixed if use_fixed is not None else USE_FIXED_SIGNAL_PROC

    def count_raw_signals(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_definition: SignalDefinition,
    ) -> int:
        """
        Count raw signals (all detected crossovers/triggers).

        Args:
            data: DataFrame with signal data
            signal_definition: Signal detection criteria

        Returns:
            Number of raw signals detected
        """
        if isinstance(data, pl.DataFrame):
            df = data.to_pandas()
        else:
            df = data.copy()

        # Count non-zero signals
        signal_col = signal_definition.signal_column
        if signal_col not in df.columns:
            return 0

        raw_count = (df[signal_col] != 0).sum()
        return int(raw_count)

    def count_filtered_signals(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_definition: SignalDefinition,
    ) -> tuple[int, pd.DataFrame]:
        """
        Count filtered signals after applying criteria.

        Args:
            data: DataFrame with signal data
            signal_definition: Signal detection criteria

        Returns:
            Tuple of (filtered_count, filtered_dataframe)
        """
        if isinstance(data, pl.DataFrame):
            df = data.to_pandas()
        else:
            df = data.copy()

        # Start with all non-zero signals
        signal_mask = df[signal_definition.signal_column] != 0

        # Apply volume filter if specified
        if (
            signal_definition.min_volume is not None
            and signal_definition.volume_column in df.columns
        ):
            volume_mask = (
                df[signal_definition.volume_column] >= signal_definition.min_volume
            )
            signal_mask = signal_mask & volume_mask

        # Apply RSI filter if specified
        if (
            signal_definition.rsi_column is not None
            and signal_definition.rsi_column in df.columns
        ):
            # For buy signals (1), RSI should be oversold
            # For sell signals (-1), RSI should be overbought
            buy_signals = df[signal_definition.signal_column] == 1
            sell_signals = df[signal_definition.signal_column] == -1

            rsi_buy_valid = ~buy_signals | (
                df[signal_definition.rsi_column] <= signal_definition.rsi_oversold
            )
            rsi_sell_valid = ~sell_signals | (
                df[signal_definition.rsi_column] >= signal_definition.rsi_overbought
            )

            signal_mask = signal_mask & rsi_buy_valid & rsi_sell_valid

        # Apply volatility filter if specified
        if signal_definition.volatility_threshold is not None:
            # Calculate price volatility (rolling standard deviation)
            price_vol = df[signal_definition.price_column].rolling(20).std()
            vol_mask = price_vol >= signal_definition.volatility_threshold
            signal_mask = signal_mask & vol_mask.fillna(True)

        filtered_df = df[signal_mask].copy()
        filtered_count = len(filtered_df)

        return filtered_count, filtered_df

    def count_position_signals(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_definition: SignalDefinition,
    ) -> int:
        """
        Count position signals (actual position changes).

        Args:
            data: DataFrame with position data
            signal_definition: Signal detection criteria

        Returns:
            Number of position change signals
        """
        if isinstance(data, pl.DataFrame):
            df = data.to_pandas()
        else:
            df = data.copy()

        position_col = signal_definition.position_column
        if position_col not in df.columns:
            return 0

        # Count position changes using diff
        position_changes = df[position_col].diff().fillna(0)
        position_count = (position_changes != 0).sum()

        return int(position_count)

    def count_trade_signals(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_definition: SignalDefinition,
    ) -> int:
        """
        Count completed trade signals.

        Args:
            data: DataFrame with trade data
            signal_definition: Signal detection criteria

        Returns:
            Number of completed trades
        """
        if isinstance(data, pl.DataFrame):
            df = data.to_pandas()
        else:
            df = data.copy()

        # Count trades as position changes (entries and exits)
        position_col = signal_definition.position_column
        if position_col not in df.columns:
            return 0

        positions = df[position_col]

        # Count position changes using pandas diff method for consistency
        position_changes = positions.diff().fillna(
            positions.iloc[0] if len(positions) > 0 else 0,
        )
        trade_count = (position_changes != 0).sum()

        return int(trade_count)

    def get_comprehensive_counts(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_definition: SignalDefinition,
    ) -> SignalCounts:
        """
        Get all signal count types for comprehensive analysis.

        Args:
            data: DataFrame with signal/position data
            signal_definition: Signal detection criteria

        Returns:
            SignalCounts object with all count types
        """
        raw_count = self.count_raw_signals(data, signal_definition)
        filtered_count, _ = self.count_filtered_signals(data, signal_definition)
        position_count = self.count_position_signals(data, signal_definition)
        trade_count = self.count_trade_signals(data, signal_definition)

        return SignalCounts(
            raw_signals=raw_count,
            filtered_signals=filtered_count,
            position_signals=position_count,
            trade_signals=trade_count,
        )

    def reconcile_signal_counts(self, counts: SignalCounts) -> dict[str, int | float]:
        """
        Provide reconciliation analysis of signal counts.

        Args:
            counts: SignalCounts object

        Returns:
            Dictionary with reconciliation metrics
        """
        return {
            "raw_signals": counts.raw_signals,
            "filtered_signals": counts.filtered_signals,
            "position_signals": counts.position_signals,
            "trade_signals": counts.trade_signals,
            "filter_efficiency": counts.filter_efficiency,
            "execution_efficiency": counts.execution_efficiency,
            "trade_efficiency": counts.trade_efficiency,
            "overall_efficiency": (
                counts.trade_signals / counts.raw_signals
                if counts.raw_signals > 0
                else 0.0
            ),
        }

    def standardize_signal_column(
        self,
        data: pd.DataFrame | pl.DataFrame,
        method: str = "crossover",
    ) -> pd.DataFrame | pl.DataFrame:
        """
        Standardize signal detection method across different data formats.

        Args:
            data: DataFrame with trading data
            method: Signal detection method ("crossover", "position_diff", "custom")

        Returns:
            DataFrame with standardized Signal column
        """
        if isinstance(data, pl.DataFrame):
            df = data.to_pandas()
            return_polars = True
        else:
            df = data.copy()
            return_polars = False

        if method == "crossover":
            # Standard moving average crossover signals
            if "Fast_MA" in df.columns and "Slow_MA" in df.columns:
                df["Signal"] = 0
                df.loc[df["Fast_MA"] > df["Slow_MA"], "Signal"] = 1
                df.loc[df["Fast_MA"] < df["Slow_MA"], "Signal"] = -1

        elif method == "position_diff":
            # Generate signals from position changes
            if "Position" in df.columns:
                df["Signal"] = df["Position"].diff().fillna(0)

        elif method == "custom":
            # Keep existing Signal column if present
            if "Signal" not in df.columns:
                df["Signal"] = 0

        # Ensure Signal column exists
        if "Signal" not in df.columns:
            df["Signal"] = 0

        if return_polars:
            return pl.from_pandas(df)
        return df


def calculate_signal_count_standardized(
    data: pd.DataFrame | pl.DataFrame,
    signal_type: str | SignalType = SignalType.FILTERED,
    signal_definition: SignalDefinition | None | None = None,
) -> int:
    """
    Convenience function for standardized signal counting.

    Args:
        data: DataFrame with signal data
        signal_type: Type of signal count to return
        signal_definition: Signal detection criteria (uses defaults if None)

    Returns:
        Signal count of specified type
    """
    processor = SignalProcessor()

    if signal_definition is None:
        signal_definition = SignalDefinition()

    if isinstance(signal_type, str):
        signal_type = SignalType(signal_type)

    if signal_type == SignalType.RAW:
        return processor.count_raw_signals(data, signal_definition)
    if signal_type == SignalType.FILTERED:
        count, _ = processor.count_filtered_signals(data, signal_definition)
        return count
    if signal_type == SignalType.POSITION:
        return processor.count_position_signals(data, signal_definition)
    if signal_type == SignalType.TRADE:
        return processor.count_trade_signals(data, signal_definition)
    msg = f"Unknown signal type: {signal_type}"
    raise ValueError(msg)


if __name__ == "__main__":
    # Example usage and validation
    print("Signal Processor Standardization Module")
    print("=" * 50)

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")

    sample_data = pd.DataFrame(
        {
            "Date": dates,
            "Close": 100 + np.cumsum(np.random.randn(100) * 0.5),
            "Volume": np.random.randint(1000, 10000, 100),
            "Signal": np.random.choice([-1, 0, 1], 100, p=[0.1, 0.8, 0.1]),
            "Position": 0,
            "RSI": np.random.uniform(20, 80, 100),
        },
    )

    # Generate positions from signals (with 1-day shift)
    sample_data["Position"] = sample_data["Signal"].shift(1).fillna(0)

    # Test signal processor
    processor = SignalProcessor()
    signal_def = SignalDefinition(
        min_volume=2000,
        rsi_column="RSI",
        rsi_oversold=30,
        rsi_overbought=70,
    )

    counts = processor.get_comprehensive_counts(sample_data, signal_def)
    reconciliation = processor.reconcile_signal_counts(counts)

    print("Signal Count Analysis:")
    print(f"Raw Signals: {counts.raw_signals}")
    print(f"Filtered Signals: {counts.filtered_signals}")
    print(f"Position Signals: {counts.position_signals}")
    print(f"Trade Signals: {counts.trade_signals}")
    print(f"Filter Efficiency: {counts.filter_efficiency:.2%}")
    print(f"Execution Efficiency: {counts.execution_efficiency:.2%}")
    print(f"Overall Efficiency: {reconciliation['overall_efficiency']:.2%}")
