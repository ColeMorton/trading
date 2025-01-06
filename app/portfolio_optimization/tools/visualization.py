"""Visualization utilities for concurrency analysis."""

from typing import Dict, List, Callable
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.portfolio_optimization.tools.types import StrategyConfig, ConcurrencyStats
from app.portfolio_optimization.tools.stats_visualization import create_stats_annotation
from app.portfolio_optimization.tools.plot_config import STRATEGY_COLORS, get_heatmap_config

def create_strategy_traces(
    data: pl.DataFrame,
    config: StrategyConfig,
    color: str,
    log: Callable[[str, str], None]
) -> List[go.Scatter]:
    """Create price and position traces for a single strategy.

    Args:
        data (pl.DataFrame): Strategy data
        config (StrategyConfig): Strategy configuration
        color (str): Color for position highlighting
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[go.Scatter]: List of traces for the strategy subplot
    """
    try:
        ticker = config['TICKER']
        log(f"Creating traces for {ticker}", "info")
        
        traces = [
            go.Scatter(
                x=data["Date"],
                y=data["Close"],
                name=f"{ticker} Price",
                line=dict(color="black", width=1)
            )
        ]
        
        # Add position highlighting for both long and short positions
        long_positions = data.filter(pl.col("Position") == 1)
        short_positions = data.filter(pl.col("Position") == -1)
        
        log(f"Found {len(long_positions)} long positions and {len(short_positions)} short positions for {ticker}", "info")
        
        # Highlight long positions
        for date, close in zip(long_positions["Date"], long_positions["Close"]):
            traces.append(
                go.Scatter(
                    x=[date, date],
                    y=[0, close],
                    mode='lines',
                    line=dict(color=color, width=1),
                    showlegend=False,
                    hoverinfo='skip'
                )
            )
        
        # Highlight short positions with a different pattern (dashed line)
        for date, close in zip(short_positions["Date"], short_positions["Close"]):
            traces.append(
                go.Scatter(
                    x=[date, date],
                    y=[0, close],
                    mode='lines',
                    line=dict(color=color, width=1, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                )
            )
        
        # Add legend entries for both long and short positions if they exist
        if len(long_positions) > 0:
            traces.append(
                go.Scatter(
                    x=[data["Date"][0]],
                    y=[data["Close"][0]],
                    name=f"{ticker} Long Positions",
                    mode='lines',
                    line=dict(color=color, width=10),
                    showlegend=True
                )
            )
        
        if len(short_positions) > 0:
            traces.append(
                go.Scatter(
                    x=[data["Date"][0]],
                    y=[data["Close"][0]],
                    name=f"{ticker} Short Positions",
                    mode='lines',
                    line=dict(color=color, width=10, dash='dash'),
                    showlegend=True
                )
            )
        
        log(f"Created {len(traces)} traces for {ticker}", "info")
        return traces
        
    except Exception as e:
        log(f"Error creating strategy traces for {config.get('TICKER', 'unknown')}: {str(e)}", "error")
        raise

def plot_concurrency(
    data_list: List[pl.DataFrame],
    stats: ConcurrencyStats,
    config_list: List[StrategyConfig],
    log: Callable[[str, str], None]
) -> go.Figure:
    """Create visualization of concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        stats (ConcurrencyStats): Concurrency statistics
        config_list (List[StrategyConfig]): List of strategy configurations
        log (Callable[[str, str], None]): Logging function

    Returns:
        go.Figure: Plotly figure object containing the visualization

    Raises:
        ValueError: If required columns are missing from dataframes
    """
    try:
        log("Starting concurrency visualization", "info")
        
        # Validate inputs
        if not data_list or not config_list:
            log("Empty data or config list provided", "error")
            raise ValueError("Data and config lists cannot be empty")
            
        if len(data_list) != len(config_list):
            log("Mismatched data and config lists", "error")
            raise ValueError("Number of dataframes must match number of configurations")
        
        required_cols = ["Date", "Close", "Position"]
        for i, df in enumerate(data_list, 1):
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                log(f"Strategy {i} missing required columns: {missing}", "error")
                raise ValueError(f"Missing required columns: {missing}")

        n_strategies = len(data_list)
        log(f"Creating visualization for {n_strategies} strategies", "info")
        
        subplot_titles = [
            f"Price and Positions ({c['TICKER']}) - {c.get('DIRECTION', 'Long')}" 
            for c in config_list
        ] + ["Strategy Concurrency"]
        
        log("Creating subplot layout", "info")
        fig = make_subplots(
            rows=n_strategies + 1,
            cols=1,
            subplot_titles=subplot_titles,
            vertical_spacing=0.05,
            row_heights=[0.8/n_strategies] * n_strategies + [0.2]
        )

        # Add strategy subplots
        log("Adding strategy subplots", "info")
        for i, (data, config) in enumerate(zip(data_list, config_list), 1):
            color = STRATEGY_COLORS[(i-1) % len(STRATEGY_COLORS)]
            log(f"Creating subplot {i}/{n_strategies} for {config['TICKER']}", "info")
            for trace in create_strategy_traces(data, config, color, log):
                fig.add_trace(trace, row=i, col=1)
                
        # Add concurrency heatmap
        log("Creating concurrency heatmap", "info")
        position_arrays = [df["Position"].fill_null(0) for df in data_list]
        active_strategies = sum(abs(pl.Series(arr)) for arr in position_arrays)  # Use abs to count both long and short positions
        heatmap_config = get_heatmap_config()
        fig.add_trace(
            go.Heatmap(
                x=data_list[0]["Date"],
                z=[active_strategies],
                **heatmap_config
            ),
            row=n_strategies + 1,
            col=1
        )

        # Add statistics and update layout
        log("Adding statistics annotation", "info")
        stats.update({
            'start_date': data_list[0]['Date'].min().strftime('%Y-%m-%d'),
            'end_date': data_list[0]['Date'].max().strftime('%Y-%m-%d')
        })
        fig.add_annotation(**create_stats_annotation(stats, log))
        
        log("Updating layout", "info")
        fig.update_layout(
            height=300 * (n_strategies + 1),
            title_text="Multi-Strategy Concurrency Analysis",
            showlegend=True
        )

        # Update axes
        log("Updating axes", "info")
        for i in range(1, n_strategies + 1):
            fig.update_yaxes(title="Price", row=i, col=1)
        fig.update_yaxes(
            showticklabels=False,
            showline=False,
            title=None,
            row=n_strategies + 1,
            col=1
        )

        log("Visualization completed successfully", "info")
        return fig
        
    except Exception as e:
        log(f"Error creating concurrency visualization: {str(e)}", "error")
        raise
