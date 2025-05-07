"""
Portfolio Filtering Module

This module provides utilities for filtering portfolios based on various criteria.
"""
from typing import List, Dict, Any, Union, Optional
import math
import polars as pl

def filter_invalid_metrics(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log = None
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
    
    # Create filters for each invalid metric condition
    filters = []
    
    # Filter out NaN Score
    if "Score" in df.columns:
        filters.append(~pl.col("Score").is_nan())
    
    # Filter out inf Profit Factor
    if "Profit Factor" in df.columns:
        filters.append(~pl.col("Profit Factor").is_infinite())

    # Filter out NaN Avg Losing Trade [%]
    if "Avg Losing Trade [%]" in df.columns:
        filters.append(~pl.col("Avg Losing Trade [%]").is_nan())
    
    # Filter out NaN Expectancy per Trade
    if "Expectancy per Trade" in df.columns:
        filters.append(~pl.col("Expectancy per Trade").is_nan())
    
    # Apply all filters if any exist
    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        
        filtered_df = df.filter(combined_filter)
    else:
        filtered_df = df
    
    # Log the filtering results
    if log:
        filtered_count = original_count - len(filtered_df)
        if filtered_count > 0:
            # Count specific invalid metrics
            nan_score_count = 0
            inf_profit_factor_count = 0
            nan_expectancy_count = 0
            nan_avg_loss_count = 0
            
            if "Score" in df.columns:
                nan_score_count = df.filter(pl.col("Score").is_nan()).height
                
            if "Profit Factor" in df.columns:
                inf_profit_factor_count = df.filter(pl.col("Profit Factor").is_infinite()).height
                
            if "Expectancy per Trade" in df.columns:
                nan_expectancy_count = df.filter(pl.col("Expectancy per Trade").is_nan()).height
                
            if "Avg Losing Trade [%]" in df.columns:
                nan_avg_loss_count = df.filter(pl.col("Avg Losing Trade [%]").is_nan()).height
            
            log(f"Filtered out {filtered_count} portfolios with invalid metrics:", "info")
            log(f"  - NaN Score: {nan_score_count}", "info")
            log(f"  - inf Profit Factor: {inf_profit_factor_count}", "info")
            log(f"  - NaN Expectancy per Trade: {nan_expectancy_count}", "info")
            log(f"  - NaN Avg Losing Trade [%]: {nan_avg_loss_count}", "info")
            log(f"Remaining portfolios: {len(filtered_df)}", "info")
    
    # Return in original format
    return filtered_df.to_dicts() if input_is_list else filtered_df

def check_invalid_metrics(stats: Dict[str, Any], log = None) -> Optional[Dict[str, Any]]:
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
    if 'Score' in stats and (
        stats['Score'] == 'NaN' or
        (isinstance(stats['Score'], float) and math.isnan(stats['Score']))
    ):
        if log:
            log(f"Invalid metric: Score is NaN", "info")
        return None
        
    # Check for inf Profit Factor
    if 'Profit Factor' in stats and (
        stats['Profit Factor'] == 'inf' or
        stats['Profit Factor'] == float('inf')
    ):
        if log:
            log(f"Invalid metric: Profit Factor is inf", "info")
        return None
        
    # Check for NaN Expectancy per Trade
    if 'Expectancy per Trade' in stats and (
        stats['Expectancy per Trade'] == 'NaN' or
        (isinstance(stats['Expectancy per Trade'], float) and math.isnan(stats['Expectancy per Trade']))
    ):
        if log:
            log(f"Invalid metric: Expectancy per Trade is NaN", "info")
        return None
        
    # Check for NaN Avg Losing Trade [%]
    if 'Avg Losing Trade [%]' in stats and (
        stats['Avg Losing Trade [%]'] == 'NaN' or
        (isinstance(stats['Avg Losing Trade [%]'], float) and math.isnan(stats['Avg Losing Trade [%]']))
    ):
        if log:
            log(f"Invalid metric: Avg Losing Trade [%] is NaN", "info")
        return None
        
    # All metrics are valid
    return stats