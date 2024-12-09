"""Visualization utilities for concurrency analysis."""

from typing import Dict, List
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.concurrency.tools.types import StrategyConfig, ConcurrencyStats
from app.concurrency.tools.stats_visualization import create_stats_annotation

def create_strategy_subplot(
    data: pl.DataFrame,
    config: StrategyConfig,
    color: str,
    row: int
) -> List[go.Scatter]:
    """Create price and position traces for a single strategy.

    Args:
        data (pl.DataFrame): Strategy data
        config (StrategyConfig): Strategy configuration
        color (str): Color for position highlighting
        row (int): Subplot row number

    Returns:
        List[go.Scatter]: List of traces for the strategy subplot
    """
    traces = []
    
    # Base price line
    traces.append(
        go.Scatter(
            x=data["Date"],
            y=data["Close"],
            name=f"{config['TICKER']} Price",
            line=dict(color="black", width=1)
        )
    )

    # Position highlighting
    for j in range(len(data)):
        if data["Position"][j] == 1:
            traces.append(
                go.Scatter(
                    x=[data["Date"][j], data["Date"][j]],
                    y=[0, data["Close"][j]],
                    mode='lines',
                    line=dict(color=color, width=1),
                    showlegend=False,
                    hoverinfo='skip'
                )
            )

    # Legend entry for positions
    traces.append(
        go.Scatter(
            x=[data["Date"][0]],
            y=[data["Close"][0]],
            name=f"{config['TICKER']} Positions",
            mode='lines',
            line=dict(color=color, width=10),
            showlegend=True
        )
    )

    return traces

def create_concurrency_heatmap(
    data_list: List[pl.DataFrame],
    position_arrays: List[pl.Series],
    n_strategies: int
) -> go.Heatmap:
    """Create heatmap showing concurrent strategies over time.

    Args:
        data_list (List[pl.DataFrame]): List of strategy data
        position_arrays (List[pl.Series]): List of position arrays
        n_strategies (int): Number of strategies being analyzed

    Returns:
        go.Heatmap: Concurrency heatmap trace
    """
    active_strategies = sum(position_arrays)
    
    # Calculate colorbar position to align with last subplot
    # The last subplot takes up 20% of the total height
    # Position the colorbar in the center of the last subplot
    y_position = 0.08  # Slightly lower than previous value
    colorbar_len = 0.18  # Slightly larger to match subplot height
    
    return go.Heatmap(
        x=data_list[0]["Date"],
        z=[active_strategies],
        colorscale='ice',
        showscale=True,
        name="Active Strategies",
        colorbar=dict(
            len=colorbar_len,      # Length of colorbar relative to plot height
            y=y_position,          # Y-position of colorbar center
            yanchor='middle',      # Anchor point for y position
            thickness=20,          # Make the colorbar slightly thicker
            ticks="outside"        # Place ticks outside the colorbar
        )
    )

def plot_concurrency(
    data_list: List[pl.DataFrame],
    stats: ConcurrencyStats,
    config_list: List[StrategyConfig]
) -> go.Figure:
    """Create visualization of concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        stats (ConcurrencyStats): Concurrency statistics
        config_list (List[StrategyConfig]): List of strategy configurations

    Returns:
        go.Figure: Plotly figure object containing the visualization

    Raises:
        ValueError: If required columns are missing from dataframes
    """
    required_cols = ["Date", "Close", "Position"]
    for df in data_list:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    n_strategies = len(data_list)
    
    # Create subplot layout
    subplot_titles = (
        [f"Price and Positions ({config['TICKER']})" for config in config_list] +
        ["Strategy Concurrency"]
    )
    
    fig = make_subplots(
        rows=n_strategies + 1,
        cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.05,
        row_heights=[0.8/n_strategies] * n_strategies + [0.2]
    )

    # Define colors for each strategy
    strategy_colors = [
        'rgba(9,30,135,0.2)',   # dark blue
        'rgba(25,75,165,0.2)',  # medium-dark blue
        'rgba(65,105,185,0.2)', # medium blue
        'rgba(95,145,205,0.2)', # light-medium blue
        'rgba(135,175,225,0.2)',# light blue
        'rgba(175,205,235,0.2)',# very light blue
        'rgba(205,225,245,0.2)' # ultra light blue
    ]
    
    # Add strategy subplots
    for i, (data, config) in enumerate(zip(data_list, config_list), 1):
        color = strategy_colors[i-1 % len(strategy_colors)]
        traces = create_strategy_subplot(data, config, color, i)
        for trace in traces:
            fig.add_trace(trace, row=i, col=1)

    # Add concurrency heatmap
    position_arrays = [df["Position"].fill_null(0) for df in data_list]
    heatmap = create_concurrency_heatmap(data_list, position_arrays, n_strategies)
    fig.add_trace(heatmap, row=n_strategies + 1, col=1)

    # Add statistics annotation
    stats['start_date'] = data_list[0]['Date'].min().strftime('%Y-%m-%d')
    stats['end_date'] = data_list[0]['Date'].max().strftime('%Y-%m-%d')
    fig.add_annotation(**create_stats_annotation(stats))

    # Update layout
    height = 300 * (n_strategies + 1)
    fig.update_layout(
        height=height,
        title_text="Multi-Strategy Concurrency Analysis",
        showlegend=True
    )

    # Update y-axis titles
    for i in range(1, n_strategies + 1):
        fig.update_yaxes(title="Price", row=i, col=1)
    
    # Update y-axis for heatmap to remove text, numbers and scale
    fig.update_yaxes(
        showticklabels=False,
        showline=False,
        title=None,
        row=n_strategies + 1,
        col=1
    )

    return fig
