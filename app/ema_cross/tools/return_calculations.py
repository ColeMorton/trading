import os
import numpy as np
import pandas as pd
import vectorbt as vbt
from typing import List, Tuple, Callable, Optional
from app.ema_cross.tools.cache_management import (
    get_cache_path,
    load_cached_data,
    save_to_cache,
    is_file_from_today
)

def calculate_returns(
    price_data: pd.DataFrame,
    fast_windows: List[int],
    slow_windows: List[int],
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = '',
    log: Optional[Callable] = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate returns for given window combinations using vectorbt.
    Uses caching to improve performance.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        fast_windows: List of fast (short) window lengths
        slow_windows: List of slow (long) window lengths
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for caching
        log: Optional logging function

    Returns:
        Tuple[pd.Series, pd.Series]: Returns and expectancy for each window combination
    """
    if ticker:
        cache_path = get_cache_path(ticker, use_ewm, freq, log)
        
        # Check if cache exists and is from today (for daily data)
        if os.path.exists(cache_path):
            if log:
                log(f"Found existing cache: {cache_path}")
            if freq != '1D' or is_file_from_today(cache_path):
                if log:
                    log("Cache is valid, attempting to load")
                cached_returns, cached_expectancy = load_cached_data(cache_path, log)
                if not cached_returns.empty and not cached_expectancy.empty:
                    if log:
                        log("Successfully loaded data from cache")
                    return cached_returns, cached_expectancy
            elif log:
                log("Cache is outdated (not from today)")
        elif log:
            log("No existing cache found")

    if log:
        log("Calculating returns and expectancy")
    
    returns_list = []
    expectancy_list = []
    indices = []
    
    # Process each window combination individually
    for fast, slow in zip(fast_windows, slow_windows):
        # Calculate MAs for this specific combination
        fast_ma = vbt.MA.run(
            price_data,
            window=fast,
            ewm=use_ewm,
            short_name='fast'
        )
        slow_ma = vbt.MA.run(
            price_data,
            window=slow,
            ewm=use_ewm,
            short_name='slow'
        )
        
        # Generate signals for this combination
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)
        
        # Calculate portfolio returns for this combination
        pf = vbt.Portfolio.from_signals(
            price_data,
            entries,
            exits,
            size=np.inf,
            fees=0.001,
            freq=freq
        )
        
        # Store results
        total_return = pf.total_return()
        if isinstance(total_return, pd.Series):
            returns_list.append(float(total_return.iloc[0]))
        else:
            returns_list.append(float(total_return))

        # Store expectancy
        expectancy = pf.trades.expectancy()
        if isinstance(expectancy, pd.Series):
            expectancy_list.append(float(expectancy.iloc[0]))
        else:
            expectancy_list.append(float(expectancy))

        indices.append((slow, fast))  # Keep original order (slow, fast)
    
    # Create Series with proper index
    if not returns_list:
        if log:
            log("No results to cache")
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    index = pd.MultiIndex.from_tuples(
        indices,
        names=['slow_window', 'fast_window']
    )
    
    returns = pd.Series(returns_list, index=index)
    expectancy = pd.Series(expectancy_list, index=index)
    
    # Cache the results if ticker is provided
    if ticker:
        if log:
            log("Caching calculation results")
        save_to_cache(returns, expectancy, cache_path, log)
    
    return returns, expectancy

def calculate_full_returns(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = '',
    log: Optional[Callable] = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate returns for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for caching
        log: Optional logging function

    Returns:
        Tuple[pd.Series, pd.Series]: Returns and expectancy for all window combinations
    """
    # Generate all valid combinations where fast < slow
    fast_windows = []
    slow_windows = []
    for fast in windows:
        for slow in windows:
            if fast < slow:
                fast_windows.append(fast)
                slow_windows.append(slow)
    
    return calculate_returns(price_data, fast_windows, slow_windows, use_ewm, freq, ticker, log)
