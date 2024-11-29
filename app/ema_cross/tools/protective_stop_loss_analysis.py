"""
Protective Stop Loss Analysis Module

This module contains functions for analyzing protective stop loss (PSL) strategies
in combination with EMA cross signals.
"""

import vectorbt as vbt
import polars as pl
import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from app.tools.file_utils import convert_stats
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi
from app.ema_cross.tools.backtest_strategy import backtest_strategy
from app.tools.export_csv import export_csv, ExportConfig

def psl_exit(price: np.ndarray, entry_price: np.ndarray, holding_period: int, short: bool, stop_loss: Optional[float] = None) -> np.ndarray:
    """
    Generate Price Stop Loss (PSL) exit signals.

    The PSL strategy monitors price action over a specified holding period and
    generates exit signals based on adverse price movements during that period.
    If stop_loss is provided, also exits when price moves against position by stop_loss percentage.

    Args:
        price (np.ndarray): Array of price data
        entry_price (np.ndarray): Array of entry prices
        holding_period (int): The holding period for the PSL
        short (bool): True if it's a short trade, False for long trades
        stop_loss (float, optional): Stop loss percentage as decimal (e.g. 0.03 for 3%)

    Returns:
        np.ndarray: Array of PSL exit signals (1 for exit, 0 for hold)
    """
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            # Check protective stop loss condition over holding period
            if short:
                if np.any(price[i-holding_period:i] >= entry_price[i-holding_period]):
                    exit_signal[i] = 1
            else:
                if np.any(price[i-holding_period:i] <= entry_price[i-holding_period]):
                    exit_signal[i] = 1
                    
            # Check stop loss condition on current bar
            if stop_loss is not None:
                if short:
                    # For shorts, exit if price rises above entry by stop loss percentage
                    if price[i] >= entry_price[i] * (1 + stop_loss):
                        exit_signal[i] = 1
                else:
                    # For longs, exit if price falls below entry by stop loss percentage
                    if price[i] <= entry_price[i] * (1 - stop_loss):
                        exit_signal[i] = 1
                        
    return exit_signal

def analyze_protective_stop_loss_parameters(
    data: pl.DataFrame,
    config: dict,
    log: Callable
) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        config (dict): The configuration dictionary
        log (callable): Logging function

    Returns:
        Tuple containing:
            - Dict[str, np.ndarray]: Dictionary containing metric arrays for:
                - trades: Number of trades
                - returns: Total returns
                - sharpe_ratio: Sharpe ratios
                - win_rate: Win rates
            - np.ndarray: Array of holding periods used
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
    
    # Generate entry/exit signals
    entries, _ = calculate_ma_signals(data, config)
    entries = entries.to_numpy().astype(bool)
    
    # Get entry prices for PSL calculation
    entry_price = data.with_columns(
        pl.when(pl.lit(entries))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']
    
    # Calculate longest holding period from actual trades
    longest_trade = pl.Series((entries != np.roll(entries, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()
    log(f"Calculated longest holding period: {longest_holding_period} days")
    
    # Create holding period range from 1 to longest holding period
    holding_period_range = np.arange(1, longest_holding_period + 1)
    
    # Initialize metric matrices
    num_periods = len(holding_period_range)
    trades_matrix = np.zeros(num_periods)
    returns_matrix = np.zeros(num_periods)
    sharpe_matrix = np.zeros(num_periods)
    win_rate_matrix = np.zeros(num_periods)
    
    # Get stop loss from config if enabled
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
            entry_price.to_numpy(),
            holding_period,
            short=config.get("SHORT", False),
            stop_loss=stop_loss
        )
        
        # Create signal column (1 for entry, 0 for exit)
        data = data.with_columns(
            pl.Series(name="Signal", values=np.where(entries, 1, np.where(exits_psl, 0, 0)))
        )
        
        # Run backtest using backtest_strategy module
        pf = backtest_strategy(data, config, log)
        stats = pf.stats()
        converted_stats = convert_stats(stats)
        
        # Add holding period parameter to stats
        converted_stats["Holding Period"] = holding_period
        portfolios.append(converted_stats)

        # Store metrics
        trades_matrix[i] = pf.positions.count()
        returns_matrix[i] = pf.total_return()
        sharpe_matrix[i] = pf.sharpe_ratio()
        win_rate_matrix[i] = pf.trades.win_rate()

    # Create filename with MA windows and RSI if used
    ticker_prefix = config.get("TICKER", "")
    if isinstance(ticker_prefix, list):
        ticker_prefix = ticker_prefix[0] if ticker_prefix else ""
    
    rsi_suffix = f"_RSI_{config['RSI_PERIOD']}_{config['RSI_THRESHOLD']}" if config.get('USE_RSI', False) else ""
    stop_loss_suffix = f"_SL_{config['STOP_LOSS']}" if config.get('STOP_LOSS') is not None else ""
    filename = f"{ticker_prefix}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}_{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}{rsi_suffix}{stop_loss_suffix}.csv"
    
    # Export portfolios
    export_config = ExportConfig(BASE_DIR=config["BASE_DIR"], TICKER=config.get("TICKER"))
    export_csv(portfolios, "ma_cross", export_config, "protective_stop_loss", filename)
    
    return {
        'trades': trades_matrix,
        'returns': returns_matrix,
        'sharpe_ratio': sharpe_matrix,
        'win_rate': win_rate_matrix
    }, holding_period_range

def analyze_holding_periods(
    data: pl.DataFrame,
    entries: pl.Series,
    exits_ema: pl.Series,
    config: dict,
    log: callable
) -> List[Tuple[int, float, int, float]]:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        entries (pl.Series): Series of entry signals
        exits_ema (pl.Series): Series of EMA-based exit signals
        config (dict): The configuration dictionary
        log (callable): Logging function

    Returns:
        List[Tuple[int, float, int, float]]: List of tuples containing:
            - Holding period
            - Total return
            - Number of positions
            - Expectancy
    """
    # Convert entries to numpy array and ensure boolean type
    entries_np = entries.to_numpy().astype(bool)
    
    entry_price = data.with_columns(
        pl.when(pl.lit(entries_np))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']

    # Calculate longest holding period
    longest_trade = pl.Series((entries_np != np.roll(entries_np, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()
    log(f"Longest holding period: {longest_holding_period}")

    # Convert exits_ema to numpy array and ensure boolean type
    exits_ema_np = exits_ema.to_numpy().astype(bool)

    # Get stop loss from config
    stop_loss = config.get('STOP_LOSS', None)
    if stop_loss is not None:
        log(f"Using stop loss of {stop_loss*100}%")

    log(f"Processing holding periods...")
    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        exits_psl = psl_exit(
            data['Close'].to_numpy(), 
            entry_price.to_numpy(), 
            holding_period, 
            short=config.get("SHORT", False),
            stop_loss=stop_loss
        )
        # Combine exits using numpy operations
        exits = np.logical_or(exits_ema_np, exits_psl)
        
        # Create signal column (1 for entry, 0 for exit)
        data_with_signals = data.with_columns(
            pl.Series(name="Signal", values=np.where(entries_np, 1, np.where(exits, 0, 0)))
        )
        
        # Run backtest using backtest_strategy module
        pf = backtest_strategy(data_with_signals, config, log)
        
        total_return = pf.total_return()
        num_positions = pf.positions.count()
        expectancy = pf.trades.expectancy()
        results.append((holding_period, total_return, num_positions, expectancy))

    return results
