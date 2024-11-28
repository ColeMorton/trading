import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict

def create_heatmap_figures(
    returns: pd.Series,
    trades: pd.Series,
    sortino: pd.Series,  # Keep parameter name as sortino for backwards compatibility
    win_rate: pd.Series,
    windows: np.ndarray,
    title: str,
    ticker: str,
    use_sma: bool = True
) -> Dict[str, go.Figure]:
    """
    Create separate heatmap figures for returns, total trades, Sharpe ratio, and win rate with consistent styling.
    Makes the heatmaps symmetrical by mirroring values across the diagonal.

    Args:
        returns: Series with MultiIndex (slow, fast) containing return values
        trades: Series with MultiIndex (slow, fast) containing total trades values
        sortino: Series with MultiIndex (slow, fast) containing Sharpe ratio values
        win_rate: Series with MultiIndex (slow, fast) containing win rate values
        windows: Array of window values for axes
        title: Title/subtitle for the plots
        ticker: Ticker symbol for the plots
        use_sma: Whether to use SMA (True) or EMA (False)

    Returns:
        Dictionary containing four Plotly figure objects - for returns, trades, Sharpe ratio, and win rate
    """
    # Create blank heatmap matrices
    size = len(windows)
    returns_heatmap = np.full((size, size), np.nan)
    trades_heatmap = np.full((size, size), np.nan)
    sharpe_heatmap = np.full((size, size), np.nan)
    win_rate_heatmap = np.full((size, size), np.nan)
    
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
            
    for (slow, fast), value in trades.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            trades_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                trades_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in sortino.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            sharpe_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                sharpe_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in win_rate.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            win_rate_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                win_rate_heatmap[fast_idx, slow_idx] = value
    
    # Get the actual min and max values from the data (excluding NaN)
    valid_returns = returns_heatmap[~np.isnan(returns_heatmap)]
    returns_zmin = np.min(valid_returns) if len(valid_returns) > 0 else 0
    returns_zmax = np.max(valid_returns) if len(valid_returns) > 0 else 0
    
    valid_trades = trades_heatmap[~np.isnan(trades_heatmap)]
    trades_zmin = np.min(valid_trades) if len(valid_trades) > 0 else 0
    trades_zmax = 200  # Set maximum value to 200 for trades heatmap

    valid_sharpe = sharpe_heatmap[~np.isnan(sharpe_heatmap)]
    sharpe_zmin = np.min(valid_sharpe) if len(valid_sharpe) > 0 else 0
    sharpe_zmax = np.max(valid_sharpe) if len(valid_sharpe) > 0 else 0

    valid_win_rate = win_rate_heatmap[~np.isnan(win_rate_heatmap)]
    win_rate_zmin = np.min(valid_win_rate) if len(valid_win_rate) > 0 else 0
    win_rate_zmax = np.max(valid_win_rate) if len(valid_win_rate) > 0 else 0
    
    # Determine MA type for title
    ma_type = "SMA" if use_sma else "EMA"
    
    # Create returns figure
    returns_fig = go.Figure()
    returns_fig.add_trace(go.Heatmap(
        z=returns_heatmap,
        x=windows,
        y=windows,
        colorbar=dict(title='Total Return', tickformat='%'),
        zmin=returns_zmin,
        zmax=returns_zmax,
        colorscale='plasma'
    ))
    
    returns_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Returns<br><sup>{title}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    # Create trades figure
    trades_fig = go.Figure()
    trades_fig.add_trace(go.Heatmap(
        z=trades_heatmap,
        x=windows,
        y=windows,
        colorbar=dict(title='Total Trades'),
        zmin=trades_zmin,
        zmax=trades_zmax,  # Use fixed maximum of 200
        colorscale='plasma'
    ))
    
    trades_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Total Trades<br><sup>{title}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50)
    )

    # Create Sharpe ratio figure
    sharpe_fig = go.Figure()
    sharpe_fig.add_trace(go.Heatmap(
        z=sharpe_heatmap,
        x=windows,
        y=windows,
        colorbar=dict(title='Sharpe Ratio'),
        zmin=sharpe_zmin,
        zmax=sharpe_zmax,
        colorscale='plasma'
    ))
    
    sharpe_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Sharpe Ratio<br><sup>{title}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50)
    )

    # Create Win Rate figure
    win_rate_fig = go.Figure()
    win_rate_fig.add_trace(go.Heatmap(
        z=win_rate_heatmap,
        x=windows,
        y=windows,
        colorbar=dict(title='Win Rate', tickformat='%'),
        zmin=win_rate_zmin,
        zmax=win_rate_zmax,
        colorscale='plasma'
    ))
    
    win_rate_fig.update_layout(
        title=dict(
            text=f'{ticker} - {ma_type} Cross Strategy Win Rate<br><sup>{title}</sup>',
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(title='Long Window'),
        xaxis=dict(title='Short Window'),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return {
        'trades': trades_fig,
        'returns': returns_fig,
        'sortino': sharpe_fig,
        'win_rate': win_rate_fig
    }
