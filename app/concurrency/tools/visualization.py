"""Visualization utilities for concurrency analysis."""

from typing import Dict, List
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.concurrency.tools.types import StrategyConfig, ConcurrencyStats

def plot_concurrency(
    data_list: List[pl.DataFrame],
    stats: ConcurrencyStats,
    config_list: List[StrategyConfig]
) -> go.Figure:
    """Create visualization of concurrent positions across multiple strategies.

    Creates a multi-panel plot showing:
    1. Individual strategy price and positions (one panel per strategy)
    2. Combined concurrency heatmap showing overlap between strategies

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals for each strategy
        stats (ConcurrencyStats): Concurrency statistics
        config_list (List[StrategyConfig]): List of configurations for each strategy

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
    
    # Create subplot layout: n strategy panels + 1 concurrency panel
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
        'rgba(0,0,255,0.2)',   # blue
        'rgba(255,0,0,0.2)',   # red
        'rgba(0,255,0,0.2)',   # green
        'rgba(128,0,128,0.2)', # purple
        'rgba(255,165,0,0.2)', # orange
        'rgba(165,42,42,0.2)', # brown
        'rgba(255,192,203,0.2)'# pink
    ]
    
    # Plot each strategy's price and positions
    for i, (data, config) in enumerate(zip(data_list, config_list), 1):
        color = strategy_colors[i-1 % len(strategy_colors)]
        
        # Base price line
        fig.add_trace(
            go.Scatter(
                x=data["Date"],
                y=data["Close"],
                name=f"{config['TICKER']} Price",
                line=dict(color="black", width=1)
            ),
            row=i, col=1
        )

        # Position highlighting
        for j in range(len(data)):
            if data["Position"][j] == 1:
                fig.add_trace(
                    go.Scatter(
                        x=[data["Date"][j], data["Date"][j]],
                        y=[0, data["Close"][j]],
                        mode='lines',
                        line=dict(color=color, width=1),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=i, col=1
                )

        # Legend entry for positions
        fig.add_trace(
            go.Scatter(
                x=[data["Date"][0]],
                y=[data["Close"][0]],
                name=f"{config['TICKER']} Positions",
                mode='lines',
                line=dict(color=color, width=10),
                showlegend=True
            ),
            row=i, col=1
        )

    # Create concurrency heatmap
    position_arrays = [df["Position"].fill_null(0).to_numpy() for df in data_list]
    active_strategies = sum(position_arrays)
    
    fig.add_trace(
        go.Heatmap(
            x=data_list[0]["Date"],
            y=['Concurrent Strategies'],
            z=[active_strategies],
            colorscale='Plasma',
            showscale=True,
            name="Active Strategies"
        ),
        row=n_strategies + 1, col=1
    )

    # Add statistics as annotations   
    stats_text = (
        f"Analysis Period: {data_list[0]['Date'].min().strftime('%Y-%m-%d')} to "
        f"{data_list[0]['Date'].max().strftime('%Y-%m-%d')}<br>"
        f"Total Periods: {stats['total_periods']}<br>"
        f"Concurrent Periods: {stats['total_concurrent_periods']}<br>"
        f"Concurrency Ratio: {stats['concurrency_ratio']:.2%}<br>"
        f"Exclusive Ratio: {stats['exclusive_ratio']:.2%}<br>"
        f"Inactive (Remaining): {stats['inactive_ratio']:.2%}<br>"
        f"Avg Concurrent Strategies: {stats['avg_concurrent_strategies']:.2f}<br>"
        f"Max Concurrent Strategies: {stats['max_concurrent_strategies']}<br>"
    )
    
    fig.add_annotation(
        xref="paper", yref="paper",
        x=1.0, y=1.0,
        text=stats_text,
        showarrow=False,
        font=dict(size=10),
        align="right",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )

    # Update layout
    height = 300 * (n_strategies + 1)  # Dynamic height based on number of strategies
    fig.update_layout(
        height=height,
        title_text="Multi-Strategy Concurrency Analysis",
        showlegend=True
    )

    # Update y-axis titles
    for i in range(1, n_strategies + 1):
        fig.update_yaxes(title="Price", row=i, col=1)
    fig.update_yaxes(title="Concurrency", row=n_strategies + 1, col=1)

    return fig
