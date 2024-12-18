import numpy as np
import polars as pl
import pandas as pd
from typing import Dict, Callable

from app.utils import get_filename, get_path
from app.ema_cross.tools.heatmap_figures import create_heatmap_figures

def plot_heatmap(portfolio_data: pl.DataFrame, config: Dict, log: Callable) -> None:
    """
    Plot heatmaps of MA cross strategy performance from portfolio data.
    
    Creates heatmaps showing the performance metrics from pre-calculated portfolio data.
    Uses Polars for data processing.

    Args:
        portfolio_data: Polars DataFrame containing portfolio performance data with columns:
            - metric: str, type of metric (returns, trades, sharpe, or win_rate)
            - value: float, value of the metric
            - fast_window: int, short moving average window
            - slow_window: int, long moving average window
        config: Configuration dictionary containing:
            - TICKER: str, ticker symbol
            - WINDOWS: int, maximum window size
            - USE_CURRENT: bool, whether to show only current signals
        log: Logging function for recording events and errors

    Returns:
        None. Saves the plots to files and displays them.

    Raises:
        Exception: If there's an error during heatmap generation
    """
    log("Starting heatmap generation from portfolio data")
    
    try:
        # Generate windows array
        windows = np.arange(2, config["WINDOWS"])
        log(f"Generated windows array up to {config['WINDOWS']}")
        
        # Convert portfolio data to pandas and prepare Series
        df = portfolio_data.to_pandas()
        
        # Create returns Series
        returns_df = df[df['metric'] == 'returns']
        returns = pd.Series(
            returns_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [returns_df['slow_window'].values, returns_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )
        
        # Create trades Series
        trades_df = df[df['metric'] == 'trades']
        trades = pd.Series(
            trades_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [trades_df['slow_window'].values, trades_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )

        # Create Sharpe Series
        sharpe_df = df[df['metric'] == 'sharpe']
        sharpe = pd.Series(
            sharpe_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [sharpe_df['slow_window'].values, sharpe_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )

        # Create Win Rate Series
        win_rate_df = df[df['metric'] == 'win_rate']
        win_rate = pd.Series(
            win_rate_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [win_rate_df['slow_window'].values, win_rate_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )
        
        if len(returns) == 0 or len(trades) == 0 or len(sharpe) == 0 or len(win_rate) == 0:
            raise ValueError("Portfolio data missing required metrics (returns, trades, sharpe, and/or win_rate)")
        
        # Create heatmap figures
        figures = create_heatmap_figures(
            returns=returns,
            trades=trades,
            sortino=sharpe,  # Keep parameter name as sortino for backwards compatibility
            win_rate=win_rate,
            windows=windows,
            title="Portfolio Performance",
            config=config
        )
        
        # Save and display plots
        png_path = get_path("png", "ema_cross", config, 'heatmap')
        base_filename = get_filename("png", config).replace('.png', '')
        log(f"Saving plots to directory: {png_path}")
        
        for plot_type, fig in figures.items():
            filename = f"{base_filename}_{plot_type}.png"
            full_path = f"{png_path}/{filename}"
            log(f"Saving {plot_type} plot to: {full_path}")
            fig.write_image(full_path)
            log(f"{plot_type.capitalize()} plot saved successfully")
            fig.show()
            log(f"{plot_type.capitalize()} plot displayed")
        
        log("Heatmap generation completed")
        
    except Exception as e:
        log(f"Error generating heatmaps: {str(e)}", "error")
        raise
