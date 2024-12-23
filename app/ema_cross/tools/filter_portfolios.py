"""
Portfolio Filtering Module

This module handles the filtering and analysis of portfolio metrics,
creating summaries of extreme values.
"""

import polars as pl
from typing import Dict, Callable, List
from app.tools.export_csv import export_csv, ExportConfig
from app.ema_cross.tools.portfolio_metrics import (
    NUMERIC_METRICS,
    DURATION_METRICS,
    get_metric_rows,
    create_metric_result
)

def _process_metrics(
    df: pl.DataFrame,
    metrics: List[str],
    columns: List[str]
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
            rows = get_metric_rows(df, metric)
            result_rows.extend(create_metric_result(metric, rows, columns))
    return result_rows

def _prepare_result_df(result_rows: List[Dict], config: ExportConfig) -> pl.DataFrame:
    """Prepare and format the result DataFrame.
    
    Args:
        result_rows: List of result dictionaries
        
    Returns:
        Formatted Polars DataFrame
    """
    if not result_rows:
        return pl.DataFrame()
        
    result_df = pl.DataFrame(result_rows)
    
    # Sort portfolios in descending order
    sort_by = config.get('SORT_BY', 'Total Return [%]')
    result_df = result_df.sort(sort_by, descending=True)
    
    # Reorder columns to put Metric Type first
    cols = ['Metric Type'] + [col for col in result_df.columns if col != 'Metric Type']
    return result_df.select(cols)

def filter_portfolios(df: pl.DataFrame, config: ExportConfig, log: Callable) -> pl.DataFrame:
    """Filter and analyze portfolio metrics, creating a summary of extreme values.

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
        result_df = _prepare_result_df(result_rows, config)
        if len(result_df) == 0:
            log("No results generated - returning empty DataFrame", "warning")
            return result_df
            
        # Log configuration details
        log(f"Filtering results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"USE_SMA: {config.get('USE_SMA', False)}")
        log(f"USE_CURRENT: {config.get('USE_CURRENT', False)}")
        
        # Export filtered results
        export_csv(
            data=result_df,
            feature1="ma_cross",
            config=config,
            feature2="portfolios_filtered",
            log=log
        )
        
        print(f"Analysis complete. Total rows in output: {len(result_rows)}")
        return result_df
        
    except Exception as e:
        log(f"Failed to filter portfolios: {e}", "error")
        raise
