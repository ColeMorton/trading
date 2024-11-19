import polars as pl
from typing import Dict
from app.utils import get_path, get_filename
from app.ema_cross.tools.portfolio_metrics import (
    NUMERIC_METRICS,
    DURATION_METRICS,
    get_metric_rows,
    create_metric_result
)

def filter_portfolios(df: pl.DataFrame, config: Dict) -> pl.DataFrame:
    """
    Filter and analyze portfolio metrics, creating a summary of extreme values.

    Args:
        df: DataFrame containing portfolio data
        config: Configuration dictionary

    Returns:
        DataFrame containing filtered and analyzed portfolio data
    """
    # Check if DataFrame is empty
    if len(df) == 0:
        print("No portfolios to filter - returning empty DataFrame")
        return df
        
    # Initialize result array
    result_rows = []

    # Process numeric metrics
    for metric in NUMERIC_METRICS:
        if metric in df.columns:
            rows = get_metric_rows(df, metric)
            result_rows.extend(create_metric_result(metric, rows, df.columns))

    # Process duration metrics
    for metric in DURATION_METRICS:
        if metric in df.columns:
            rows = get_metric_rows(df, metric)
            result_rows.extend(create_metric_result(metric, rows, df.columns))

    # If no results were generated, return empty DataFrame
    if not result_rows:
        print("No results generated - returning empty DataFrame")
        return pl.DataFrame()

    # Convert results to DataFrame
    result_df = pl.DataFrame(result_rows)

    # Sort portfolios by Total Return [%] in descending order
    if 'Total Return [%]' in result_df.columns:
        result_df = result_df.sort("Total Return [%]", descending=True)

    # Reorder columns to put Metric Type first
    cols = ['Metric Type'] + [col for col in result_df.columns if col != 'Metric Type']
    result_df = result_df.select(cols)

    # Export to CSV
    csv_path = get_path("csv", "ma_cross", config, 'portfolios_filtered')
    csv_filename = get_filename("csv", config)
    result_df.write_csv(csv_path + "/" + csv_filename)

    print(f"Analysis complete. Results written to {csv_path}")
    print(f"Total rows in output: {len(result_rows)}")

    return result_df
