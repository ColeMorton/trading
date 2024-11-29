"""
Protective Stop Loss Metrics Module

This module handles the calculation and organization of performance metrics
for protective stop loss analysis.
"""

import numpy as np
import polars as pl
import vectorbt as vbt
from typing import Dict, List, Tuple, Callable
from app.ema_cross.tools.psl_types import MetricMatrices
from app.tools.file_utils import convert_stats
from app.ema_cross.tools.backtest_strategy import backtest_strategy

def initialize_metric_matrices(num_periods: int) -> MetricMatrices:
    """
    Initialize arrays for storing performance metrics.

    Args:
        num_periods (int): Number of holding periods to analyze

    Returns:
        MetricMatrices: Dictionary containing initialized metric arrays
    """
    return {
        'trades': np.zeros(num_periods),
        'returns': np.zeros(num_periods),
        'sharpe_ratio': np.zeros(num_periods),
        'win_rate': np.zeros(num_periods)
    }

def calculate_portfolio_metrics(
    portfolio: vbt.Portfolio,
    metrics: MetricMatrices,
    index: int
) -> None:
    """
    Calculate and store portfolio metrics for a given holding period.

    Args:
        portfolio (vbt.Portfolio): VectorBT portfolio object
        metrics (MetricMatrices): Dictionary of metric arrays
        index (int): Index to store metrics at
    """
    metrics['trades'][index] = portfolio.positions.count()
    metrics['returns'][index] = portfolio.total_return()
    metrics['sharpe_ratio'][index] = portfolio.sharpe_ratio()
    metrics['win_rate'][index] = portfolio.trades.win_rate()

def create_portfolio_stats(
    portfolio: vbt.Portfolio,
    holding_period: int
) -> Dict:
    """
    Create portfolio statistics dictionary with holding period information.

    Args:
        portfolio (vbt.Portfolio): VectorBT portfolio object
        holding_period (int): Current holding period being analyzed

    Returns:
        Dict: Portfolio statistics with holding period
    """
    stats = portfolio.stats()
    converted_stats = convert_stats(stats)
    converted_stats["Holding Period"] = holding_period
    return converted_stats

def create_filename(config: Dict) -> str:
    """
    Create standardized filename for exporting results.

    Args:
        config (Dict): Configuration dictionary containing strategy parameters

    Returns:
        str: Formatted filename
    """
    ticker_prefix = config.get("TICKER", "")
    if isinstance(ticker_prefix, list):
        ticker_prefix = ticker_prefix[0] if ticker_prefix else ""
    
    rsi_suffix = (
        f"_RSI_{config['RSI_PERIOD']}_{config['RSI_THRESHOLD']}" 
        if config.get('USE_RSI', False) else ""
    )
    stop_loss_suffix = (
        f"_SL_{config['STOP_LOSS']}" 
        if config.get('STOP_LOSS') is not None else ""
    )
    
    return (
        f"{ticker_prefix}_D_"
        f"{'SMA' if config.get('USE_SMA', False) else 'EMA'}_"
        f"{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}"
        f"{rsi_suffix}{stop_loss_suffix}.csv"
    )
