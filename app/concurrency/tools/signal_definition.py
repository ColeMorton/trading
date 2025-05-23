"""
Signal Definition Module.

This module provides different methods for defining and extracting signals
from position data, allowing for consistent signal definition across the system.
"""

from typing import Dict, Any, Optional, Callable, Literal
from enum import Enum
import polars as pl
import numpy as np


class SignalDefinitionMode(Enum):
    """Enumeration of signal definition modes."""
    POSITION_CHANGE = "position_change"  # Signal on position changes (0→1, 1→0)
    COMPLETE_TRADE = "complete_trade"    # Signal represents complete trades (entry to exit)
    ENTRY_ONLY = "entry_only"            # Signal only on entries (0→1)
    EXIT_ONLY = "exit_only"              # Signal only on exits (1→0)


def extract_signals(
    df: pl.DataFrame,
    mode: SignalDefinitionMode = SignalDefinitionMode.POSITION_CHANGE,
    position_column: str = "Position",
    log: Optional[Callable[[str, str], None]] = None
) -> pl.DataFrame:
    """Extract signals from position data using the specified mode.
    
    Args:
        df: DataFrame with position data
        mode: Signal definition mode
        position_column: Name of the position column
        log: Optional logging function
        
    Returns:
        pl.DataFrame: DataFrame with Date and signal columns
    """
    if position_column not in df.columns:
        if log:
            log(f"Position column '{position_column}' not found in DataFrame", "error")
        return pl.DataFrame({"Date": [], "signal": []})
    
    # Ensure Date column exists
    if "Date" not in df.columns:
        if log:
            log("Date column not found in DataFrame", "error")
        return pl.DataFrame({"Date": [], "signal": []})
    
    # Extract signals based on mode
    if mode == SignalDefinitionMode.POSITION_CHANGE:
        # Signal on any position change (standard method)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("signal")
        )
    
    elif mode == SignalDefinitionMode.COMPLETE_TRADE:
        # Signal represents complete trades (entry to exit)
        # This requires post-processing to match entries with exits
        position_changes = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("change")
        )
        
        # Extract entries and exits
        entries = position_changes.filter(pl.col("change") > 0)
        exits = position_changes.filter(pl.col("change") < 0)
        
        # Create trade signals (each trade has entry and exit dates)
        # For compatibility with existing code, we'll still use the position change format
        # but ensure the metadata includes trade information
        signals_df = position_changes.with_columns(
            pl.col("change").alias("signal")
        ).drop("change")
        
        # Add trade metadata if logging is enabled
        if log:
            log(f"Extracted {len(entries)} entries and {len(exits)} exits for complete trades", "info")
    
    elif mode == SignalDefinitionMode.ENTRY_ONLY:
        # Signal only on entries (0→1)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.when(pl.col(position_column).diff() > 0)
            .then(pl.col(position_column).diff())
            .otherwise(0)
            .alias("signal")
        )
    
    elif mode == SignalDefinitionMode.EXIT_ONLY:
        # Signal only on exits (1→0)
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.when(pl.col(position_column).diff() < 0)
            .then(pl.col(position_column).diff())
            .otherwise(0)
            .alias("signal")
        )
    
    else:
        # Default to position change if mode is invalid
        if log:
            log(f"Invalid signal definition mode: {mode}. Using position_change instead.", "warning")
        signals_df = df.select(["Date", position_column]).with_columns(
            pl.col(position_column).diff().alias("signal")
        )
    
    return signals_df


def get_signal_definition_mode(config: Dict[str, Any]) -> SignalDefinitionMode:
    """Get the signal definition mode from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        SignalDefinitionMode: Signal definition mode
    """
    mode_str = config.get("SIGNAL_DEFINITION_MODE", "position_change")
    
    try:
        return SignalDefinitionMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        return SignalDefinitionMode.POSITION_CHANGE


def align_signal_definitions(
    backtest_signals: np.ndarray,
    implementation_signals: np.ndarray,
    dates: np.ndarray,
    log: Optional[Callable[[str, str], None]] = None
) -> Dict[str, np.ndarray]:
    """Align signal definitions between backtest and implementation.
    
    This function helps reconcile differences between backtest and implementation
    signal definitions, making it easier to compare performance.
    
    Args:
        backtest_signals: Signals from backtest
        implementation_signals: Signals from implementation
        dates: Array of dates corresponding to signals
        log: Optional logging function
        
    Returns:
        Dict[str, np.ndarray]: Dictionary with aligned signals
    """
    if len(backtest_signals) != len(implementation_signals) or len(backtest_signals) != len(dates):
        if log:
            log("Signal arrays have different lengths and cannot be aligned", "error")
        return {
            "backtest_signals": backtest_signals,
            "implementation_signals": implementation_signals,
            "aligned": False
        }
    
    # Convert implementation signals to match backtest format
    # This is a simplified approach - in practice, more sophisticated
    # alignment might be needed based on specific signal definitions
    aligned_implementation = np.zeros_like(implementation_signals)
    
    # Track active trades in backtest
    active_trade = False
    trade_start_idx = 0
    
    for i in range(len(backtest_signals)):
        # Detect trade entry in backtest
        if backtest_signals[i] > 0 and not active_trade:
            active_trade = True
            trade_start_idx = i
        
        # Detect trade exit in backtest
        elif backtest_signals[i] < 0 and active_trade:
            active_trade = False
            
            # Find corresponding implementation signals during this trade period
            impl_signals_during_trade = implementation_signals[trade_start_idx:i+1]
            
            # If implementation had any signals during this period, consider it aligned
            if np.any(impl_signals_during_trade != 0):
                aligned_implementation[trade_start_idx:i+1] = implementation_signals[trade_start_idx:i+1]
    
    if log:
        match_rate = np.mean(np.sign(aligned_implementation) == np.sign(backtest_signals))
        log(f"Signal alignment complete. Match rate: {match_rate:.2%}", "info")
    
    return {
        "backtest_signals": backtest_signals,
        "implementation_signals": implementation_signals,
        "aligned_implementation": aligned_implementation,
        "aligned": True
    }