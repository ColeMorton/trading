"""Visualization utilities for concurrency analysis."""

from typing import Dict
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.concurrency.tools.types import StrategyConfig, ConcurrencyStats

def plot_concurrency(
    data_1: pl.DataFrame,
    data_2: pl.DataFrame,
    stats: ConcurrencyStats,
    config_1: StrategyConfig,
    config_2: StrategyConfig
) -> go.Figure:
    """Create visualization of concurrent positions.

    Creates a three-panel plot showing:
    1. First strategy's price and positions
    2. Second strategy's price and positions
    3. Concurrent position periods

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy
        stats (ConcurrencyStats): Concurrency statistics
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy

    Returns:
        go.Figure: Plotly figure object containing the visualization

    Raises:
        ValueError: If required columns are missing from dataframes
    """
    required_cols = ["Date", "Close", "Position"]
    for df in [data_1, data_2]:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f"Price and Positions ({config_1['TICKER']})",
            f"Price and Positions ({config_2['TICKER']})",
            "Position Concurrency"
        ),
        vertical_spacing=0.1,
        row_heights=[0.35, 0.35, 0.3]
    )

    # First strategy plot - Base price line
    fig.add_trace(
        go.Scatter(
            x=data_1["Date"],
            y=data_1["Close"],
            name=f"{config_1['TICKER']} Price",
            line=dict(color="black", width=1)
        ),
        row=1, col=1
    )

    # Add position highlighting for first strategy
    for i in range(len(data_1)):
        if data_1["Position"][i] == 1:
            fig.add_trace(
                go.Scatter(
                    x=[data_1["Date"][i], data_1["Date"][i]],
                    y=[0, data_1["Close"][i]],
                    mode='lines',
                    line=dict(color='rgba(0,0,255,0.2)', width=1),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=1
            )

    # Second strategy plot - Base price line
    fig.add_trace(
        go.Scatter(
            x=data_2["Date"],
            y=data_2["Close"],
            name=f"{config_2['TICKER']} Price",
            line=dict(color="black", width=1)
        ),
        row=2, col=1
    )

    # Add position highlighting for second strategy
    for i in range(len(data_2)):
        if data_2["Position"][i] == 1:
            fig.add_trace(
                go.Scatter(
                    x=[data_2["Date"][i], data_2["Date"][i]],
                    y=[0, data_2["Close"][i]],
                    mode='lines',
                    line=dict(color='rgba(255,0,0,0.2)', width=1),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1
            )

    # Add legend entries for positions
    fig.add_trace(
        go.Scatter(
            x=[data_1["Date"][0]],
            y=[data_1["Close"][0]],
            name=f"{config_1['TICKER']} Positions",
            mode='lines',
            line=dict(color='rgba(0,0,255,0.2)', width=10),
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=[data_2["Date"][0]],
            y=[data_2["Close"][0]],
            name=f"{config_2['TICKER']} Positions",
            mode='lines',
            line=dict(color='rgba(255,0,0,0.2)', width=10),
            showlegend=True
        ),
        row=2, col=1
    )

    # Concurrent positions
    concurrent = (data_1["Position"] & data_2["Position"]).cast(pl.Int32)
    fig.add_trace(
        go.Scatter(
            x=data_1["Date"],
            y=concurrent,
            name="Concurrent Positions",
            fill="tozeroy",
            fillcolor='rgba(0,255,0,0.3)',
            line=dict(color="green", width=1)
        ),
        row=3, col=1
    )

    # Add statistics as annotations
    stats_text = (
        f"Analysis Period: {data_1['Date'].min().strftime('%Y-%m-%d')} to "
        f"{data_1['Date'].max().strftime('%Y-%m-%d')}<br>"
        f"Total Days: {stats['total_days']}<br>"
        f"Concurrent Days: {stats['concurrent_days']}<br>"
        f"Concurrency Ratio: {stats['concurrency_ratio']:.2%}<br>"
        f"Signal Correlation: {stats['correlation']:.2f}"
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
    fig.update_layout(
        height=1000,
        title_text=f"Concurrency Analysis: {config_1['TICKER']} vs {config_2['TICKER']}",
        showlegend=True,
        yaxis=dict(title="Price"),
        yaxis2=dict(title="Price"),
        yaxis3=dict(title="Concurrent")
    )

    return fig
