import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict

def create_heatmap_figures(
    returns: pd.Series,
    expectancy: pd.Series,
    windows: np.ndarray,
    subtitle: str,
    ticker: str,
    use_sma: bool = True
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
        use_sma: Whether to use SMA (True) or EMA (False)

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
    """
    # Create blank heatmap matrices
    max_window = max(windows)
    min_window = min(windows)
    size = len(windows)
    returns_heatmap = np.full((size, size), np.nan)
    expectancy_heatmap = np.full((size, size), np.nan)
    
    # Create window index mapping
    window_to_idx = {w: i for i, w in enumerate(windows)}
    
    # Fill in values and mirror them for symmetry
    for (slow, fast), value in returns.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            returns_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                returns_heatmap[fast_idx, slow_idx] = value
            
    for (slow, fast), value in expectancy.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            expectancy_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                expectancy_heatmap[fast_idx, slow_idx] = value
    
    # Get the actual min and max values from the data (excluding NaN)
    valid_returns = returns_heatmap[~np.isnan(returns_heatmap)]
    returns_zmin = np.min(valid_returns) if len(valid_returns) > 0 else 0
    returns_zmax = np.max(valid_returns) if len(valid_returns) > 0 else 0
    
    valid_expectancy = expectancy_heatmap[~np.isnan(expectancy_heatmap)]
    expectancy_zmin = np.min(valid_expectancy) if len(valid_expectancy) > 0 else 0
    expectancy_zmax = np.max(valid_expectancy) if len(valid_expectancy) > 0 else 0
    
    # Determine MA type for title
    ma_type = "SMA" if use_sma else "EMA"
    
    # Create returns figure
    returns_fig = go.Figure()
    returns_fig.add_trace(go.Heatmap(
        z=returns_heatmap,
        x=windows,  # Use actual window values
        y=windows,  # Use actual window values
        colorbar=dict(title='Total Return', tickformat='%'),
        zmin=returns_zmin,
        zmax=returns_zmax,
        colorscale='plasma'
    ))
    
    returns_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Returns<br><sup>{subtitle}</sup>',
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
        z=expectancy_heatmap,
        x=windows,  # Use actual window values
        y=windows,  # Use actual window values
        colorbar=dict(title='Expectancy'),
        zmin=expectancy_zmin,
        zmax=expectancy_zmax,
        colorscale='plasma'
    ))
    
    expectancy_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Expectancy<br><sup>{subtitle}</sup>',
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
