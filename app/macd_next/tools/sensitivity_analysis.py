"""
Sensitivity Analysis Module for MACD Cross Strategy

This module performs sensitivity analysis on MACD cross strategy parameters,
calculating performance metrics for different combinations of short/long/signal windows.
"""

import polars as pl
from typing import List, Dict, Any, Optional, Callable, Iterator
from app.macd_next.tools.signal_generation import generate_macd_signals
from app.tools.stats_converter import convert_stats
from app.tools.backtest_strategy import backtest_strategy

def analyze_parameter_combination(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    signal_window: int,
    config: Dict[str, Any],
    log: Callable
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single MACD parameter combination.
    
    Args:
        data: Price data DataFrame
        short_window: Short-term EMA period
        long_window: Long-term EMA period
        signal_window: Signal line EMA period
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        Optional[Dict]: Portfolio statistics if successful, None if failed
    """
    try:
        log(f"Analyzing windows - Short: {short_window}, Long: {long_window}, Signal: {signal_window}", "info")
        log(f"Data length: {len(data)}, Required length: {max(short_window, long_window, signal_window)}", "info")
        
        if len(data) == 0:
            log(f"Insufficient data for parameters {short_window}/{long_window}/{signal_window}", "warning")
            return None
            
        # Skip invalid window combinations
        if long_window <= short_window:
            log(f"Invalid window combination: Long window {long_window} <= Short window {short_window}", "debug")
            return None
            
        # Create strategy config for this parameter combination
        strategy_config = config.copy()
        strategy_config.update({
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window
        })
        
        # Calculate signals for this parameter combination
        temp_data = generate_macd_signals(data.clone(), strategy_config)
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for parameters {short_window}/{long_window}/{signal_window}", "warning")
            return None
            
        # Count signals and positions
        signal_count = temp_data.filter(pl.col("Signal") != 0).height
        position_count = temp_data.filter(pl.col("Signal").shift(1).fill_null(0) != 0).height
        log(f"Windows {short_window}, {long_window}, {signal_window}: {position_count} positions from {signal_count} signals", "info")
            
        # Get current signal state
        current = temp_data.tail(1).select("Signal").item() != 0
        
        # Check if there's an exit signal
        direction = config.get("DIRECTION", "Long").lower()
        if direction == "long":
            exit_signal = (temp_data.tail(1).select("MACD").item() < temp_data.tail(1).select("Signal_Line").item() and
                          temp_data.tail(2).head(1).select("MACD").item() >= temp_data.tail(2).head(1).select("Signal_Line").item())
        else:
            exit_signal = (temp_data.tail(1).select("MACD").item() > temp_data.tail(1).select("Signal_Line").item() and
                          temp_data.tail(2).head(1).select("MACD").item() <= temp_data.tail(2).head(1).select("Signal_Line").item())
        
        log(f"Windows {short_window}, {long_window}, {signal_window}: Entry signal: {current}, Exit signal: {exit_signal}", "info")
        
        # Backtest the strategy
        portfolio = backtest_strategy(temp_data, config, log)
        
        # Get and convert statistics
        stats = portfolio.stats()
        
        # Use correct column names from the start
        stats.update({
            'Short Window': short_window,
            'Long Window': long_window,
            'Signal Window': signal_window,
            'Strategy Type': 'MACD',  # Ensure Strategy Type is set to MACD
            'Signal Count': signal_count,  # Add Signal Count
            'Position Count': position_count,  # Add Position Count
            'Signal Entry': current,  # Add Signal Entry flag
            'Signal Exit': exit_signal  # Add Signal Exit flag
        })
        
        # Get ticker from config
        if 'TICKER' in config:
            ticker = config['TICKER']
            stats['Ticker'] = ticker
        
        converted_stats = convert_stats(stats, log, config, current)
        
        # Ensure these fields are present in the converted stats
        if 'Signal Count' not in converted_stats:
            converted_stats['Signal Count'] = signal_count
        if 'Position Count' not in converted_stats:
            converted_stats['Position Count'] = position_count
        if 'Strategy Type' not in converted_stats:
            converted_stats['Strategy Type'] = 'MACD'
        if 'Signal Entry' not in converted_stats:
            converted_stats['Signal Entry'] = current
        if 'Signal Exit' not in converted_stats:
            converted_stats['Signal Exit'] = exit_signal
        if 'Ticker' in stats and 'Ticker' not in converted_stats:
            converted_stats['Ticker'] = stats['Ticker']
        
        return converted_stats
        
    except Exception as e:
        log(f"Failed to process parameters {short_window}/{long_window}/{signal_window}: {str(e)}", "warning")
        return None

def analyze_parameter_combinations(
    data: pl.DataFrame,
    short_windows: Iterator[int],
    long_windows: Iterator[int],
    signal_windows: Iterator[int],
    config: Dict[str, Any],
    log: Callable
) -> List[Dict[str, Any]]:
    """
    Analyze all valid MACD parameter combinations.
    
    Args:
        data: Price data DataFrame
        short_windows: Range of short-term EMA periods
        long_windows: Range of long-term EMA periods
        signal_windows: Range of signal line EMA periods
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        List[Dict]: List of portfolio statistics for each valid combination
    """
    portfolios = []
    
    for short_window in short_windows:
        for long_window in long_windows:
            if long_window <= short_window:
                continue
                
            for signal_window in signal_windows:
                result = analyze_parameter_combination(
                    data=data,
                    short_window=short_window,
                    long_window=long_window,
                    signal_window=signal_window,
                    config=config,
                    log=log
                )
                if result is not None:
                    portfolios.append(result)
                    
    return portfolios
