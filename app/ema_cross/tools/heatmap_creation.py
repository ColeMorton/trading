import numpy as np
import pandas as pd
import polars as pl
import plotly.graph_objects as go
from typing import List, Tuple, Dict, Callable, Optional
from app.ema_cross.tools.heatmap_figures import create_heatmap_figures

def create_current_heatmap(
    portfolio_data: pl.DataFrame,
    windows: np.ndarray,
    window_combs: List[Tuple[int, int]],
    use_ewm: bool,
    ticker: str = '',
    log: Optional[Callable] = None
) -> Dict[str, go.Figure]:
    """
    Create heatmaps showing only current signal combinations using pre-calculated portfolio data.

    Args:
        portfolio_data: Portfolio data DataFrame containing performance metrics
        windows: Array of window values
        window_combs: List of (short, long) window combinations to display
        use_ewm: Whether EMA (True) or SMA (False) was used
        ticker: Ticker symbol for the plots
        log: Optional logging function

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
    """
    # Ensure window_combs is a list of tuples
    if isinstance(window_combs, set):
        window_combs = list(window_combs)
    
    # Filter portfolio data for specified window combinations
    filtered_data = portfolio_data.filter(
        pl.col('Short Window').is_in([w[0] for w in window_combs]) &
        pl.col('Long Window').is_in([w[1] for w in window_combs])
    )
    
    # Only proceed if we have valid combinations
    if len(filtered_data) == 0:
        if log:
            log("No valid window combinations found", "error")
        raise ValueError("No valid window combinations found")
    
    # Convert to pandas for heatmap creation
    returns = pd.Series(
        filtered_data['Total Return [%]'].to_list(),
        index=pd.MultiIndex.from_tuples(
            list(zip(filtered_data['Long Window'].to_list(), filtered_data['Short Window'].to_list())),
            names=['slow_window', 'fast_window']
        )
    )
    
    expectancy = pd.Series(
        filtered_data['Expectancy'].to_list(),
        index=returns.index
    )
    
    return create_heatmap_figures(returns, expectancy, windows, "Current Signals Only", ticker, use_sma=not use_ewm)

def create_full_heatmap(
    portfolio_data: pl.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    ticker: str = '',
    log: Optional[Callable] = None
) -> Dict[str, go.Figure]:
    """
    Create full heatmaps for all window combinations using pre-calculated portfolio data.

    Args:
        portfolio_data: Portfolio data DataFrame containing performance metrics
        windows: Array of window values
        use_ewm: Whether EMA (True) or SMA (False) was used
        ticker: Ticker symbol for the plots
        log: Optional logging function

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
    """
    # Convert to pandas for heatmap creation
    returns = pd.Series(
        portfolio_data['Total Return [%]'].to_list(),
        index=pd.MultiIndex.from_tuples(
            list(zip(portfolio_data['Long Window'].to_list(), portfolio_data['Short Window'].to_list())),
            names=['slow_window', 'fast_window']
        )
    )
    
    expectancy = pd.Series(
        portfolio_data['Expectancy'].to_list(),
        index=returns.index
    )
    
    return create_heatmap_figures(returns, expectancy, windows, "All Signals", ticker, use_sma=not use_ewm)
