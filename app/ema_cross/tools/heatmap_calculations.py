import numpy as np
import pandas as pd
import vectorbt as vbt
from typing import List, Tuple

def calculate_returns(
    price_data: pd.DataFrame,
    fast_windows: List[int],
    slow_windows: List[int],
    use_ewm: bool,
    freq: str = '1D'
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate returns for given window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        fast_windows: List of fast (short) window lengths
        slow_windows: List of slow (long) window lengths
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Tuple[pd.Series, pd.Series]: Returns and expectancy for each window combination
    """
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
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    index = pd.MultiIndex.from_tuples(
        indices,
        names=['slow_window', 'fast_window']
    )
    
    return (
        pd.Series(returns_list, index=index),
        pd.Series(expectancy_list, index=index)
    )

def calculate_full_returns(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D'
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate returns for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

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
    
    return calculate_returns(price_data, fast_windows, slow_windows, use_ewm, freq)
