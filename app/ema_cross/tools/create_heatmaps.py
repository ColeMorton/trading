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
    expectancy: pd.Series,
    windows: np.ndarray,
    subtitle: str
) -> go.Figure:
    """
    Create a vectorbt heatmap figure with consistent styling.
    Makes the heatmap symmetrical by mirroring values across the diagonal.
    Creates two heatmaps stacked vertically - returns and expectancy.

    Args:
        returns: Series of returns
        expectancy: Series of expectancy values
        windows: Array of window values for axes
        subtitle: Subtitle for the plot

    Returns:
        Plotly figure object
    """
    # Create blank heatmap matrices
    max_window = max(windows)
    returns_heatmap = np.full((max_window + 1, max_window + 1), np.nan)
    expectancy_heatmap = np.full((max_window + 1, max_window + 1), np.nan)
    
    # Fill in values and mirror them for symmetry
    for (slow, fast), value in returns.items():
        returns_heatmap[slow, fast] = value
        # Mirror the same value across diagonal (if not on diagonal)
        if slow != fast:
            returns_heatmap[fast, slow] = value
            
    for (slow, fast), value in expectancy.items():
        expectancy_heatmap[slow, fast] = value
        # Mirror the same value across diagonal (if not on diagonal)
        if slow != fast:
            expectancy_heatmap[fast, slow] = value
    
    # Get the actual min and max values from the data (excluding NaN)
    valid_returns = returns_heatmap[~np.isnan(returns_heatmap)]
    returns_zmin = np.min(valid_returns)
    returns_zmax = np.max(valid_returns)
    
    valid_expectancy = expectancy_heatmap[~np.isnan(expectancy_heatmap)]
    expectancy_zmin = np.min(valid_expectancy)
    expectancy_zmax = np.max(valid_expectancy)
    
    # Create figure with subplots
    fig = go.Figure()
    
    # Add returns heatmap
    fig.add_trace(go.Heatmap(
        z=returns_heatmap[2:, 2:],  # Slice the heatmap to start at index 2
        x=np.arange(2, max_window + 1),  # Start x axis at 2
        y=np.arange(2, max_window + 1),  # Start y axis at 2
        colorbar=dict(title='Total Return', tickformat='%', y=0.75, len=0.45),
        zmin=returns_zmin,
        zmax=returns_zmax,
        colorscale='plasma',
        yaxis='y'
    ))
    
    # Add expectancy heatmap
    fig.add_trace(go.Heatmap(
        z=expectancy_heatmap[2:, 2:],  # Slice the heatmap to start at index 2
        x=np.arange(2, max_window + 1),  # Start x axis at 2
        y=np.arange(2, max_window + 1),  # Start y axis at 2
        colorbar=dict(title='Expectancy', y=0.25, len=0.45),
        zmin=expectancy_zmin,
        zmax=expectancy_zmax,
        colorscale='plasma',
        yaxis='y2'
    ))
    
    # Update layout to create two vertically stacked plots
    fig.update_layout(
        title=dict(
            text=f'Moving Average Cross Strategy Analysis<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(
            title='Long Window',
            domain=[0.55, 1]
        ),
        yaxis2=dict(
            title='Long Window',
            domain=[0, 0.45]
        ),
        xaxis=dict(
            title='Short Window',
            domain=[0.1, 0.9]
        ),
        xaxis2=dict(
            title='Short Window',
            domain=[0.1, 0.9],
            anchor='y2'
        ),
        height=1280  # Increase height to accommodate both heatmaps
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
    
    returns, expectancy = calculate_returns(price_data, fast_windows, slow_windows, use_ewm, freq)
    return create_heatmap_figure(returns, expectancy, windows, "Current Signals Only")

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
    returns, expectancy = calculate_full_returns(price_data, windows, use_ewm, freq)
    return create_heatmap_figure(returns, expectancy, windows, "All Signals")
