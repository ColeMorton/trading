"""
RSI Heatmap Module

This module contains functions for analyzing RSI parameter sensitivity.
"""

import polars as pl
import numpy as np
from typing import Dict, Callable, Any
from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import export_csv, ExportConfig

def analyze_rsi_parameters(
    data: pl.DataFrame,
    config: Dict[str, Any],
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    log: Callable
) -> Dict[str, np.ndarray]:
    """
    Analyze RSI parameters across different thresholds and window lengths.

    Args:
        data (pl.DataFrame): Price and indicator data
        config (Dict[str, Any]): Strategy configuration
        rsi_thresholds (np.ndarray): Array of RSI thresholds to test
        rsi_windows (np.ndarray): Array of RSI window lengths to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric matrices
    """
    # Initialize result matrices
    matrices = {
        'returns': np.zeros((len(rsi_thresholds), len(rsi_windows))),
        'win_rate': np.zeros((len(rsi_thresholds), len(rsi_windows))),
        'sharpe_ratio': np.zeros((len(rsi_thresholds), len(rsi_windows))),
        'trades': np.zeros((len(rsi_thresholds), len(rsi_windows)))
    }
    portfolios = []
    
    # Get baseline performance ONLY IF RELATIVE is True
    if config.get('RELATIVE', True):
        baseline_config = {**config, "USE_RSI": False}
        baseline_data = calculate_ma_and_signals(
            data,
            baseline_config["SHORT_WINDOW"],
            baseline_config["LONG_WINDOW"],
            baseline_config,
            log
        )
        baseline_portfolio = backtest_strategy(baseline_data, baseline_config, log)
        baseline_stats = convert_stats(baseline_portfolio.stats(), baseline_config)
    
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
    
    # Analyze each combination
    for i, threshold in enumerate(rsi_thresholds):
        config["RSI_THRESHOLD"] = threshold
        config["USE_RSI"] = True
        
        for j, window in enumerate(rsi_windows):
            config["RSI_WINDOW"] = window
            data_with_signals = calculate_ma_and_signals(
                data,
                config["SHORT_WINDOW"],
                config["LONG_WINDOW"],
                config,
                log
            )
            
            portfolio = backtest_strategy(data_with_signals, config, log)
            stats = convert_stats(portfolio.stats(), config)
            
            # Add RSI parameters and append to portfolios
            stats.update({"RSI Window": window, "RSI Threshold": threshold})
            portfolios.append(stats)
            
            # Calculate relative metrics ONLY IF RELATIVE is True
            for metric in matrices.keys():
                current = float(stats.get(
                    {'returns': 'Total Return [%]',
                     'win_rate': 'Win Rate [%]',
                     'sharpe_ratio': 'Sharpe Ratio',
                     'trades': 'Total Closed Trades'}[metric],
                    0
                ))
                
                if config.get('RELATIVE', True):
                    baseline = baseline_metrics[metric]
                    if metric in ['sharpe_ratio', 'trades'] and baseline != 0:
                        matrices[metric][i, j] = ((current / baseline) * 100 - 100)
                    else:
                        matrices[metric][i, j] = current - baseline
                else:
                    matrices[metric][i, j] = current # Use absolute value when RELATIVE is False
            
            if log:
                log(f"Analyzed RSI window {window}, threshold {threshold}")
    
    # Export results
    filename = f"{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}.csv"
    export_config = ExportConfig(
        BASE_DIR=config["BASE_DIR"],
        TICKER=config.get("TICKER"),
        USE_HOURLY=config.get("USE_HOURLY", False),
        USE_SMA=config.get("USE_SMA", False)
    )
    export_csv(portfolios, "ma_cross", export_config, "rsi", filename)
    
    return {k: v.T for k, v in matrices.items()}
