"""
Parameter analysis module for protective stop loss analysis.

This module handles the analysis of protective stop loss parameters and their impact
on strategy performance.
"""

import numpy as np
import polars as pl
from typing import Callable
from app.tools.backtest_strategy import backtest_strategy
from app.tools.export_csv import export_csv, ExportConfig
from app.ma_cross.tools.psl_types import PSLConfig, AnalysisResult, HoldingPeriodResult
from app.ma_cross.tools.psl_exit import psl_exit
from app.ma_cross.tools.psl_metrics import (
    initialize_metric_matrices,
    calculate_portfolio_metrics,
    create_portfolio_stats,
    create_filename
)
from app.ma_cross.tools.psl_signals import create_signal_column, find_last_negative_candle
from app.ma_cross.tools.psl_data_preparation import prepare_data

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
    
    # Get stop loss from config
    stop_loss = config.get('STOP_LOSS', None)
    if stop_loss is not None:
        log(f"Using stop loss of {stop_loss*100}%")
    
    # Find last negative candle
    max_holding_period = find_last_negative_candle(
        data['Close'].to_numpy(),
        entries,
        short=config.get("SHORT", False),
        stop_loss=stop_loss,
        log=log
    )
    
    # Create holding period range
    holding_period_range = np.arange(1, max_holding_period + 2)  # +2 to include the first profitable period
    
    # Initialize metrics
    metrics = initialize_metric_matrices(len(holding_period_range))
    
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

    # Find last negative candle
    max_holding_period = find_last_negative_candle(
        data['Close'].to_numpy(),
        entries_np,
        short=config.get("SHORT", False),
        stop_loss=config.get('STOP_LOSS', None),
        log=log
    )

    # Get stop loss from config
    stop_loss = config.get('STOP_LOSS', None)
    if stop_loss is not None:
        log(f"Using stop loss of {stop_loss*100}%")

    log(f"Processing holding periods...")
    results = []
    for holding_period in range(max_holding_period + 1, 0, -1):
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
