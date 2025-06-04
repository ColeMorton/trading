"""
Signal Filtering Module.

This module provides a centralized, pipeline-based approach to signal filtering,
ensuring consistent application of filters across the entire application.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import numpy as np
import pandas as pd
import polars as pl

from app.tools.setup_logging import setup_logging

# Type definitions
DataFrame = Union[pl.DataFrame, pd.DataFrame]
FilterResult = Dict[str, Any]
T = TypeVar("T")


class FilterInterface(ABC):
    """Abstract base class for all signal filters."""

    @abstractmethod
    def apply(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply the filter to the data.

        Args:
            data: DataFrame containing signal data
            config: Configuration dictionary for the filter

        Returns:
            DataFrame: Filtered data
        """

    @abstractmethod
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get statistics about the filter application.

        Returns:
            Dict[str, Any]: Statistics about the filter application
        """


class BaseFilter(FilterInterface):
    """Base class for signal filters with common functionality."""

    def __init__(self, name: str, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the filter.

        Args:
            name: Name of the filter
            log: Optional logging function. If not provided, a default logger will be created.
        """
        self.name = name

        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging(
                f"filter_{name.lower()}", Path("./logs"), f"filter_{name.lower()}.log"
            )
        else:
            self.log = log

        # Statistics tracking
        self.total_signals = 0
        self.filtered_signals = 0
        self.rejection_reasons = {}

    def get_filter_stats(self) -> Dict[str, Any]:
        """Get statistics about the filter application.

        Returns:
            Dict[str, Any]: Statistics about the filter application
        """
        return {
            "filter_name": self.name,
            "total_signals": self.total_signals,
            "filtered_signals": self.filtered_signals,
            "pass_rate": 1.0
            - (
                self.filtered_signals / self.total_signals
                if self.total_signals > 0
                else 0.0
            ),
            "rejection_reasons": self.rejection_reasons,
        }

    def _convert_to_pandas(self, data: DataFrame) -> pd.DataFrame:
        """Convert DataFrame to pandas if it's polars.

        Args:
            data: DataFrame to convert

        Returns:
            pd.DataFrame: Pandas DataFrame
        """
        if isinstance(data, pl.DataFrame):
            return data.to_pandas()
        return data

    def _convert_to_polars(self, data: pd.DataFrame) -> pl.DataFrame:
        """Convert DataFrame to polars.

        Args:
            data: DataFrame to convert

        Returns:
            pl.DataFrame: Polars DataFrame
        """
        return pl.from_pandas(data)

    def _track_rejection(self, reason: str, count: int = 1) -> None:
        """Track a rejection reason.

        Args:
            reason: Reason for rejection
            count: Number of rejections for this reason
        """
        if reason in self.rejection_reasons:
            self.rejection_reasons[reason] += count
        else:
            self.rejection_reasons[reason] = count


