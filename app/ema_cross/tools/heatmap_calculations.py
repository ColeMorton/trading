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
) -> pd.Series:
    """
    Calculate returns for given window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        fast_windows: List of fast (short) window lengths
        slow_windows: List of slow (long) window lengths
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Series of returns for each window combination
    """
    returns_list = []
    indices = []
    
    for fast, slow in zip(fast_windows, slow_windows):
        # Calculate MAs
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
        
        # Generate signals
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)
        
        # Calculate portfolio returns
        pf_kwargs = dict(size=np.inf, fees=0.001, freq=freq)
        pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)
        
        # Store results - handle Series properly
        total_return = pf.total_return()
        if isinstance(total_return, pd.Series):
            returns_list.append(float(total_return.iloc[0]))
        else:
            returns_list.append(float(total_return))
        indices.append((slow, fast))
    
    # Create Series with proper index
    return pd.Series(
        returns_list,
        index=pd.MultiIndex.from_tuples(
            indices,
            names=['slow_window', 'fast_window']
        )
    )

def calculate_full_returns(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D'
) -> pd.Series:
    """
    Calculate returns for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Series of returns for all window combinations
    """
    fast_ma, slow_ma = vbt.MA.run_combs(
        price_data,
        window=windows,
        r=2,
        short_names=['fast', 'slow'],
        ewm=use_ewm
    )
    
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    pf_kwargs = dict(size=np.inf, fees=0.001, freq=freq)
    pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)
    
    returns = pf.total_return()
    # Handle Series properly
    if isinstance(returns, pd.Series):
        returns = returns.apply(lambda x: float(x) if isinstance(x, pd.Series) else float(x))
    
    returns.index = pd.MultiIndex.from_tuples(
        [(idx[2], idx[0]) for idx in returns.index],
        names=['slow_window', 'fast_window']
    )
    
    return returns
