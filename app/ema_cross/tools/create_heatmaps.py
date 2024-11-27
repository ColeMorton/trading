import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple, Dict
from app.ema_cross.tools.heatmap_calculations import (
    calculate_returns,
    calculate_full_returns
)

def create_heatmap_figures(
    returns: pd.Series,
    expectancy: pd.Series,
    windows: np.ndarray,
    subtitle: str,
    ticker: str
) -> Dict[str, go.Figure]:
    """
    Create separate vectorbt heatmap figures for returns and expectancy with consistent styling.
    Makes the heatmaps symmetrical by mirroring values across the diagonal.

    Args:
        returns: Series of returns
        expectancy: Series of expectancy values
        windows: Array of window values for axes
        subtitle: Subtitle for the plots
        ticker: Ticker symbol for the plots

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
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
    
    # Create returns figure
    returns_fig = go.Figure()
    returns_fig.add_trace(go.Heatmap(
        z=returns_heatmap[2:, 2:],  # Slice the heatmap to start at index 2
        x=np.arange(2, max_window + 1),  # Start x axis at 2
        y=np.arange(2, max_window + 1),  # Start y axis at 2
        colorbar=dict(title='Total Return', tickformat='%'),
        zmin=returns_zmin,
        zmax=returns_zmax,
        colorscale='plasma'
    ))
    
    returns_fig.update_layout(
        title=dict(
            text=f'{ticker} - Moving Average Cross Strategy Returns<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,  # Enable auto-sizing
        margin=dict(l=50, r=50, t=100, b=50)  # Adjust margins for better fit
    )
    
    # Create expectancy figure
    expectancy_fig = go.Figure()
    expectancy_fig.add_trace(go.Heatmap(
        z=expectancy_heatmap[2:, 2:],  # Slice the heatmap to start at index 2
        x=np.arange(2, max_window + 1),  # Start x axis at 2
        y=np.arange(2, max_window + 1),  # Start y axis at 2
        colorbar=dict(title='Expectancy'),
        zmin=expectancy_zmin,
        zmax=expectancy_zmax,
        colorscale='plasma'
    ))
    
    expectancy_fig.update_layout(
        title=dict(
            text=f'{ticker} - Moving Average Cross Strategy Expectancy<br><sup>{subtitle}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,  # Enable auto-sizing
        margin=dict(l=50, r=50, t=100, b=50)  # Adjust margins for better fit
    )
    
    return {
        'returns': returns_fig,
        'expectancy': expectancy_fig
    }

def create_current_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    window_combs: List[Tuple[int, int]],
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = ''
) -> Dict[str, go.Figure]:
    """
    Create heatmaps showing only current signal combinations.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values
        window_combs: List of (short, long) window combinations to display
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for the plots

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
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
    return create_heatmap_figures(returns, expectancy, windows, "Current Signals Only", ticker)

def create_full_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = ''
) -> Dict[str, go.Figure]:
    """
    Create full heatmaps for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for the plots

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
    """
    returns, expectancy = calculate_full_returns(price_data, windows, use_ewm, freq)
    return create_heatmap_figures(returns, expectancy, windows, "All Signals", ticker)
