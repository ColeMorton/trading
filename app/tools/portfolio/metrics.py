from typing import Any

import polars as pl


# List of numeric metrics
NUMERIC_METRICS = [
    "Total Return [%]",
    "Total Fees Paid",
    "Max Drawdown [%]",
    "Total Trades",
    "Win Rate [%]",
    "Best Trade [%]",
    "Worst Trade [%]",
    "Avg Winning Trade [%]",
    "Avg Losing Trade [%]",
    "Profit Factor",
    "Expectancy",
    "Sharpe Ratio",
    "Calmar Ratio",
    "Omega Ratio",
    "Sortino Ratio",
]

# List of duration metrics
DURATION_METRICS = [
    "Max Drawdown Duration",
    "Avg Winning Trade Duration",
    "Avg Losing Trade Duration",
]


def get_metric_rows(df: pl.DataFrame, column: str) -> list[Any]:
    """
    Get row for metric extremes.

    Args:
        df: DataFrame containing portfolio data
        column: Column name to analyze

    Returns:
        List of rows containing metric extremes
    """
    # Convert string numbers to numeric if needed
    if df[column].dtype == pl.Utf8:
        # Check if this is a duration column that needs special handling
        if column in DURATION_METRICS:
            try:
                # Try to convert duration strings like "1329 days 00:00:00" to numeric
                # days
                df = df.with_columns(
                    pl.col(column)
                    .str.extract(r"(\d+) days")
                    .cast(pl.Float64)
                    .alias(column)
                )
            except Exception:
                # If duration parsing fails, keep as string
                pass
        else:
            try:
                df = df.with_columns(pl.col(column).cast(pl.Float64).alias(column))
            except (pl.ComputeError, pl.SchemaError, pl.InvalidOperationError):
                # Keep as string if conversion fails (e.g., non-numeric values)
                pass

    # Get the row index for max value
    max_idx = df[column].arg_max()
    max_row = df.row(max_idx)

    # Get the row index for min value
    min_idx = df[column].arg_min()
    min_row = df.row(min_idx)

    # For numeric columns, also get mean and median
    if df[column].dtype in [pl.Float64, pl.Int64] or (
        df[column].dtype == pl.Utf8
        and all(
            str(x).replace("-", "").replace(".", "").isdigit()
            for x in df[column]
            if x is not None
        )
    ):
        mean_val = df[column].mean()
        # Find row closest to mean
        mean_idx = (df[column] - mean_val).abs().arg_min()
        mean_row = df.row(mean_idx)

        median_val = df[column].median()
        # Find row closest to median
        median_idx = (df[column] - median_val).abs().arg_min()
        median_row = df.row(median_idx)

        return [max_row, min_row, mean_row, median_row]
    # For non-numeric columns, only return max and min
    return [max_row, min_row]


def create_metric_result(
    metric: str, rows: list[Any], df_columns: list[str]
) -> list[dict[str, Any]]:
    """
    Create result dictionaries for a metric's rows.

    Args:
        metric: Name of the metric
        rows: List of rows containing metric values
        df_columns: List of column names from the original DataFrame

    Returns:
        List of dictionaries containing metric results
    """
    result_rows = []

    if len(rows) == 4:  # Numeric metric with mean/median
        labels = ["Most", "Least", "Mean", "Median"]
    else:  # Non-numeric metric with only max/min
        labels = ["Most", "Least"]

    for label, row in zip(labels, rows, strict=False):
        result_rows.append(
            {
                "Metric Type": f"{label} {metric}",
                **dict(zip(df_columns, row, strict=False)),
            }
        )

    return result_rows
