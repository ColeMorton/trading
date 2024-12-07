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

    # Define colors for each strategy aligned with ice colorscale
    strategy_colors = [
        'rgba(9,30,135,0.2)',   # dark blue
        'rgba(25,75,165,0.2)',  # medium-dark blue
        'rgba(65,105,185,0.2)', # medium blue
        'rgba(95,145,205,0.2)', # light-medium blue
        'rgba(135,175,225,0.2)',# light blue
        'rgba(175,205,235,0.2)',# very light blue
        'rgba(205,225,245,0.2)' # ultra light blue
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
            colorscale='ice',
            showscale=True,
            name="Active Strategies"
        ),
        row=n_strategies + 1, col=1
    )

    # Add statistics as annotations
    stats_text = (
        f"Analysis Period: {data_list[0]['Date'].min().strftime('%Y-%m-%d')} to "
        f"{data_list[0]['Date'].max().strftime('%Y-%m-%d')}<br>"
        f"<br><b>Concurrency Metrics:</b><br>"
        f"Total Periods: {stats['total_periods']}<br>"
        f"Concurrent Periods: {stats['total_concurrent_periods']}<br>"
        f"Concurrency Ratio: {stats['concurrency_ratio']:.2%}<br>"
        f"Exclusive Ratio: {stats['exclusive_ratio']:.2%}<br>"
        f"Inactive (Remaining): {stats['inactive_ratio']:.2%}<br>"
        f"Avg Concurrent Strategies: {stats['avg_concurrent_strategies']:.2f}<br>"
        f"Max Concurrent Strategies: {stats['max_concurrent_strategies']}<br>"
        f"Risk Concentration Index: {stats['risk_concentration_index']:.2f}<br>"
        f"Efficiency Score: {stats['efficiency_score']:.2f}<br>"
    )

    # Add risk metrics section
    stats_text += "<br><b>Risk Metrics:</b><br>"
    risk_metrics = stats['risk_metrics']
    
    # Add strategy risk contributions
    for key in sorted(risk_metrics.keys()):
        if key.startswith('strategy_'):
            stats_text += f"Strategy {key.split('_')[1]} Risk Contribution: {risk_metrics[key]:.2%}<br>"
    
    # Add risk overlaps
    for key in sorted(risk_metrics.keys()):
        if key.startswith('risk_overlap_'):
            stats_text += f"Risk Overlap {key.split('_')[2]}-{key.split('_')[3]}: {risk_metrics[key]:.2%}<br>"
    
    # Add total portfolio risk
    if 'total_portfolio_risk' in risk_metrics:
        stats_text += f"Total Portfolio Risk: {risk_metrics['total_portfolio_risk']:.4f}<br>"
    
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
