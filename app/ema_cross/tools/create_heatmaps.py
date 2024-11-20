import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple
from app.ema_cross.tools.heatmap_calculations import (
    calculate_returns,
    calculate_full_returns
)

def create_heatmap_figure(
    returns: pd.Series,
    windows: np.ndarray,
    subtitle: str
) -> go.Figure:
    """
    Create a vectorbt heatmap figure with consistent styling.

    Args:
        returns: Series of returns
        windows: Array of window values for axes
        subtitle: Subtitle for the plot

    Returns:
        Plotly figure object
    """
    # Use vectorbt's heatmap with symmetric=True
    fig = returns.vbt.heatmap(
        x_level='fast_window',
        y_level='slow_window',
        symmetric=True,
        trace_kwargs=dict(
            colorbar=dict(
                title='Total Return',
                tickformat='%'
            )
        )
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Short Window',
        yaxis_title='Long Window',
        title=dict(
            text=f'Moving Average Cross Strategy Returns<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        )
    )
    
    return fig

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
    # Extract windows ensuring correct order (fast_window, slow_window)
    fast_windows = []
    slow_windows = []
    for comb in window_combs:
        fast_windows.append(min(comb))  # Short window is always smaller
        slow_windows.append(max(comb))  # Long window is always larger
    
    returns = calculate_returns(price_data, fast_windows, slow_windows, use_ewm, freq)
    return create_heatmap_figure(returns, windows, "Current Signals Only")

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
    returns = calculate_full_returns(price_data, windows, use_ewm, freq)
    return create_heatmap_figure(returns, windows, "All Signals")
