"""
Normalization Module.

This module provides standardized methods for normalizing metrics and data,
ensuring consistency across the entire application.
"""

from collections.abc import Callable
from typing import Any, TypeVar

import numpy as np
import pandas as pd
import polars as pl

from app.tools.setup_logging import setup_logging


# Type variable for generic functions
T = TypeVar("T", np.ndarray, pd.Series, list[float])


class Normalizer:
    """Class for standardized data normalization."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the Normalizer class.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging("normalizer", "normalizer.log")
        else:
            self.log = log

    def min_max_scale(
        self,
        data: T,
        feature_range: tuple[float, float] = (0, 1),
        clip: bool = True,
    ) -> T:
        """Scale data to a specified range using min-max scaling.

        Args:
            data: Data to normalize (numpy array, pandas Series, or list of floats)
            feature_range: Target range for normalized data (default: 0 to 1)
            clip: Whether to clip values outside the feature range

        Returns:
            Normalized data of the same type as input
        """
        try:
            self.log(f"Applying min-max scaling to range {feature_range}", "debug")

            # Convert to numpy array for processing
            if isinstance(data, pd.Series):
                values = data.to_numpy()
                is_series = True
            elif isinstance(data, list):
                values = np.array(data)
                is_list = True
            else:
                values = data
                is_series = False
                is_list = False

            # Handle empty or single-value arrays
            if len(values) == 0:
                self.log("Empty data provided for normalization", "warning")
                return data

            if len(values) == 1 or np.all(values == values[0]):
                self.log(
                    "Single value or constant data provided for normalization",
                    "warning",
                )
                # Return a constant value at the midpoint of the feature range
                constant_value = (feature_range[0] + feature_range[1]) / 2
                if is_series:
                    return pd.Series([constant_value] * len(values), index=data.index)
                if is_list:
                    return [constant_value] * len(values)
                return np.full_like(values, constant_value)

            # Calculate min and max
            data_min = np.min(values)
            data_max = np.max(values)
            data_range = data_max - data_min

            if data_range == 0:
                self.log("Zero range in data provided for normalization", "warning")
                # Return a constant value at the midpoint of the feature range
                constant_value = (feature_range[0] + feature_range[1]) / 2
                if is_series:
                    return pd.Series([constant_value] * len(values), index=data.index)
                if is_list:
                    return [constant_value] * len(values)
                return np.full_like(values, constant_value)

            # Scale to [0, 1]
            scaled = (values - data_min) / data_range

            # Scale to feature range
            target_range = feature_range[1] - feature_range[0]
            scaled = scaled * target_range + feature_range[0]

            # Clip values if requested
            if clip:
                scaled = np.clip(scaled, feature_range[0], feature_range[1])

            # Return in the same format as input
            if is_series:
                return pd.Series(scaled, index=data.index)
            if is_list:
                return scaled.tolist()
            return scaled
        except Exception as e:
            self.log(f"Error in min_max_scale: {e!s}", "error")
            return data

    def z_score_normalize(
        self,
        data: T,
        clip: bool = False,
        clip_range: tuple[float, float] = (-3, 3),
    ) -> T:
        """Normalize data using z-score (standard score) normalization.

        Args:
            data: Data to normalize (numpy array, pandas Series, or list of floats)
            clip: Whether to clip outliers
            clip_range: Range to clip values to if clip is True

        Returns:
            Normalized data of the same type as input
        """
        try:
            self.log("Applying z-score normalization", "debug")

            # Convert to numpy array for processing
            if isinstance(data, pd.Series):
                values = data.to_numpy()
                is_series = True
            elif isinstance(data, list):
                values = np.array(data)
                is_list = True
            else:
                values = data
                is_series = False
                is_list = False

            # Handle empty or single-value arrays
            if len(values) == 0:
                self.log("Empty data provided for normalization", "warning")
                return data

            if len(values) == 1:
                self.log("Single value provided for normalization", "warning")
                # Return 0 (mean of z-score distribution)
                if is_series:
                    return pd.Series([0.0] * len(values), index=data.index)
                if is_list:
                    return [0.0] * len(values)
                return np.zeros_like(values)

            # Calculate mean and standard deviation
            mean = np.mean(values)
            std = np.std(values)

            if std == 0:
                self.log(
                    "Zero standard deviation in data provided for normalization",
                    "warning",
                )
                # Return 0 (mean of z-score distribution)
                if is_series:
                    return pd.Series([0.0] * len(values), index=data.index)
                if is_list:
                    return [0.0] * len(values)
                return np.zeros_like(values)

            # Calculate z-scores
            z_scores = (values - mean) / std

            # Clip values if requested
            if clip:
                z_scores = np.clip(z_scores, clip_range[0], clip_range[1])

            # Return in the same format as input
            if is_series:
                return pd.Series(z_scores, index=data.index)
            if is_list:
                return z_scores.tolist()
            return z_scores
        except Exception as e:
            self.log(f"Error in z_score_normalize: {e!s}", "error")
            return data

    def robust_scale(
        self,
        data: T,
        quantile_range: tuple[float, float] = (0.25, 0.75),
        clip: bool = False,
        clip_range: tuple[float, float] = (-3, 3),
    ) -> T:
        """Scale data using robust scaling based on quantiles.

        Args:
            data: Data to normalize (numpy array, pandas Series, or list of floats)
            quantile_range: Quantile range to use for scaling
            clip: Whether to clip outliers
            clip_range: Range to clip values to if clip is True

        Returns:
            Normalized data of the same type as input
        """
        try:
            self.log(
                f"Applying robust scaling with quantile range {quantile_range}",
                "debug",
            )

            # Convert to numpy array for processing
            if isinstance(data, pd.Series):
                values = data.to_numpy()
                is_series = True
            elif isinstance(data, list):
                values = np.array(data)
                is_list = True
            else:
                values = data
                is_series = False
                is_list = False

            # Handle empty or single-value arrays
            if len(values) == 0:
                self.log("Empty data provided for normalization", "warning")
                return data

            if len(values) == 1:
                self.log("Single value provided for normalization", "warning")
                # Return 0 (center of robust scale distribution)
                if is_series:
                    return pd.Series([0.0] * len(values), index=data.index)
                if is_list:
                    return [0.0] * len(values)
                return np.zeros_like(values)

            # Calculate quantiles
            q_low, q_high = np.percentile(
                values,
                [quantile_range[0] * 100, quantile_range[1] * 100],
            )
            iqr = q_high - q_low

            if iqr == 0:
                self.log("Zero IQR in data provided for normalization", "warning")
                # Return 0 (center of robust scale distribution)
                if is_series:
                    return pd.Series([0.0] * len(values), index=data.index)
                if is_list:
                    return [0.0] * len(values)
                return np.zeros_like(values)

            # Calculate median
            median = np.median(values)

            # Scale data
            scaled = (values - median) / iqr

            # Clip values if requested
            if clip:
                scaled = np.clip(scaled, clip_range[0], clip_range[1])

            # Return in the same format as input
            if is_series:
                return pd.Series(scaled, index=data.index)
            if is_list:
                return scaled.tolist()
            return scaled
        except Exception as e:
            self.log(f"Error in robust_scale: {e!s}", "error")
            return data

    def normalize_metrics(
        self,
        metrics: dict[str, Any],
        method: str = "min_max",
        feature_range: tuple[float, float] = (0, 1),
    ) -> dict[str, Any]:
        """Normalize a dictionary of metrics.

        Args:
            metrics: Dictionary of metrics to normalize
            method: Normalization method ('min_max', 'z_score', or 'robust')
            feature_range: Target range for min_max normalization

        Returns:
            Dict[str, Any]: Dictionary of normalized metrics
        """
        try:
            self.log(f"Normalizing metrics dictionary using {method} method", "info")

            # Create a copy of the metrics dictionary
            normalized = {}

            # Define metrics that should be normalized
            numeric_metrics = [
                "avg_return",
                "win_rate",
                "profit_factor",
                "sharpe_ratio",
                "sortino_ratio",
                "calmar_ratio",
                "expectancy_per_trade",
                "signal_quality_score",
                "signal_consistency",
                "signal_density",
            ]

            # Normalize each metric
            for key, value in metrics.items():
                # Skip non-numeric values and metrics that shouldn't be normalized
                if not isinstance(value, int | float) or key not in numeric_metrics:
                    normalized[key] = value
                    continue

                # Apply the selected normalization method
                if method == "min_max":
                    normalized[key] = self.min_max_scale([value], feature_range)[0]
                elif method == "z_score":
                    # For single values, z-score doesn't make sense, so use min_max
                    normalized[key] = self.min_max_scale([value], feature_range)[0]
                elif method == "robust":
                    # For single values, robust scaling doesn't make sense, so use
                    # min_max
                    normalized[key] = self.min_max_scale([value], feature_range)[0]
                else:
                    # Unknown method, keep original value
                    normalized[key] = value

            return normalized
        except Exception as e:
            self.log(f"Error normalizing metrics: {e!s}", "error")
            return metrics

    def normalize_dataframe(
        self,
        df: pd.DataFrame | pl.DataFrame,
        columns: list[str],
        method: str = "min_max",
        feature_range: tuple[float, float] = (0, 1),
    ) -> pd.DataFrame | pl.DataFrame:
        """Normalize selected columns in a DataFrame.

        Args:
            df: DataFrame to normalize
            columns: List of column names to normalize
            method: Normalization method ('min_max', 'z_score', or 'robust')
            feature_range: Target range for min_max normalization

        Returns:
            Normalized DataFrame of the same type as input
        """
        try:
            self.log(
                f"Normalizing DataFrame columns {columns} using {method} method",
                "info",
            )

            # Convert to pandas if polars
            is_polars = isinstance(df, pl.DataFrame)
            if is_polars:
                df_pd = df.to_pandas()
            else:
                df_pd = df

            # Create a copy of the DataFrame
            normalized = df_pd.copy()

            # Normalize each column
            for col in columns:
                if col not in df_pd.columns:
                    self.log(f"Column {col} not found in DataFrame", "warning")
                    continue

                # Skip columns with non-numeric data
                if not np.issubdtype(df_pd[col].dtype, np.number):
                    self.log(
                        f"Column {col} is not numeric, skipping normalization",
                        "warning",
                    )
                    continue

                # Apply the selected normalization method
                if method == "min_max":
                    normalized[col] = self.min_max_scale(df_pd[col], feature_range)
                elif method == "z_score":
                    normalized[col] = self.z_score_normalize(df_pd[col])
                elif method == "robust":
                    normalized[col] = self.robust_scale(df_pd[col])
                else:
                    # Unknown method, keep original values
                    self.log(f"Unknown normalization method: {method}", "warning")

            # Convert back to polars if needed
            if is_polars:
                return pl.from_pandas(normalized)
            return normalized
        except Exception as e:
            self.log(f"Error normalizing DataFrame: {e!s}", "error")
            return df


# Convenience functions for backward compatibility


def min_max_normalize(
    data: np.ndarray | pd.Series | list[float],
    feature_range: tuple[float, float] = (0, 1),
    log: Callable | None | None = None,
) -> np.ndarray | pd.Series | list[float]:
    """Normalize data to a specified range using min-max scaling.

    Args:
        data: Data to normalize
        feature_range: Target range for normalized data
        log: Optional logging function

    Returns:
        Normalized data of the same type as input
    """
    normalizer = Normalizer(log)
    return normalizer.min_max_scale(data, feature_range)


def z_score_normalize(
    data: np.ndarray | pd.Series | list[float],
    log: Callable | None | None = None,
) -> np.ndarray | pd.Series | list[float]:
    """Normalize data using z-score (standard score) normalization.

    Args:
        data: Data to normalize
        log: Optional logging function

    Returns:
        Normalized data of the same type as input
    """
    normalizer = Normalizer(log)
    return normalizer.z_score_normalize(data)


def normalize_metrics_dict(
    metrics: dict[str, Any],
    method: str = "min_max",
    feature_range: tuple[float, float] = (0, 1),
    log: Callable | None | None = None,
) -> dict[str, Any]:
    """Normalize a dictionary of metrics.

    Args:
        metrics: Dictionary of metrics to normalize
        method: Normalization method ('min_max', 'z_score', or 'robust')
        feature_range: Target range for min_max normalization
        log: Optional logging function

    Returns:
        Dict[str, Any]: Dictionary of normalized metrics
    """
    normalizer = Normalizer(log)
    return normalizer.normalize_metrics(metrics, method, feature_range)
