"""
Portfolio Filtering Module

This module handles the filtering and analysis of portfolio metrics for the
MACD cross strategy, creating summaries of extreme values.
"""

from typing import Any, Callable, Dict, List

import polars as pl

from app.tools.export_csv import ExportConfig
from app.tools.portfolio.metrics import DURATION_METRICS, NUMERIC_METRICS


def create_metric_result(
    metric: str, row_idx: int, df: pl.DataFrame, label: str
) -> Dict[str, Any]:
    """Create result dictionary for a metric including window parameters.

    Args:
        metric: Name of the metric being processed
        row_idx: Index of the row in the DataFrame
        df: Original DataFrame
        label: Label for the metric (Most, Least, Mean, Median)

    Returns:
        Result dictionary
    """
    # Get the full row from the DataFrame
    row = df.row(row_idx, named=True)

    # Create result with window parameters
    result = {
        "Metric Type": f"{label} {metric}",
        "Short Window": row.get("Short Window", 0),
        "Long Window": row.get("Long Window", 0),
        "Signal Window": row.get("Signal Window", 0),
    }

    # Add remaining columns
    for col in df.columns:
        if col not in ["Metric Type", "Short Window", "Long Window", "Signal Window"]:
            result[col] = row.get(col)

    return result


def _process_metrics(
    df: pl.DataFrame, metrics: List[str], columns: List[str]
) -> List[Dict]:
    """Process a list of metrics and create result rows.

    Args:
        df: DataFrame containing portfolio data
        metrics: List of metrics to process
        columns: DataFrame columns

    Returns:
        List of result dictionaries
    """
    result_rows = []
    for metric in metrics:
        if metric in df.columns:
            # Convert string numbers to numeric if needed
            if df[metric].dtype == pl.Utf8:
                try:
                    df = df.with_columns(pl.col(metric).cast(pl.Float64).alias(metric))
                except (pl.ComputeError, pl.SchemaError):
                    # Keep as string if conversion fails (e.g., non-numeric values)
                    pass

            # Get indices for metric extremes
            max_idx = df[metric].arg_max()
            min_idx = df[metric].arg_min()

            # Create results for max and min
            result_rows.append(create_metric_result(metric, max_idx, df, "Most"))
            result_rows.append(create_metric_result(metric, min_idx, df, "Least"))

            # For numeric columns, also get mean and median
            if df[metric].dtype in [pl.Float64, pl.Int64]:
                mean_val = df[metric].mean()
                mean_idx = (df[metric] - mean_val).abs().arg_min()
                result_rows.append(create_metric_result(metric, mean_idx, df, "Mean"))

                median_val = df[metric].median()
                median_idx = (df[metric] - median_val).abs().arg_min()
                result_rows.append(
                    create_metric_result(metric, median_idx, df, "Median")
                )

    return result_rows


def _prepare_result_df(result_rows: List[Dict]) -> pl.DataFrame:
    """Prepare and format the result DataFrame.

    Args:
        result_rows: List of result dictionaries

    Returns:
        Formatted Polars DataFrame
    """
    if not result_rows:
        return pl.DataFrame()

    result_df = pl.DataFrame(result_rows)

    # Sort portfolios by Total Return [%] in descending order
    if "Total Return [%]" in result_df.columns:
        result_df = result_df.sort("Total Return [%]", descending=True)

    # Reorder columns to put Metric Type and window parameters first
    cols = ["Metric Type", "Short Window", "Long Window", "Signal Window"]
    remaining_cols = [col for col in result_df.columns if col not in cols]
    cols.extend(remaining_cols)

    # Cast window parameters to integers
    for window_col in ["Short Window", "Long Window", "Signal Window"]:
        if window_col in result_df.columns:
            result_df = result_df.with_columns(
                [pl.col(window_col).cast(pl.Int32).alias(window_col)]
            )

    return result_df.select(cols)


def filter_portfolios(
    df: pl.DataFrame, config: ExportConfig, log: Callable
) -> pl.DataFrame:
    """Filter and analyze portfolio metrics for the MACD cross strategy, creating a summary of extreme values.

    This function analyzes portfolios across different MACD parameter combinations (short/long/signal windows)
    and identifies the best performing combinations based on various metrics.

    The filtered portfolios highlight parameter combinations that excel in multiple metrics,
    making them ideal candidates for best portfolio selection. The resulting DataFrame
    is used by the portfolio selection algorithm to identify the most consistent
    and high-performing parameter combinations.

    Args:
        df: DataFrame containing portfolio data
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        DataFrame containing filtered and analyzed portfolio data
    """
    try:
        # Check if DataFrame is empty
        if len(df) == 0:
            log("No portfolios to filter - returning empty DataFrame", "warning")
            return df

        # Process metrics
        result_rows = []
        result_rows.extend(_process_metrics(df, NUMERIC_METRICS, df.columns))
        result_rows.extend(_process_metrics(df, DURATION_METRICS, df.columns))

        # Prepare result DataFrame
        result_df = _prepare_result_df(result_rows)
        if len(result_df) == 0:
            log("No results generated - returning empty DataFrame", "warning")
            return result_df

        # Log configuration details
        log(f"Filtering results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"USE_CURRENT: {config.get('USE_CURRENT', False)}")
        log(
            f"Short Window Range: {config.get('SHORT_WINDOW_START', 8)} to {config.get('SHORT_WINDOW_END', 20)}"
        )
        log(
            f"Long Window Range: {config.get('LONG_WINDOW_START', 13)} to {config.get('LONG_WINDOW_END', 34)}"
        )
        log(
            f"Signal Window Range: {config.get('SIGNAL_WINDOW_START', 5)} to {config.get('SIGNAL_WINDOW_END', 13)}"
        )

        print(f"Analysis complete. Total rows in output: {len(result_rows)}")
        return result_df

    except Exception as e:
        log(f"Failed to filter portfolios: {e}", "error")
        raise
