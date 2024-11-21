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
    Makes the heatmap symmetrical by mirroring values across the diagonal.

    Args:
        returns: Series of returns
        windows: Array of window values for axes
        subtitle: Subtitle for the plot

    Returns:
        Plotly figure object
    """
    # Create a blank heatmap matrix
    max_window = max(windows)
    heatmap = np.full((max_window + 1, max_window + 1), np.nan)
    
    # Fill in values and mirror them for symmetry
    for (slow, fast), value in returns.items():
        heatmap[slow, fast] = value
        # Mirror the same value across diagonal (if not on diagonal)
        if slow != fast:
            heatmap[fast, slow] = value  # Mirror the same value
    
    # Get the actual min and max values from the data (excluding NaN)
    valid_data = heatmap[~np.isnan(heatmap)]
    zmin = np.min(valid_data)
    zmax = np.max(valid_data)
    
    # Create the heatmap using plotly, starting from index 2
    fig = go.Figure(data=go.Heatmap(
        z=heatmap[2:, 2:],  # Slice the heatmap to start at index 2
        x=np.arange(2, max_window + 1),  # Start x axis at 2
        y=np.arange(2, max_window + 1),  # Start y axis at 2
        colorbar=dict(title='Total Return', tickformat='%'),
        zmin=zmin,  # Set minimum value from data
        zmax=zmax,  # Set maximum value from data
        colorscale='plasma'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Moving Average Cross Strategy Returns<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Short Window',
        yaxis_title='Long Window'
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
    # Ensure window_combs is a list of tuples
    if isinstance(window_combs, set):
        window_combs = list(window_combs)
    
    # Extract windows maintaining exact combinations
    fast_windows = []
    slow_windows = []
    for short, long in window_combs:
        # Only include combinations where both windows are in the valid range
        if short in windows and long in windows and short < long:
            fast_windows.append(short)
            slow_windows.append(long)
    
    # Only proceed if we have valid combinations
    if not fast_windows or not slow_windows:
        raise ValueError("No valid window combinations found")
    
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
