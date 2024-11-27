import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt
from typing import List, Tuple, Callable, Optional, Dict
from app.tools.file_utils import convert_stats

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

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        fast_windows: List of fast (short) window lengths
        slow_windows: List of slow (long) window lengths
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for portfolio lookup
        log: Optional logging function

    Returns:
        Tuple[pd.Series, pd.Series]: Returns and expectancy for each window combination
    """
    if log:
        log("Calculating returns and expectancy")
    
    stats_list = []
    indices = []
    
    # Process each window combination individually
    for fast, slow in zip(fast_windows, slow_windows):
        # Calculate MAs for this specific combination
        fast_ma = vbt.MA.run(
            price_data['Close'],  # Use only Close price
            window=fast,
            ewm=use_ewm,
            short_name='fast'
        )
        slow_ma = vbt.MA.run(
            price_data['Close'],  # Use only Close price
            window=slow,
            ewm=use_ewm,
            short_name='slow'
        )
        
        # Generate signals for this combination
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)
        
        # Calculate portfolio returns for this combination
        pf = vbt.Portfolio.from_signals(
            price_data['Close'],  # Use only Close price
            entries,
            exits,
            size=np.inf,
            fees=0.001,
            freq=freq
        )
        
        # Get portfolio statistics
        stats = pf.stats()
        # Add window information
        stats['Short Window'] = fast
        stats['Long Window'] = slow
        stats['Use SMA'] = not use_ewm
        if ticker:
            stats['Ticker'] = ticker
        
        # Convert stats using existing utility
        converted_stats = convert_stats(stats)
        stats_list.append(converted_stats)
        indices.append((slow, fast))  # Keep original order (slow, fast)
    
    # Create Series with proper index
    if not stats_list:
        if log:
            log("No results calculated")
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    index = pd.MultiIndex.from_tuples(
        indices,
        names=['slow_window', 'fast_window']
    )
    
    # Extract returns and expectancy
    returns = pd.Series([stats['Total Return [%]'] for stats in stats_list], index=index)
    expectancy = pd.Series([stats['Expectancy'] for stats in stats_list], index=index)
    
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
        ticker: Ticker symbol for portfolio lookup
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
