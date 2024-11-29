"""
Protective Stop Loss Analysis Module

This module coordinates the analysis of protective stop loss strategies,
integrating signal generation, metrics calculation, and results export.
"""

import numpy as np
import polars as pl
from typing import List, Tuple, Dict, Callable
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi
from app.ema_cross.tools.backtest_strategy import backtest_strategy
from app.tools.export_csv import export_csv, ExportConfig
from app.ema_cross.tools.psl_types import PSLConfig, MetricMatrices, AnalysisResult, HoldingPeriodResult
from app.ema_cross.tools.psl_exit import psl_exit, calculate_longest_holding_period
from app.ema_cross.tools.psl_metrics import (
    initialize_metric_matrices,
    calculate_portfolio_metrics,
    create_portfolio_stats,
    create_filename
)

def prepare_data(data: pl.DataFrame, config: PSLConfig, log: Callable) -> Tuple[pl.DataFrame, np.ndarray]:
    """
    Prepare data by calculating technical indicators and generating entry signals.

    Args:
        data (pl.DataFrame): Price data
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        Tuple[pl.DataFrame, np.ndarray]: Prepared data and entry signals
    """
    # Calculate moving averages
    data = calculate_mas(
        data, 
        config['SHORT_WINDOW'], 
        config['LONG_WINDOW'], 
        config.get('USE_SMA', False)
    )
    
    # Calculate RSI if enabled
    if config.get("USE_RSI", False):
        data = calculate_rsi(data, config['RSI_PERIOD'])
        log(f"RSI calculated with period {config['RSI_PERIOD']}")
    
    # Generate entry signals
    entries, _ = calculate_ma_signals(data, config)
    entries = entries.to_numpy().astype(bool)
    
    return data, entries

def create_signal_column(
    entries: np.ndarray,
    exits: np.ndarray,
    size: int
) -> np.ndarray:
    """
    Create signal column with proper position tracking.

    Args:
        entries (np.ndarray): Entry signals
        exits (np.ndarray): Exit signals
        size (int): Size of the array

    Returns:
        np.ndarray: Signal column (1 for entry, 0 for exit)
    """
    signals = np.zeros(size)
    position_active = False
    
    for i in range(size):
        if entries[i]:
            position_active = True
            signals[i] = 1
        elif exits[i] and position_active:
            position_active = False
            signals[i] = 0
        elif position_active:
            signals[i] = 1
            
    return signals

def analyze_protective_stop_loss_parameters(
    data: pl.DataFrame,
    config: PSLConfig,
    log: Callable
) -> AnalysisResult:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        AnalysisResult: Tuple containing metric matrices and holding period range
    """
    # Prepare data and generate entry signals
    data, entries = prepare_data(data, config, log)
    
    # Calculate longest holding period
    longest_holding_period = calculate_longest_holding_period(entries)
    log(f"Calculated longest holding period: {longest_holding_period} days")
    
    # Create holding period range
    holding_period_range = np.arange(1, longest_holding_period + 1)
    
    # Initialize metrics
    metrics = initialize_metric_matrices(len(holding_period_range))
    
    # Get stop loss from config
    stop_loss = config.get('STOP_LOSS', None)
    if stop_loss is not None:
        log(f"Using stop loss of {stop_loss*100}%")

    # Store portfolios for export
    portfolios = []

    # Test each holding period
    for i, holding_period in enumerate(holding_period_range):
        log(f"Testing holding period: {holding_period} days")
        
        # Generate PSL exit signals
        exits_psl = psl_exit(
            data['Close'].to_numpy(),
            entries,
            holding_period,
            short=config.get("SHORT", False),
            stop_loss=stop_loss
        )
        
        # Create signal column with proper position tracking
        signals = create_signal_column(
            entries,
            exits_psl,
            len(data)
        )
        
        # Create test data with signals
        test_data = data.with_columns(
            pl.Series(name="Signal", values=signals)
        )
        
        # Run backtest
        pf = backtest_strategy(test_data, config, log)
        
        # Calculate and store metrics
        calculate_portfolio_metrics(pf, metrics, i)
        portfolios.append(create_portfolio_stats(pf, holding_period))

    # Export results
    filename = create_filename(config)
    export_config = ExportConfig(BASE_DIR=config["BASE_DIR"], TICKER=config.get("TICKER"))
    export_csv(portfolios, "ma_cross", export_config, "protective_stop_loss", filename)
    
    return metrics, holding_period_range

def analyze_holding_periods(
    data: pl.DataFrame,
    entries: pl.Series,
    exits_ema: pl.Series,
    config: PSLConfig,
    log: Callable
) -> HoldingPeriodResult:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): Price data
        entries (pl.Series): Entry signals
        exits_ema (pl.Series): EMA-based exit signals
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        HoldingPeriodResult: List of tuples containing performance metrics
    """
    # Convert signals to numpy arrays
    entries_np = entries.to_numpy().astype(bool)
    exits_ema_np = exits_ema.to_numpy().astype(bool)

    # Calculate longest holding period
    longest_holding_period = calculate_longest_holding_period(entries_np)
    log(f"Longest holding period: {longest_holding_period}")

    # Get stop loss from config
    stop_loss = config.get('STOP_LOSS', None)
    if stop_loss is not None:
        log(f"Using stop loss of {stop_loss*100}%")

    log(f"Processing holding periods...")
    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        # Generate PSL exit signals
        exits_psl = psl_exit(
            data['Close'].to_numpy(),
            entries_np,
            holding_period,
            short=config.get("SHORT", False),
            stop_loss=stop_loss
        )
        
        # Combine exits using numpy operations
        exits = np.logical_or(exits_ema_np, exits_psl)
        
        # Create signal column with proper position tracking
        signals = create_signal_column(
            entries_np,
            exits,
            len(data)
        )
        
        # Create test data with signals
        test_data = data.with_columns(
            pl.Series(name="Signal", values=signals)
        )
        
        # Run backtest
        pf = backtest_strategy(test_data, config, log)
        
        # Store results
        results.append((
            holding_period,
            pf.total_return(),
            pf.positions.count(),
            pf.trades.expectancy()
        ))

    return results
