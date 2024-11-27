import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict

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
