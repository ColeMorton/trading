"""
Mean Reversion Heatmap Module

This module contains functions for analyzing Mean Reversion parameter sensitivity.
"""

import polars as pl
import numpy as np
from typing import Dict, Callable, Any
from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats
from app.tools.export_csv import export_csv, ExportConfig
from app.mean_reversion.tools.calculate_signals import calculate_signals, SignalConfig

def analyze_parameters(
    data: pl.DataFrame,
    config: Dict[str, Any],
    change_range: np.ndarray,
    candle_exit_range: np.ndarray,
    log: Callable
) -> Dict[str, np.ndarray]:
    """
    Analyze mean reversion parameters across different price changes and exit candles.

    Args:
        data (pl.DataFrame): Price data
        config (Dict[str, Any]): Strategy configuration
        change_range (np.ndarray): Array of price change percentages to test
        candle_exit_range (np.ndarray): Array of exit candles to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric matrices
    """
    # Initialize result matrices
    matrices = {
        'returns': np.zeros((len(change_range), len(candle_exit_range))),
        'win_rate': np.zeros((len(change_range), len(candle_exit_range))),
        'sharpe_ratio': np.zeros((len(change_range), len(candle_exit_range))),
        'trades': np.zeros((len(change_range), len(candle_exit_range)))
    }
    portfolios = []

    # Test each parameter combination
    for i, price_change in enumerate(change_range):
        for j, exit_candles in enumerate(candle_exit_range):
            try:
                # Create signal config
                signal_config = SignalConfig(
                    PRICE_CHANGE_PCT=float(price_change),
                    EXIT_CANDLES=int(exit_candles),
                    DIRECTION=config['DIRECTION']
                )

                # Calculate signals
                entries, exits = calculate_signals(data, signal_config)
                
                # Create signals DataFrame for backtest
                signals_df = data.with_columns([
                    entries.alias('Signal')
                ])
                
                # Run backtest
                portfolio = backtest_strategy(signals_df, config, log)
                
                # Store results
                if portfolio is not None:
                    stats = portfolio.stats()
                    matrices['returns'][i, j] = stats['Total Return [%]']
                    matrices['win_rate'][i, j] = stats['Win Rate [%]']
                    matrices['sharpe_ratio'][i, j] = stats['Sharpe Ratio']
                    matrices['trades'][i, j] = stats['Total Trades']
                    
                    # Add to portfolios list for export
                    portfolio_stats = {
                        'price_change': price_change,
                        'exit_candles': exit_candles,
                        **convert_stats(stats, log, config)  # Pass log function and config
                    }
                    portfolios.append(portfolio_stats)
                    
                if log:
                    log(f"Tested price_change={price_change:.1f}%, exit_candles={exit_candles}")
                    
            except Exception as e:
                if log:
                    log(f"Error testing price_change={price_change:.1f}%, exit_candles={exit_candles}: {str(e)}", "error")
                continue

    # Export results
    timeframe = "Hourly" if config["USE_HOURLY"] else "Daily"
    filename = f"{config['TICKER']}_{timeframe}.csv"
    export_config = ExportConfig(
        BASE_DIR=config["BASE_DIR"],
        TICKER=config.get("TICKER"),
        USE_HOURLY=config.get("USE_HOURLY", False),
        USE_SMA=config.get("USE_SMA", False)
    )
    export_csv(portfolios, "mean_reversion", export_config, "mean_reversion", filename)
    
    return {k: v.T for k, v in matrices.items()}
