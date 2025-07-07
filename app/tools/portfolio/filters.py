"""
Portfolio Filtering Module

This module provides utilities for filtering portfolios based on various criteria.
"""

import math
from typing import Any, Dict, List, Optional, Union

import polars as pl


def filter_invalid_metrics(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame], log=None
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Filter out portfolios with invalid metric values.

    Removes portfolios where any of the following is true:
    - Score = NaN
    - Profit Factor = inf
    - Expectancy per Trade = NaN
    - Avg Losing Trade [%] = NaN

    Args:
        portfolios: List of portfolio dictionaries or Polars DataFrame
        log: Optional logging function

    Returns:
        Filtered portfolios in the same format as input (list or DataFrame)
    """
    if portfolios is None:
        return None

    if isinstance(portfolios, list) and len(portfolios) == 0:
        return []

    if isinstance(portfolios, pl.DataFrame) and len(portfolios) == 0:
        return pl.DataFrame()

    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    original_count = len(df)

    # Note: Filters are now applied directly below to avoid Polars implementation errors

    # Use pandas fallback to avoid Polars implementation errors
    try:
        import pandas as pd

        # Convert to pandas for safer filtering operations
        pandas_df = df.to_pandas()
        original_pandas_count = len(pandas_df)

        # Apply filters using pandas (more robust)
        if "Score" in pandas_df.columns:
            pandas_df = pandas_df[
                pandas_df["Score"].notna()
                & pandas_df["Score"]
                .replace([float("inf"), float("-inf")], float("nan"))
                .notna()
            ]

        if "Profit Factor" in pandas_df.columns:
            pandas_df = pandas_df[
                pandas_df["Profit Factor"].notna()
                & pandas_df["Profit Factor"]
                .replace([float("inf"), float("-inf")], float("nan"))
                .notna()
            ]

        if "Avg Losing Trade [%]" in pandas_df.columns:
            pandas_df = pandas_df[
                pandas_df["Avg Losing Trade [%]"].notna()
                & pandas_df["Avg Losing Trade [%]"]
                .replace([float("inf"), float("-inf")], float("nan"))
                .notna()
            ]

        if "Expectancy per Trade" in pandas_df.columns:
            pandas_df = pandas_df[
                pandas_df["Expectancy per Trade"].notna()
                & pandas_df["Expectancy per Trade"]
                .replace([float("inf"), float("-inf")], float("nan"))
                .notna()
            ]

        # Convert back to Polars
        filtered_df = pl.from_pandas(pandas_df)

        if log:
            filtered_count = original_pandas_count - len(pandas_df)
            if filtered_count > 0:
                log(
                    f"Using pandas fallback: Filtered out {filtered_count} portfolios with invalid metrics",
                    "info",
                )

    except Exception as e:
        if log:
            log(
                f"Warning: Pandas fallback filtering failed, returning original data: {e}",
                "warning",
            )
        filtered_df = df

    # Log final filtering results
    if log:
        filtered_count = original_count - len(filtered_df)
        if filtered_count > 0:
            log(
                f"Final result: Filtered out {filtered_count} portfolios with invalid metrics",
                "info",
            )
        log(f"Remaining portfolios: {len(filtered_df)}", "info")

    # Return in original format
    return filtered_df.to_dicts() if input_is_list else filtered_df


def check_invalid_metrics(stats: Dict[str, Any], log=None) -> Optional[Dict[str, Any]]:
    """Check if portfolio stats have invalid metrics.

    Checks if any of the following is true:
    - Score = NaN
    - Profit Factor = inf
    - Expectancy per Trade = NaN
    - Avg Losing Trade [%] = NaN

    Args:
        stats: Dictionary containing portfolio statistics
        log: Optional logging function

    Returns:
        The original stats dictionary if all metrics are valid, None if any metric is invalid
    """
    if not stats:
        return None

    # Check for NaN Score
    if "Score" in stats and (
        stats["Score"] == "NaN"
        or (isinstance(stats["Score"], float) and math.isnan(stats["Score"]))
    ):
        if log:
            log("Invalid metric: Score is NaN", "info")
        return None

    # Check for inf Profit Factor
    if "Profit Factor" in stats and (
        stats["Profit Factor"] == "inf" or stats["Profit Factor"] == float("inf")
    ):
        if log:
            log("Invalid metric: Profit Factor is inf", "info")
        return None

    # Check for NaN Expectancy per Trade
    if "Expectancy per Trade" in stats and (
        stats["Expectancy per Trade"] == "NaN"
        or (
            isinstance(stats["Expectancy per Trade"], float)
            and math.isnan(stats["Expectancy per Trade"])
        )
    ):
        if log:
            log("Invalid metric: Expectancy per Trade is NaN", "info")
        return None

    # Check for NaN Avg Losing Trade [%]
    if "Avg Losing Trade [%]" in stats and (
        stats["Avg Losing Trade [%]"] == "NaN"
        or (
            isinstance(stats["Avg Losing Trade [%]"], float)
            and math.isnan(stats["Avg Losing Trade [%]"])
        )
    ):
        if log:
            log("Invalid metric: Avg Losing Trade [%] is NaN", "info")
        return None

    # All metrics are valid
    return stats
