import os
import pandas as pd
from typing import Tuple, Callable, Optional
from app.tools.file_utils import is_file_from_today

def ensure_cache_directory(log: Optional[Callable] = None) -> bool:
    """
    Ensure the cache directory structure exists.
    Creates the directory if it doesn't exist.

    Args:
        log: Optional logging function

    Returns:
        bool: True if directory exists or was created, False if creation failed
    """
    cache_dir = "csv/ma_cross/heatmap_cache"
    try:
        if not os.path.exists(cache_dir):
            if log:
                log(f"Creating cache directory: {cache_dir}")
            os.makedirs(cache_dir, exist_ok=True)
            if log:
                log(f"Cache directory created successfully: {cache_dir}")
        else:
            if log:
                log(f"Cache directory already exists: {cache_dir}")
        return True
    except Exception as e:
        if log:
            log(f"Failed to create cache directory {cache_dir}: {str(e)}", "error")
        return False

def get_cache_path(
    ticker: str,
    use_ewm: bool,
    freq: str,
    log: Optional[Callable] = None
) -> str:
    """
    Get the cache file path for heatmap data.

    Args:
        ticker: Ticker symbol
        use_ewm: Whether EMA or SMA is used
        freq: Data frequency
        log: Optional logging function

    Returns:
        str: Path to cache file
    """
    if not ensure_cache_directory(log):
        if log:
            log("Failed to ensure cache directory exists", "error")
    
    ma_type = 'EMA' if use_ewm else 'SMA'
    cache_path = f"csv/ma_cross/heatmap_cache/{ticker}_{freq}_{ma_type}_heatmap.csv"
    if log:
        log(f"Cache path: {cache_path}")
    return cache_path

def load_cached_data(
    cache_path: str,
    log: Optional[Callable] = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Load cached heatmap data if available.

    Args:
        cache_path: Path to cache file
        log: Optional logging function

    Returns:
        Tuple[pd.Series, pd.Series]: Cached returns and expectancy data
    """
    try:
        if log:
            log(f"Attempting to load cache from: {cache_path}")
        df = pd.read_csv(cache_path)
        # Convert to multi-index series
        index = pd.MultiIndex.from_tuples(
            list(zip(df['slow_window'], df['fast_window'])),
            names=['slow_window', 'fast_window']
        )
        returns = pd.Series(df['returns'].values, index=index)
        expectancy = pd.Series(df['expectancy'].values, index=index)
        if log:
            log(f"Successfully loaded cache from: {cache_path}")
        return returns, expectancy
    except Exception as e:
        if log:
            log(f"Failed to load cache from {cache_path}: {str(e)}", "error")
        return pd.Series(dtype=float), pd.Series(dtype=float)

def save_to_cache(
    returns: pd.Series,
    expectancy: pd.Series,
    cache_path: str,
    log: Optional[Callable] = None
) -> None:
    """
    Save heatmap data to cache.

    Args:
        returns: Returns series
        expectancy: Expectancy series
        cache_path: Path to cache file
        log: Optional logging function
    """
    try:
        # Create directory if it doesn't exist (redundant safety check)
        cache_dir = os.path.dirname(cache_path)
        if not os.path.exists(cache_dir):
            if log:
                log(f"Creating cache directory: {cache_dir}")
            os.makedirs(cache_dir, exist_ok=True)
            if log:
                log(f"Cache directory created successfully: {cache_dir}")
        
        # Create DataFrame from series
        df = pd.DataFrame({
            'slow_window': [idx[0] for idx in returns.index],
            'fast_window': [idx[1] for idx in returns.index],
            'returns': returns.values,
            'expectancy': expectancy.values
        })
        
        if log:
            log(f"Saving cache to: {cache_path}")
        # Save to CSV
        df.to_csv(cache_path, index=False)
        if log:
            log(f"Successfully saved cache to: {cache_path}")
            
    except Exception as e:
        if log:
            log(f"Failed to save cache to {cache_path}: {str(e)}", "error")
