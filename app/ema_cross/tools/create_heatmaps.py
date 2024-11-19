import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple
from app.ema_cross.tools.heatmap_calculations import (
    calculate_returns,
    calculate_full_returns,
    create_returns_matrix
)

def create_heatmap_figure(
    matrix: np.ndarray,
    windows: np.ndarray,
    subtitle: str
) -> go.Figure:
    """
    Create a Plotly heatmap figure with consistent styling.

    Args:
        matrix: 2D array of values for the heatmap
        windows: Array of window values for axes
        subtitle: Subtitle for the plot

    Returns:
        Plotly figure object
    """
    return go.Figure(data=go.Heatmap(
        z=matrix,
        x=windows,
        y=windows,
        colorscale='Viridis',
        colorbar=dict(title='Total Return', tickformat='%'),
        hoverongaps=False
    )).update_layout(
        xaxis_title='Short Window',
        yaxis_title='Long Window',
        title=dict(
            text=f'Moving Average Cross Strategy Returns<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        )
    )

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
    matrix = create_returns_matrix(returns, windows, window_combs)
    return create_heatmap_figure(matrix, windows, "Current Signals Only")

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
    matrix = create_returns_matrix(returns, windows)
    return create_heatmap_figure(matrix, windows, "All Signals")
