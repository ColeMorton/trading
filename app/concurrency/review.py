"""
Concurrency Analysis Module for Trading Strategies

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure.
"""

import os
import polars as pl
import numpy as np
from typing import TypedDict, NotRequired, Dict, List, Tuple
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class StrategyConfig(TypedDict):
    """
    Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_PERIOD (int): Period for RSI calculation
        RSI_THRESHOLD (float): RSI threshold for signal filtering
        STOP_LOSS (float): Stop loss percentage

    Optional Fields:
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        REFRESH (NotRequired[bool]): Whether to refresh data
        BASE_DIR (NotRequired[str]): Base directory for data storage
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    RSI_PERIOD: int
    RSI_THRESHOLD: float
    STOP_LOSS: float
    USE_SMA: NotRequired[bool]
    REFRESH: NotRequired[bool]
    BASE_DIR: NotRequired[str]

def align_data(data_1: pl.DataFrame, data_2: pl.DataFrame) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """
    Align two dataframes by date.

    Args:
        data_1 (pl.DataFrame): First dataframe
        data_2 (pl.DataFrame): Second dataframe

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Aligned dataframes
    """
    # Find common date range
    min_date = max(data_1["Date"].min(), data_2["Date"].min())
    max_date = min(data_1["Date"].max(), data_2["Date"].max())
    
    # Filter both dataframes to common date range
    data_1_aligned = data_1.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    )
    data_2_aligned = data_2.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    )
    
    return data_1_aligned, data_2_aligned

def analyze_concurrency(data_1: pl.DataFrame, data_2: pl.DataFrame) -> Dict:
    """
    Analyze concurrent positions between two strategies.

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy

    Returns:
        Dict: Dictionary containing concurrency statistics
    """
    # Align data by date
    data_1_aligned, data_2_aligned = align_data(data_1, data_2)
    
    # Convert Position columns to numpy arrays for correlation calculation
    pos_1 = data_1_aligned["Position"].fill_null(0).to_numpy()
    pos_2 = data_2_aligned["Position"].fill_null(0).to_numpy()
    
    concurrent_positions = (data_1_aligned["Position"] & data_2_aligned["Position"]).cast(pl.Int32)
    total_days = len(data_1_aligned)
    concurrent_days = concurrent_positions.sum()
    
    stats = {
        "total_days": total_days,
        "concurrent_days": int(concurrent_days),
        "concurrency_ratio": float(concurrent_days / total_days),
        "avg_position_length": float((data_1_aligned["Position"].sum() + data_2_aligned["Position"].sum()) / 2),
        "correlation": float(np.corrcoef(pos_1, pos_2)[0, 1])
    }
    
    return stats, data_1_aligned, data_2_aligned

def plot_concurrency(data_1: pl.DataFrame, data_2: pl.DataFrame, stats: Dict, config_1: StrategyConfig, config_2: StrategyConfig) -> go.Figure:
    """
    Create visualization of concurrent positions.

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy
        stats (Dict): Concurrency statistics
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy

    Returns:
        go.Figure: Plotly figure object
    """
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

    # First strategy plot
    fig.add_trace(
        go.Scatter(
            x=data_1["Date"],
            y=data_1["Close"],
            name=f"{config_1['TICKER']} Price",
            line=dict(color="black", width=1)
        ),
        row=1, col=1
    )

    position_dates_1 = data_1.filter(pl.col("Position") == 1)["Date"]
    fig.add_trace(
        go.Scatter(
            x=position_dates_1,
            y=data_1.filter(pl.col("Position") == 1)["Close"],
            name=f"{config_1['TICKER']} Positions",
            mode="markers",
            marker=dict(color="blue", size=8)
        ),
        row=1, col=1
    )

    # Second strategy plot
    fig.add_trace(
        go.Scatter(
            x=data_2["Date"],
            y=data_2["Close"],
            name=f"{config_2['TICKER']} Price",
            line=dict(color="black", width=1)
        ),
        row=2, col=1
    )

    position_dates_2 = data_2.filter(pl.col("Position") == 1)["Date"]
    fig.add_trace(
        go.Scatter(
            x=position_dates_2,
            y=data_2.filter(pl.col("Position") == 1)["Close"],
            name=f"{config_2['TICKER']} Positions",
            mode="markers",
            marker=dict(color="red", size=8)
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
            line=dict(color="green")
        ),
        row=3, col=1
    )

    # Add statistics as annotations
    stats_text = (
        f"Analysis Period: {data_1['Date'].min().strftime('%Y-%m-%d')} to {data_1['Date'].max().strftime('%Y-%m-%d')}<br>"
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

    fig.update_layout(
        height=1000,
        title_text=f"Concurrency Analysis: {config_1['TICKER']} vs {config_2['TICKER']}",
        showlegend=True
    )

    return fig

def run(config_1: StrategyConfig, config_2: StrategyConfig) -> bool:
    """
    Run concurrency analysis between two strategies.

    Args:
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='concurrency',
        log_file='concurrency_analysis.log'
    )
    
    try:
        log(f"Starting concurrency analysis for {config_1['TICKER']} vs {config_2['TICKER']}")
        
        # Get and prepare data for both strategies
        data_1 = get_data(config_1["TICKER"], config_1)
        data_2 = get_data(config_2["TICKER"], config_2)
        
        # Calculate MAs and signals for both strategies
        data_1 = calculate_ma_and_signals(
            data_1, 
            config_1['SHORT_WINDOW'], 
            config_1['LONG_WINDOW'], 
            config_1
        )
        
        data_2 = calculate_ma_and_signals(
            data_2, 
            config_2['SHORT_WINDOW'], 
            config_2['LONG_WINDOW'], 
            config_2
        )
        
        # Analyze concurrency
        stats, data_1_aligned, data_2_aligned = analyze_concurrency(data_1, data_2)
        log(f"Concurrency analysis completed. Concurrent ratio: {stats['concurrency_ratio']:.2%}")
        
        # Create and display visualization
        fig = plot_concurrency(data_1_aligned, data_2_aligned, stats, config_1, config_2)
        fig.show()
        log("Visualization displayed successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    # Example configurations
    strategy_1: StrategyConfig = {
        "TICKER": "BTC-USD",
        "SHORT_WINDOW": 27,
        "LONG_WINDOW": 29,
        "BASE_DIR": ".",
        "USE_SMA": True,
        "REFRESH": True,
        "USE_RSI": False,
        "RSI_PERIOD": 14,
        "RSI_THRESHOLD": 50,
        "STOP_LOSS": 0.0911
    }

    strategy_2: StrategyConfig = {
        "TICKER": "SOL-USD",
        "SHORT_WINDOW": 14,
        "LONG_WINDOW": 32,
        "BASE_DIR": ".",
        "USE_SMA": True,
        "REFRESH": True,
        "USE_RSI": True,
        "RSI_PERIOD": 26,
        "RSI_THRESHOLD": 43,
        "STOP_LOSS": 0.125
    }

    try:
        result = run(strategy_1, strategy_2)
        if result:
            print("Concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
