"""
Portfolio Collection Module

This module handles the collection, sorting, and export of portfolios.
It provides centralized functionality for consistent portfolio operations
across the application.
"""
from typing import List, Dict, Any, Union, Callable, Optional
import polars as pl
from app.strategies.ma_cross.config_types import Config

# Define our own error class to avoid circular imports
class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""
    pass

def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    config: Config
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Sort portfolios using consistent logic across the application.
    
    Args:
        portfolios: Either a list of portfolio dictionaries or a Polars DataFrame
        config: Configuration dictionary containing sorting preferences
        
    Returns:
        Sorted portfolios in the same format as input (list or DataFrame)
        
    Note:
        Uses config['SORT_BY'] to determine sort column, defaults to 'Total Return [%]'
    """
    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios
    
    # Sort using consistent logic
    sort_by = config.get('SORT_BY', 'Total Return [%]')
    sorted_df = df.sort(sort_by, descending=True)
    
    # Return in original format
    return sorted_df.to_dicts() if input_is_list else sorted_df

def deduplicate_and_aggregate_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log: Optional[Callable] = None,
    desired_metric_types: Optional[List[str]] = None
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """
    Deduplicate portfolios based on unique strategy configuration and 
    aggregate metric types.
    
    Args:
        portfolios: Portfolio data
        log: Logging function
        desired_metric_types: Optional list of specific Metric Types to keep.
                             If None, keeps all. If provided, filters to only these types.
        
    Returns:
        Deduplicated portfolios with aggregated metric types
    """
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios
    
    # Filter to desired Metric Types if specified
    if desired_metric_types is not None and "Metric Type" in df.columns:
        original_count = len(df)
        df = df.filter(pl.col("Metric Type").is_in(desired_metric_types))
        if log:
            log(f"Filtered to desired Metric Types: {len(df)}/{original_count} rows kept", "info")
    
    # Verify Score column exists (should be calculated by stats_converter)
    if "Score" not in df.columns:
        if log:
            log("Warning: Score column not found in portfolios", "warning")
        # Use Total Return [%] as fallback
        df = df.with_columns(
            pl.col("Total Return [%]").cast(pl.Float64).alias("Score")
        )
    
    # Create unique ID including Signal Window
    # Handle different column naming conventions
    short_window_col = "Short Window" if "Short Window" in df.columns else "SMA_FAST"
    long_window_col = "Long Window" if "Long Window" in df.columns else "SMA_SLOW"
    
    unique_id_components = [
        pl.col("Ticker").cast(pl.Utf8),
        pl.col("Strategy Type").cast(pl.Utf8)
    ]
    
    # Add window columns if they exist
    if short_window_col in df.columns:
        unique_id_components.append(pl.col(short_window_col).cast(pl.Utf8))
    if long_window_col in df.columns:
        unique_id_components.append(pl.col(long_window_col).cast(pl.Utf8))
    
    # Add Signal Window if it exists
    if "Signal Window" in df.columns:
        unique_id_components.append(pl.col("Signal Window").cast(pl.Utf8))
    
    # Create concatenated unique ID
    df = df.with_columns(
        pl.concat_str(unique_id_components, separator="_").alias("unique_id")
    )
    
    # Sort by Score descending
    df = df.sort("Score", descending=True)
    
    # Check if Metric Type column exists
    if "Metric Type" not in df.columns:
        if log:
            log("No Metric Type column found, skipping aggregation", "warning")
        # No deduplication needed if no Metric Type column
        return df.drop("unique_id").to_dicts() if input_is_list else df.drop("unique_id")
    
    # Group by unique_id and aggregate
    agg_exprs = []
    for col in df.columns:
        if col == "Metric Type":
            # Collect all metric types as a list
            agg_exprs.append(pl.col(col).alias(f"{col}_list"))
        elif col != "unique_id":
            # Keep first value (highest score) for other columns
            agg_exprs.append(pl.col(col).first().alias(col))
    
    df_grouped = df.group_by("unique_id").agg(agg_exprs)
    
    # Post-process to sort metric types manually since Polars aggregation is complex
    if "Metric Type_list" in df_grouped.columns:
        # Convert to Python dicts for easier manipulation
        rows = df_grouped.to_dicts()
        
        def get_priority(metric: str) -> int:
            metric = metric.strip()
            if metric.startswith('Most'):
                return 1
            elif metric.startswith('Mean'):
                return 2
            elif metric.startswith('Median'):
                return 3
            elif metric.startswith('Least'):
                return 4
            else:
                return 5
        
        # Process each row
        for row in rows:
            metric_list = row.get("Metric Type_list", [])
            if metric_list:
                sorted_metrics = sorted(metric_list, key=lambda x: (get_priority(x), x))
                row["Metric Type"] = ', '.join(sorted_metrics)
            else:
                row["Metric Type"] = ""
            # Remove the temporary list column
            if "Metric Type_list" in row:
                del row["Metric Type_list"]
        
        # Convert back to DataFrame
        df_grouped = pl.DataFrame(rows)
    
    # Drop the temporary unique_id column
    df_grouped = df_grouped.drop("unique_id")
    
    # Sort by Score again to ensure proper order
    df_grouped = df_grouped.sort("Score", descending=True)
    
    if log:
        log(f"Deduplicated portfolios from {len(df)} to {len(df_grouped)} rows", "info")
    
    return df_grouped.to_dicts() if input_is_list else df_grouped

def export_best_portfolios(
    portfolios: List[Dict[str, Any]],
    config: Config,
    log: callable
) -> bool:
    """Export the best portfolios to a CSV file with deduplication.

    Args:
        portfolios: List of portfolio dictionaries to export
        config: Configuration for the export
        log: Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return False
        
    try:
        # Log configuration for debugging
        log(f"Configuration for export_best_portfolios:", "info")
        required_fields = ["BASE_DIR", "TICKER"]
        for field in required_fields:
            log(f"Field '{field}' present: {field in config}, value: {config.get(field)}", "info")
            
        # Sort by Score instead of Total Return [%]
        original_sort_by = config.get('SORT_BY', 'Total Return [%]')
        config['SORT_BY'] = 'Score'
        
        # Sort portfolios
        sorted_portfolios = sort_portfolios(portfolios, config)
        
        # Define the desired Metric Types to keep (based on NDAQ example)
        desired_metric_types = [
            "Most Total Return [%]",
            "Median Total Trades", 
            "Mean Avg Winning Trade [%]",
            "Most Sharpe Ratio",
            "Most Omega Ratio", 
            "Most Sortino Ratio"
        ]
        
        # Apply deduplication and metric type aggregation
        deduplicated_portfolios = deduplicate_and_aggregate_portfolios(
            sorted_portfolios, log, desired_metric_types
        )
        
        # Restore original sort configuration
        config['SORT_BY'] = original_sort_by
        
        # Import export_portfolios here to avoid circular imports
        if log:
            log("Importing export_portfolios to avoid circular imports", "info")
        try:
            from app.tools.strategy.export_portfolios import export_portfolios
        except ImportError as e:
            log(f"Failed to import export_portfolios due to circular import: {str(e)}", "error")
            return False
        
        export_portfolios(
            portfolios=deduplicated_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log
        )
        
        log(f"Exported {len(deduplicated_portfolios)} unique portfolios sorted by Score")
        return True
        
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False

def combine_strategy_portfolios(
    ema_portfolios: List[Dict[str, Any]],
    sma_portfolios: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combine portfolios from EMA and SMA strategies.

    Args:
        ema_portfolios (List[Dict[str, Any]]): List of EMA strategy portfolios
        sma_portfolios (List[Dict[str, Any]]): List of SMA strategy portfolios

    Returns:
        List[Dict[str, Any]]: Combined list of portfolios with all required columns
    """
    # Ensure all required columns are present in both sets of portfolios
    required_columns = ["Short Window", "Long Window", "Strategy Type"]
    
    for portfolio in ema_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "EMA"
                else:
                    portfolio[col] = None
    
    for portfolio in sma_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "SMA"
                else:
                    portfolio[col] = None
    
    return ema_portfolios + sma_portfolios