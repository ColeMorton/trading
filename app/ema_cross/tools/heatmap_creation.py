import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple, Dict, Callable, Optional
from app.ema_cross.tools.return_calculations import (
    calculate_returns,
    calculate_full_returns
)
from app.ema_cross.tools.heatmap_figures import create_heatmap_figures

def create_current_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    window_combs: List[Tuple[int, int]],
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = '',
    log: Optional[Callable] = None
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
        log: Optional logging function

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
        if log:
            log("No valid window combinations found", "error")
        raise ValueError("No valid window combinations found")
    
    returns, expectancy = calculate_returns(price_data, fast_windows, slow_windows, use_ewm, freq, ticker, log)
    return create_heatmap_figures(returns, expectancy, windows, "Current Signals Only", ticker)

def create_full_heatmap(
    price_data: pd.DataFrame,
    windows: np.ndarray,
    use_ewm: bool,
    freq: str = '1D',
    ticker: str = '',
    log: Optional[Callable] = None
) -> Dict[str, go.Figure]:
    """
    Create full heatmaps for all window combinations using vectorbt.

    Args:
        price_data: Price data DataFrame (Pandas format required for vectorbt)
        windows: Array of window values to test
        use_ewm: Whether to use EMA (True) or SMA (False)
        freq: Frequency for portfolio calculation
        ticker: Ticker symbol for the plots
        log: Optional logging function

    Returns:
        Dictionary containing two Plotly figure objects - one for returns and one for expectancy
    """
    returns, expectancy = calculate_full_returns(price_data, windows, use_ewm, freq, ticker, log)
    return create_heatmap_figures(returns, expectancy, windows, "All Signals", ticker)
