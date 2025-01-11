"""
Stop Loss Analysis Module

This module contains functions for analyzing stop loss parameter sensitivity.
"""

import polars as pl
import numpy as np
from typing import Dict, Callable, Any
from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats
from app.tools.calculate_rsi import calculate_rsi
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import export_csv, ExportConfig

def analyze_stop_loss_parameters(
    data: pl.DataFrame,
    config: Dict[str, Any],
    stop_loss_range: np.ndarray,
    log: Callable
) -> Dict[str, np.ndarray]:
    """
    Analyze stop loss parameters across different percentages.

    Args:
        data (pl.DataFrame): Price and indicator data
        config (Dict): Strategy configuration
        stop_loss_range (np.ndarray): Array of stop loss percentages to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric arrays for returns, win rates, and Sharpe Ratio
    """
    num_stops = len(stop_loss_range)
    
    # Initialize result arrays
    returns_array = np.zeros(num_stops)
    win_rate_array = np.zeros(num_stops)
    sharpe_ratio_array = np.zeros(num_stops)
    trades_array = np.zeros(num_stops)
    
    # Store portfolios for export
    portfolios = []

    # Add RSI if enabled
    if config.get('USE_RSI', False):
        data = calculate_rsi(data, config['RSI_PERIOD'])
        log(f"RSI enabled with period: {config['RSI_PERIOD']} and threshold: {config['RSI_THRESHOLD']}")

    # Calculate MA and base signals
    data_with_signals = calculate_ma_and_signals(
        data,
        config["SHORT_WINDOW"],
        config["LONG_WINDOW"],
        config,
        log  # Pass the log parameter here
    )
    
    # Get baseline performance ONLY IF RELATIVE is True
    if config.get('RELATIVE', True):
        baseline_config = {**config, "STOP_LOSS": None}
        baseline_portfolio = backtest_strategy(data_with_signals, baseline_config, log)
        baseline_stats = convert_stats(baseline_portfolio.stats(), log, baseline_config)
        
        # Store baseline metrics
        baseline_metrics = {
            'returns': float(baseline_stats.get('Total Return [%]', 0)),
            'win_rate': float(baseline_stats.get('Win Rate [%]', 0)),
            'sharpe_ratio': float(baseline_stats.get('Sharpe Ratio', 0)),
            'trades': float(baseline_stats.get('Total Closed Trades', 0))
        }
        
        if log:
            log(f"Baseline metrics - Returns: {baseline_metrics['returns']:.2f}%, "
                f"Win Rate: {baseline_metrics['win_rate']:.2f}%, "
                f"Sharpe: {baseline_metrics['sharpe_ratio']:.2f}, "
                f"Trades: {baseline_metrics['trades']}")
    
    # Analyze each stop loss percentage
    for i, stop_loss in enumerate(stop_loss_range):
        # Convert percentage to decimal (e.g., 3.74% -> 0.0374)
        stop_loss_pct = round(float(stop_loss), 2)
        stop_loss_decimal = stop_loss_pct / 100
        config["STOP_LOSS"] = stop_loss_decimal
        
        if log:
            log(f"Testing stop loss of {stop_loss_pct:.2f}% ({stop_loss_decimal:.4f})")
        
        portfolio = backtest_strategy(data_with_signals, config, log)
        stats = portfolio.stats()
        converted_stats = convert_stats(stats, log, config)
        
        # Add stop loss parameter to stats
        converted_stats["Stop Loss [%]"] = stop_loss
        portfolios.append(converted_stats)
        
        # Calculate metrics
        current_metrics = {
            'returns': float(converted_stats.get('Total Return [%]', 0)),
            'win_rate': float(converted_stats.get('Win Rate [%]', 0)),
            'sharpe_ratio': float(converted_stats.get('Sharpe Ratio', 0)),
            'trades': float(converted_stats.get('Total Closed Trades', 0))
        }
        
        # Calculate relative or absolute metrics based on config
        if config.get('RELATIVE', True):
            returns_array[i] = current_metrics['returns'] - baseline_metrics['returns']
            win_rate_array[i] = current_metrics['win_rate'] - baseline_metrics['win_rate']
            
            # For Sharpe and trades, use percentage change when baseline is non-zero
            if baseline_metrics['sharpe_ratio'] != 0:
                sharpe_ratio_array[i] = ((current_metrics['sharpe_ratio'] / baseline_metrics['sharpe_ratio']) * 100 - 100)
            else:
                sharpe_ratio_array[i] = current_metrics['sharpe_ratio']
                
            if baseline_metrics['trades'] != 0:
                trades_array[i] = ((current_metrics['trades'] / baseline_metrics['trades']) * 100 - 100)
            else:
                trades_array[i] = current_metrics['trades']
        else:
            returns_array[i] = current_metrics['returns']
            win_rate_array[i] = current_metrics['win_rate']
            sharpe_ratio_array[i] = current_metrics['sharpe_ratio']
            trades_array[i] = current_metrics['trades']
        
        if log:
            log(f"Analyzed stop loss {stop_loss_pct:.2f}%")
    
    # Create filename with MA windows and RSI if used
    ticker_prefix = config.get("TICKER", "")
    if isinstance(ticker_prefix, list):
        ticker_prefix = ticker_prefix[0] if ticker_prefix else ""
    
    rsi_suffix = f"_RSI_{config['RSI_PERIOD']}_{config['RSI_THRESHOLD']}" if config.get('USE_RSI', False) else ""
    filename = f"{ticker_prefix}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}_{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}{rsi_suffix}.csv"
    
    # Export portfolios
    export_config = ExportConfig(BASE_DIR=config["BASE_DIR"], TICKER=config.get("TICKER"))
    export_csv(portfolios, "ma_cross", export_config, "stop_loss", filename)
    
    # Ensure no NaN values in final arrays
    returns_array = np.nan_to_num(returns_array, 0)
    win_rate_array = np.nan_to_num(win_rate_array, 0)
    sharpe_ratio_array = np.nan_to_num(sharpe_ratio_array, 0)
    trades_array = np.nan_to_num(trades_array, 0)
    
    return {
        'trades': trades_array,
        'returns': returns_array,
        'sharpe_ratio': sharpe_ratio_array,
        'win_rate': win_rate_array
    }
