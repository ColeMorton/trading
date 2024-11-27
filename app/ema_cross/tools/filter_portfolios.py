import polars as pl
import os
from datetime import datetime
from typing import Dict, Callable
from app.ema_cross.tools.portfolio_metrics import (
    NUMERIC_METRICS,
    DURATION_METRICS,
    get_metric_rows,
    create_metric_result
)

def filter_portfolios(df: pl.DataFrame, config: Dict, log: Callable) -> pl.DataFrame:
    """
    Filter and analyze portfolio metrics, creating a summary of extreme values.

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
            log("No results generated - returning empty DataFrame", "warning")
            return pl.DataFrame()

        # Convert results to DataFrame
        result_df = pl.DataFrame(result_rows)

        # Sort portfolios by Total Return [%] in descending order
        if 'Total Return [%]' in result_df.columns:
            result_df = result_df.sort("Total Return [%]", descending=True)

        # Reorder columns to put Metric Type first
        cols = ['Metric Type'] + [col for col in result_df.columns if col != 'Metric Type']
        result_df = result_df.select(cols)

        # Get base directory from config
        base_dir = config.get('BASE_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
        
        # Construct base path
        portfolios_dir = os.path.join(base_dir, 'csv', 'ma_cross', 'portfolios_filtered')
        
        # If USE_CURRENT is True, add date subdirectory
        if config.get("USE_CURRENT", False):
            today = datetime.now().strftime("%Y%m%d")
            portfolios_dir = os.path.join(portfolios_dir, today)
        
        # Ensure directory exists
        os.makedirs(portfolios_dir, exist_ok=True)
        
        # Construct filename
        ticker = config.get("TICKER", "")
        use_hourly = config.get("USE_HOURLY", False)
        use_sma = config.get("USE_SMA", False)
        
        filename = f"{ticker}_{'H' if use_hourly else 'D'}_{'SMA' if use_sma else 'EMA'}.csv"
        full_path = os.path.join(portfolios_dir, filename)
        
        # Log configuration details
        log(f"Filtering results for {ticker}")
        log(f"USE_HOURLY: {use_hourly}")
        log(f"USE_SMA: {use_sma}")
        log(f"USE_CURRENT: {config.get('USE_CURRENT', False)}")
        log(f"Saving to: {full_path}")
        
        # Save file
        result_df.write_csv(full_path)
        
        log(f"Filtered results exported successfully")
        print(f"Analysis complete. Results written to {portfolios_dir}")
        print(f"Total rows in output: {len(result_rows)}")

        return result_df
        
    except Exception as e:
        log(f"Failed to filter portfolios: {e}", "error")
        raise
