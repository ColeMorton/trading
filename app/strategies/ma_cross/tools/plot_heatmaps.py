import numpy as np
import polars as pl
import pandas as pd
from typing import Dict, Callable

from app.utils import get_filename, get_path
from app.strategies.ma_cross.tools.heatmap_figures import create_heatmap_figures

def plot_heatmap(portfolio_data: pl.DataFrame, config: Dict, log: Callable) -> None:
    """
    Plot heatmaps of MA cross strategy performance from portfolio data.
    
    Creates heatmaps showing the performance metrics from pre-calculated portfolio data.
    Uses Polars for data processing.

    Args:
        portfolio_data: Polars DataFrame containing portfolio performance data with columns:
            - metric: str, type of metric (trades, profit_factor, expectancy, win_rate, sortino, score)
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
        
        # Create profit_factor Series
        profit_factor_df = df[df['metric'] == 'profit_factor']
        profit_factor = pd.Series(
            profit_factor_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [profit_factor_df['slow_window'].values, profit_factor_df['fast_window'].values],
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

        # Create Sortino Series
        sortino_df = df[df['metric'] == 'sortino']
        sortino = pd.Series(
            sortino_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [sortino_df['slow_window'].values, sortino_df['fast_window'].values],
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
        
        # Create Expectancy Series
        expectancy_df = df[df['metric'] == 'expectancy']
        expectancy = pd.Series(
            expectancy_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [expectancy_df['slow_window'].values, expectancy_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )
        
        # Create Score Series
        score_df = df[df['metric'] == 'score']
        score = pd.Series(
            score_df['value'].values,
            index=pd.MultiIndex.from_arrays(
                [score_df['slow_window'].values, score_df['fast_window'].values],
                names=['slow', 'fast']
            )
        )
        
        # Check if required metrics are present
        if len(profit_factor) == 0 or len(trades) == 0 or len(sortino) == 0 or len(win_rate) == 0:
            raise ValueError("Portfolio data missing required metrics (profit_factor, trades, sortino, and/or win_rate)")
            
        # Log the number of entries for each metric
        log(f"Metric counts - Profit Factor: {len(profit_factor)}, Trades: {len(trades)}, Sortino: {len(sortino)}, Win Rate: {len(win_rate)}, Expectancy: {len(expectancy)}, Score: {len(score)}")
        
        # Create heatmap figures
        figures = create_heatmap_figures(
            profit_factor=profit_factor,
            trades=trades,
            sortino=sortino,
            win_rate=win_rate,
            expectancy=expectancy,
            score=score,
            windows=windows,
            title="Portfolio Performance",
            config=config
        )
        
        # Save and display plots
        png_path = get_path("png", "ma_cross", config, 'heatmap')
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
