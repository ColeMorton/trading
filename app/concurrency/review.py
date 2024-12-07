"""
Concurrency Analysis Module for Trading Strategies

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure.
"""

import polars as pl
import numpy as np
from typing import TypedDict, NotRequired, Dict, List
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
        RSI_WINDOW (int): Period for RSI calculation
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
    RSI_WINDOW: int
    RSI_THRESHOLD: float
    STOP_LOSS: float
    USE_SMA: NotRequired[bool]
    REFRESH: NotRequired[bool]
    BASE_DIR: NotRequired[str]

def analyze_concurrency(data_1: pl.DataFrame, data_2: pl.DataFrame) -> Dict:
    """
    Analyze concurrent positions between two strategies.

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy

    Returns:
        Dict: Dictionary containing concurrency statistics
    """
    # Convert Position columns to numpy arrays for correlation calculation
    pos_1 = data_1["Position"].fill_null(0).to_numpy()
    pos_2 = data_2["Position"].fill_null(0).to_numpy()
    
    concurrent_positions = (data_1["Position"] & data_2["Position"]).cast(pl.Int32)
    total_days = len(data_1)
    concurrent_days = concurrent_positions.sum()
    
    stats = {
        "total_days": total_days,
        "concurrent_days": int(concurrent_days),
        "concurrency_ratio": float(concurrent_days / total_days),
        "avg_position_length": float((data_1["Position"].sum() + data_2["Position"].sum()) / 2),
        "correlation": float(np.corrcoef(pos_1, pos_2)[0, 1])
    }
    
    return stats

def plot_concurrency(data_1: pl.DataFrame, data_2: pl.DataFrame, stats: Dict, config_1: StrategyConfig, config_2: StrategyConfig) -> None:
    """
    Create visualization of concurrent positions.

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy
        stats (Dict): Concurrency statistics
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            f"Price and Positions ({config_1['TICKER']})",
            "Position Concurrency"
        ),
        vertical_spacing=0.15
    )

    # Price and positions plot
    fig.add_trace(
        go.Scatter(
            x=data_1["Date"],
            y=data_1["Close"],
            name="Price",
            line=dict(color="black", width=1)
        ),
        row=1, col=1
    )

    # Strategy 1 positions
    position_dates_1 = data_1.filter(pl.col("Position") == 1)["Date"]
    fig.add_trace(
        go.Scatter(
            x=position_dates_1,
            y=data_1.filter(pl.col("Position") == 1)["Close"],
            name="Strategy 1 Positions",
            mode="markers",
            marker=dict(color="blue", size=8)
        ),
        row=1, col=1
    )

    # Strategy 2 positions
    position_dates_2 = data_2.filter(pl.col("Position") == 1)["Date"]
    fig.add_trace(
        go.Scatter(
            x=position_dates_2,
            y=data_2.filter(pl.col("Position") == 1)["Close"],
            name="Strategy 2 Positions",
            mode="markers",
            marker=dict(color="red", size=8)
        ),
        row=1, col=1
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
        row=2, col=1
    )

    # Add statistics as annotations
    stats_text = (
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
        height=800,
        title_text=f"Concurrency Analysis: {config_1['TICKER']}",
        showlegend=True
    )

    fig.write_html("concurrency_analysis.html")

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
        log(f"Starting concurrency analysis for {config_1['TICKER']}")
        
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
        stats = analyze_concurrency(data_1, data_2)
        log(f"Concurrency analysis completed. Concurrent ratio: {stats['concurrency_ratio']:.2%}")
        
        # Create visualization
        plot_concurrency(data_1, data_2, stats, config_1, config_2)
        log("Visualization created successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    # Example configurations
    strategy_1: StrategyConfig = {
        "TICKER": "MCD",
        "SHORT_WINDOW": 32,
        "LONG_WINDOW": 38,
        "BASE_DIR": ".",
        "USE_SMA": False,
        "REFRESH": True,
        "USE_RSI": False,
        "RSI_WINDOW": 22,
        "RSI_THRESHOLD": 45,
        "STOP_LOSS": 0.0423
    }

    strategy_2: StrategyConfig = {
        "TICKER": "MCD",
        "SHORT_WINDOW": 32,
        "LONG_WINDOW": 38,
        "BASE_DIR": ".",
        "USE_SMA": False,
        "REFRESH": True,
        "USE_RSI": False,
        "RSI_WINDOW": 22,
        "RSI_THRESHOLD": 45,
        "STOP_LOSS": 0.0423
    }

    try:
        result = run(strategy_1, strategy_2)
        if result:
            print("Concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
