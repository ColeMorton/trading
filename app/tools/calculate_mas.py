import polars as pl
from typing import Callable

def calculate_mas(
        data: pl.DataFrame,
        fast_window: int,
        slow_window: int,
        use_sma: bool,
        log: Callable
    ) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA).
    
    Args:
        data: Price data DataFrame
        fast_window: Fast MA window size
        slow_window: Slow MA window size
        use_sma: If True, use Simple Moving Average, otherwise use Exponential Moving Average
        log: Logging function
        
    Returns:
        DataFrame with MA columns added
    """
    log(f"Calculating {'SMA' if use_sma else 'EMA'} with windows {fast_window}, {slow_window}")
    log(f"Input data shape: {data.shape}")
    
    # Ensure data is sorted by date
    data = data.sort("Date")
    
    # Ensure Close column is properly formatted
    if "Close" not in data.columns:
        raise ValueError("Data must contain a 'Close' column")
    
    # Calculate moving averages
    if use_sma:
        result = data.with_columns([
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=fast_window).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=slow_window).alias("MA_SLOW")
        ])
    else:
        result = data.with_columns([
            pl.col("Close").cast(pl.Float64).ewm_mean(span=fast_window, adjust=False).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).ewm_mean(span=slow_window, adjust=False).alias("MA_SLOW")
        ])
    
    # Count non-null values in MA columns
    valid_fast = result.select(pl.col("MA_FAST").is_not_null()).sum().item()
    valid_slow = result.select(pl.col("MA_SLOW").is_not_null()).sum().item()
    log(f"Valid MA points - Fast: {valid_fast}, Slow: {valid_slow}")
    
    # Verify that we have enough valid MA points
    if valid_slow < 2:
        log(f"Warning: Not enough valid slow MA points ({valid_slow}). Need at least 2 for crossover detection.", "warning")
    
    # Calculate additional MA metrics for analysis
    result = calculate_ma_metrics(result, log)
    
    return result

def calculate_ma_metrics(data: pl.DataFrame, log: Callable) -> pl.DataFrame:
    """
    Calculate additional moving average metrics for analysis.
    
    Args:
        data: DataFrame with MA_FAST and MA_SLOW columns
        log: Logging function
        
    Returns:
        DataFrame with additional MA metrics
    """
    try:
        # Calculate MA difference (fast - slow)
        data = data.with_columns([
            (pl.col("MA_FAST") - pl.col("MA_SLOW")).alias("MA_DIFF")
        ])
        
        # Calculate MA difference percentage
        data = data.with_columns([
            (pl.col("MA_DIFF") / pl.col("MA_SLOW") * 100).alias("MA_DIFF_PCT")
        ])
        
        # Calculate MA crossover points
        data = data.with_columns([
            (pl.col("MA_FAST") > pl.col("MA_SLOW")).alias("FAST_ABOVE_SLOW"),
            (pl.col("MA_FAST") > pl.col("MA_SLOW")).shift(1).alias("PREV_FAST_ABOVE_SLOW")
        ])
        
        # Identify crossover points
        data = data.with_columns([
            (
                (pl.col("FAST_ABOVE_SLOW") & ~pl.col("PREV_FAST_ABOVE_SLOW")) |
                (~pl.col("FAST_ABOVE_SLOW") & pl.col("PREV_FAST_ABOVE_SLOW"))
            ).alias("IS_CROSSOVER")
        ])
        
        # Count crossovers
        crossover_count = data.filter(pl.col("IS_CROSSOVER") == True).height
        log(f"Detected {crossover_count} MA crossovers in the dataset")
        
        return data
    except Exception as e:
        log(f"Error calculating MA metrics: {str(e)}", "error")
        # Return original data if metrics calculation fails
        return data
