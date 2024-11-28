"""
RSI Analysis Module

This module contains functions for analyzing RSI (Relative Strength Index)
parameters in combination with EMA cross signals.
"""

import polars as pl
import vectorbt as vbt
from typing import Dict
from app.tools.file_utils import convert_stats

def backtest(data: pl.DataFrame, rsi_threshold: float) -> vbt.Portfolio:
    """
    Run backtest with RSI threshold filtering.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_threshold (float): RSI threshold for entry signals

    Returns:
        vbt.Portfolio: Portfolio object containing backtest results
    """
    # Convert to pandas for vectorbt
    data_pd = data.to_pandas()
    
    # Generate entry/exit signals
    entries = (
        (data_pd['MA_FAST'] > data_pd['MA_SLOW']) & 
        (data_pd['MA_FAST'].shift(1) <= data_pd['MA_SLOW'].shift(1)) &
        (data_pd['RSI'] >= rsi_threshold)
    )
    
    exits = (
        (data_pd['MA_FAST'] < data_pd['MA_SLOW']) & 
        (data_pd['MA_FAST'].shift(1) >= data_pd['MA_SLOW'].shift(1))
    )
    
    # Create portfolio
    portfolio = vbt.Portfolio.from_signals(
        close=data_pd['Close'],
        entries=entries,
        exits=exits,
        init_cash=1000,
        fees=0.001,
        freq='D'
    )
    
    return portfolio

def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: pl.Series) -> pl.DataFrame:
    """
    Run sensitivity analysis across RSI thresholds.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_range (pl.Series): Array of RSI thresholds to test

    Returns:
        pl.DataFrame: Results of sensitivity analysis with metrics for each threshold
    """
    results = []
    for rsi_threshold in rsi_range:
        portfolio = backtest(data, rsi_threshold)
        stats = portfolio.stats()
        
        # Add RSI threshold to stats
        stats['RSI Threshold'] = rsi_threshold
        
        # Convert stats to proper format
        converted_stats = convert_stats(stats)
        
        results.append({
            'RSI Threshold': rsi_threshold,
            'Total Return': converted_stats['Total Return [%]'],
            'Win Rate': converted_stats['Win Rate [%]'],
            'Expectancy': converted_stats['Expectancy'],
            'Number of Positions': converted_stats['Total Closed Trades']
        })
    
    return pl.DataFrame(results)
