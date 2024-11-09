import numpy as np
import pandas as pd
import plotly.graph_objects as go
import vectorbt as vbt

def create_full_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D'
) -> go.Figure:
    """
    Create a full heatmap for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation

    Returns:
        Plotly figure object containing the heatmap
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
    returns.index = pd.MultiIndex.from_tuples(
        [(idx[2], idx[0]) for idx in returns.index],
        names=['slow_window', 'fast_window']
    )
    
    fig = returns.vbt.heatmap(
        symmetric=True,
        trace_kwargs=dict(
            colorscale='Viridis',
            colorbar=dict(title='Total return', tickformat='%'),
            showscale=True
        )
    )
    
    return fig