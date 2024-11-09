from typing import Tuple, List
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import vectorbt as vbt

def calculate_returns(
    price_data: pd.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
    use_ewm: bool,
    freq: str = '1D'
) -> pd.Series:
    """
    Calculate returns for given window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        short_windows: List of short window lengths
        long_windows: List of long window lengths
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Series of returns for each window combination
    """
    fast_ma = vbt.MA.run(price_data, list(short_windows), short_name='fast', ewm=use_ewm)
    slow_ma = vbt.MA.run(price_data, list(long_windows), short_name='slow', ewm=use_ewm)

    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    pf_kwargs = dict(size=np.inf, fees=0.001, freq=freq)
    pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)
    
    return pf.total_return()

def create_current_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    window_combs: List[Tuple[int, int]],
    use_ewm: bool,
    freq: str = '1D'
) -> go.Figure:
    """
    Create a heatmap showing only current signal combinations.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values
        window_combs: List of (short, long) window combinations to display
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Plotly figure object containing the heatmap
    """
    short_windows, long_windows = zip(*window_combs)
    returns = calculate_returns(price_data, short_windows, long_windows, use_ewm, freq)
    
    matrix = np.full((len(windows), len(windows)), np.nan)
    for i, (short, long) in enumerate(window_combs):
        long_idx = np.where(windows == long)[0][0]
        short_idx = np.where(windows == short)[0][0]
        matrix[long_idx, short_idx] = returns.iloc[i]
    
    return go.Figure(data=go.Heatmap(
        z=matrix,
        x=windows,
        y=windows,
        colorscale='Viridis',
        colorbar=dict(title='Total return', tickformat='%'),
        hoverongaps=False
    ))