class RSIFilter(BaseFilter):
    """Filter signals based on RSI values."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the RSI filter.

        Args:
            log: Optional logging function
        """
        super().__init__("RSI", log)

    def apply(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply RSI filter to signals.

        Args:
            data: DataFrame containing signal data
            config: Configuration dictionary with RSI parameters

        Returns:
            DataFrame: Filtered data
        """
        # Extract configuration
        use_rsi = config.get("USE_RSI", False)
        rsi_threshold = config.get("RSI_THRESHOLD", 70)
        direction = config.get("DIRECTION", "Long")
        signal_column = config.get("SIGNAL_COLUMN", "Signal")
        rsi_column = config.get("RSI_COLUMN", "RSI")

        # Skip if RSI filtering is disabled or RSI column is missing
        if not use_rsi or rsi_column not in data.columns:
            self.log(
                f"RSI filtering skipped: enabled={use_rsi}, column_exists={rsi_column in data.columns}",
                "info",
            )
            return data

        self.log(
            f"Applying RSI filter with threshold {rsi_threshold}, direction={direction}",
            "info",
        )

        # Convert to pandas for processing
        is_polars = isinstance(data, pl.DataFrame)
        if is_polars:
            df = data.to_pandas()
        else:
            df = data

        # Count signals before filtering
        self.total_signals = int(np.sum(df[signal_column] != 0))

        # Create a copy of the original signals for comparison
        original_signals = df[signal_column].copy()

        # Apply RSI filter based on direction
        if direction == "Long":
            # For long positions, only enter when RSI >= threshold
            df.loc[
                (df[signal_column] != 0) & (df[rsi_column] < rsi_threshold),
                signal_column,
            ] = 0
        else:
            # For short positions, only enter when RSI <= (100 - threshold)
            df.loc[
                (df[signal_column] != 0) & (df[rsi_column] > (100 - rsi_threshold)),
                signal_column,
            ] = 0

        # Count filtered signals
        self.filtered_signals = int(
            np.sum(original_signals != 0) - np.sum(df[signal_column] != 0)
        )

        # Track rejection reason
        reason = f"RSI {'below' if direction == 'Long' else 'above'} threshold"
        self._track_rejection(reason, self.filtered_signals)

        self.log(
            f"RSI filter rejected {self.filtered_signals} of {self.total_signals} signals",
            "info",
        )

        # Convert back to polars if needed
        if is_polars:
            return pl.from_pandas(df)
        return df


class VolumeFilter(BaseFilter):
    """Filter signals based on volume thresholds."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the volume filter.

        Args:
            log: Optional logging function
        """
        super().__init__("Volume", log)

    def apply(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply volume filter to signals.

        Args:
            data: DataFrame containing signal data
            config: Configuration dictionary with volume parameters

        Returns:
            DataFrame: Filtered data
        """
        # Extract configuration
        use_volume = config.get("USE_VOLUME_FILTER", False)
        min_volume = config.get("MIN_VOLUME", 0)
        volume_column = config.get("VOLUME_COLUMN", "Volume")
        signal_column = config.get("SIGNAL_COLUMN", "Signal")

        # Skip if volume filtering is disabled or volume column is missing
        if not use_volume or volume_column not in data.columns:
            self.log(
                f"Volume filtering skipped: enabled={use_volume}, column_exists={volume_column in data.columns}",
                "info",
            )
            return data

        self.log(f"Applying volume filter with minimum volume {min_volume}", "info")

        # Convert to pandas for processing
        is_polars = isinstance(data, pl.DataFrame)
        if is_polars:
            df = data.to_pandas()
        else:
            df = data

        # Count signals before filtering
        self.total_signals = int(np.sum(df[signal_column] != 0))

        # Create a copy of the original signals for comparison
        original_signals = df[signal_column].copy()

        # Apply volume filter
        df.loc[
            (df[signal_column] != 0) & (df[volume_column] < min_volume), signal_column
        ] = 0

        # Count filtered signals
        self.filtered_signals = int(
            np.sum(original_signals != 0) - np.sum(df[signal_column] != 0)
        )

        # Track rejection reason
        self._track_rejection("Insufficient volume", self.filtered_signals)

        self.log(
            f"Volume filter rejected {self.filtered_signals} of {self.total_signals} signals",
            "info",
        )

        # Convert back to polars if needed
        if is_polars:
            return pl.from_pandas(df)
        return df


class VolatilityFilter(BaseFilter):
    """Filter signals based on volatility (ATR) thresholds."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the volatility filter.

        Args:
            log: Optional logging function
        """
        super().__init__("Volatility", log)

    def apply(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply volatility filter to signals.

        Args:
            data: DataFrame containing signal data
            config: Configuration dictionary with volatility parameters

        Returns:
            DataFrame: Filtered data
        """
        # Extract configuration
        use_volatility = config.get("USE_VOLATILITY_FILTER", False)
        min_atr = config.get("MIN_ATR", 0)
        max_atr = config.get("MAX_ATR", float("inf"))
        atr_column = config.get("ATR_COLUMN", "ATR")
        signal_column = config.get("SIGNAL_COLUMN", "Signal")

        # Skip if volatility filtering is disabled or ATR column is missing
        if not use_volatility or atr_column not in data.columns:
            self.log(
                f"Volatility filtering skipped: enabled={use_volatility}, column_exists={atr_column in data.columns}",
                "info",
            )
            return data

        self.log(
            f"Applying volatility filter with ATR range {min_atr} to {max_atr}", "info"
        )

        # Convert to pandas for processing
        is_polars = isinstance(data, pl.DataFrame)
        if is_polars:
            df = data.to_pandas()
        else:
            df = data

        # Count signals before filtering
        self.total_signals = int(np.sum(df[signal_column] != 0))

        # Create a copy of the original signals for comparison
        original_signals = df[signal_column].copy()

        # Apply volatility filter
        df.loc[
            (df[signal_column] != 0)
            & ((df[atr_column] < min_atr) | (df[atr_column] > max_atr)),
            signal_column,
        ] = 0

        # Count filtered signals
        self.filtered_signals = int(
            np.sum(original_signals != 0) - np.sum(df[signal_column] != 0)
        )

        # Track rejection reasons
        low_vol_count = int(
            np.sum(
                (original_signals != 0)
                & (df[atr_column] < min_atr)
                & (df[signal_column] == 0)
            )
        )
        high_vol_count = int(
            np.sum(
                (original_signals != 0)
                & (df[atr_column] > max_atr)
                & (df[signal_column] == 0)
            )
        )

        if low_vol_count > 0:
            self._track_rejection("Low volatility", low_vol_count)
        if high_vol_count > 0:
            self._track_rejection("High volatility", high_vol_count)

        self.log(
            f"Volatility filter rejected {self.filtered_signals} of {self.total_signals} signals",
            "info",
        )

        # Convert back to polars if needed
        if is_polars:
            return pl.from_pandas(df)
        return df


class SignalFilterPipeline:
    """Pipeline for applying multiple filters to signals in sequence."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the signal filter pipeline.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging(
                "signal_filter_pipeline", Path("./logs"), "signal_filter_pipeline.log"
            )
        else:
            self.log = log

        # Initialize filters
        self.filters: List[FilterInterface] = []
        self.filter_stats: List[Dict[str, Any]] = []

    def add_filter(self, filter_obj: FilterInterface) -> None:
        """Add a filter to the pipeline.

        Args:
            filter_obj: Filter object implementing FilterInterface
        """
        self.filters.append(filter_obj)
        self.log(f"Added {filter_obj.name} filter to pipeline", "info")

    def apply_filters(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """Apply all filters in the pipeline.

        Args:
            data: DataFrame containing signal data
            config: Configuration dictionary for filters

        Returns:
            DataFrame: Filtered data
        """
        self.log(f"Applying filter pipeline with {len(self.filters)} filters", "info")

        # Reset filter stats
        self.filter_stats = []

        # Apply each filter in sequence
        filtered_data = data
        for filter_obj in self.filters:
            self.log(f"Applying {filter_obj.name} filter", "info")
            filtered_data = filter_obj.apply(filtered_data, config)
            self.filter_stats.append(filter_obj.get_filter_stats())

        self.log("Filter pipeline complete", "info")
        return filtered_data

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the filter pipeline.

        Returns:
            Dict[str, Any]: Statistics about the filter pipeline
        """
        # Calculate overall statistics
        total_signals = (
            self.filter_stats[0]["total_signals"] if self.filter_stats else 0
        )
        remaining_signals = total_signals - sum(
            stat["filtered_signals"] for stat in self.filter_stats
        )

        return {
            "total_filters": len(self.filters),
            "total_signals": total_signals,
            "remaining_signals": remaining_signals,
            "overall_pass_rate": (
                remaining_signals / total_signals if total_signals > 0 else 0.0
            ),
            "filter_stats": self.filter_stats,
        }


# Factory function to create a standard filter pipeline
def create_standard_filter_pipeline(
    log: Optional[Callable[[str, str], None]] = None
) -> SignalFilterPipeline:
    """Create a standard filter pipeline with common filters.

    Args:
        log: Optional logging function

    Returns:
        SignalFilterPipeline: Configured filter pipeline
    """
    pipeline = SignalFilterPipeline(log)

    # Add standard filters
    pipeline.add_filter(RSIFilter(log))
    pipeline.add_filter(VolumeFilter(log))
    pipeline.add_filter(VolatilityFilter(log))

    return pipeline


# Convenience function for filtering signals
def filter_signals(
    data: DataFrame,
    config: Dict[str, Any],
    log: Optional[Callable[[str, str], None]] = None,
    custom_pipeline: Optional[SignalFilterPipeline] | None = None,
) -> Tuple[DataFrame, Dict[str, Any]]:
    """Filter signals using a standard or custom filter pipeline.

    Args:
        data: DataFrame containing signal data
        config: Configuration dictionary for filters
        log: Optional logging function
        custom_pipeline: Optional custom filter pipeline

    Returns:
        Tuple containing:
            - DataFrame: Filtered data
            - Dict[str, Any]: Filter statistics
    """
    # Use provided pipeline or create a standard one
    pipeline = (
        custom_pipeline
        if custom_pipeline is not None
        else create_standard_filter_pipeline(log)
    )

    # Apply filters
    filtered_data = pipeline.apply_filters(data, config)

    # Get statistics
    stats = pipeline.get_pipeline_stats()

    return filtered_data, stats
