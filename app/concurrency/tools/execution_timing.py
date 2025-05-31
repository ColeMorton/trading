"""
Execution Timing Module.

This module provides functionality to handle signal execution timing,
reducing implementation lag and improving performance.
"""

import os
from typing import Dict, Any, Optional, Callable, Tuple, List
import numpy as np
import polars as pl
from enum import Enum
from .signal_processor import SignalProcessor, SignalDefinition

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv('USE_FIXED_SIGNAL_PROC', 'true').lower() == 'true'


class ExecutionMode(Enum):
    """Enumeration of execution timing modes."""
    NEXT_PERIOD = "next_period"      # Execute signals in the next period (default, has lag)
    SAME_PERIOD = "same_period"      # Execute signals in the same period (no lag)
    OPTIMAL = "optimal"              # Use machine learning to determine optimal execution timing
    CUSTOM_DELAY = "custom_delay"    # Use a custom delay (in periods)


def apply_execution_timing(
    signals: np.ndarray,
    mode: ExecutionMode = ExecutionMode.NEXT_PERIOD,
    custom_delay: int = 1,
    log: Optional[Callable[[str, str], None]] = None
) -> np.ndarray:
    """Apply execution timing to signals.
    
    Args:
        signals: Array of signals
        mode: Execution timing mode
        custom_delay: Custom delay in periods (only used with CUSTOM_DELAY mode)
        log: Optional logging function
        
    Returns:
        np.ndarray: Signals with applied execution timing
    """
    if len(signals) == 0:
        return signals
    
    # Create a copy to avoid modifying the original
    timed_signals = np.zeros_like(signals)
    
    if mode == ExecutionMode.NEXT_PERIOD:
        # Shift signals forward by one period (default behavior with lag)
        timed_signals[1:] = signals[:-1]
    
    elif mode == ExecutionMode.SAME_PERIOD:
        # No lag - execute in the same period
        timed_signals = signals.copy()
    
    elif mode == ExecutionMode.OPTIMAL:
        # Use a simple heuristic to determine optimal timing
        # In a real implementation, this could use ML to predict optimal timing
        timed_signals = _calculate_optimal_timing(signals)
    
    elif mode == ExecutionMode.CUSTOM_DELAY:
        # Apply custom delay
        if custom_delay > 0 and custom_delay < len(signals):
            timed_signals[custom_delay:] = signals[:-custom_delay]
        else:
            if log:
                log(f"Invalid custom delay: {custom_delay}. Using default (1).", "warning")
            timed_signals[1:] = signals[:-1]
    
    else:
        # Default to next period if mode is invalid
        if log:
            log(f"Invalid execution mode: {mode}. Using next_period instead.", "warning")
        timed_signals[1:] = signals[:-1]
    
    if log:
        if USE_FIXED_SIGNAL_PROC:
            # Create temporary dataframe for signal counting
            temp_df = pl.DataFrame({
                'signal_original': signals,
                'signal_timed': timed_signals
            })
            signal_processor = SignalProcessor(use_fixed=True)
            signal_def_orig = SignalDefinition(signal_column='signal_original')
            signal_def_timed = SignalDefinition(signal_column='signal_timed')
            
            orig_counts = signal_processor.count_raw_signals(temp_df, signal_def_orig)
            timed_counts = signal_processor.count_raw_signals(temp_df, signal_def_timed)
            
            non_zero_original = orig_counts
            non_zero_timed = timed_counts
        else:
            # Legacy counting method
            non_zero_original = np.count_nonzero(signals)
            non_zero_timed = np.count_nonzero(timed_signals)
        log(f"Applied {mode.value} execution timing. Original signals: {non_zero_original}, Timed signals: {non_zero_timed}", "info")
    
    return timed_signals


def _calculate_optimal_timing(signals: np.ndarray) -> np.ndarray:
    """Calculate optimal execution timing for signals.
    
    This is a simplified implementation. In practice, this would use
    machine learning to predict the optimal execution timing based on
    historical data and market conditions.
    
    Args:
        signals: Array of signals
        
    Returns:
        np.ndarray: Signals with optimal timing
    """
    # For now, this is a simple heuristic that reduces lag for strong signals
    # and maintains lag for weaker signals
    timed_signals = np.zeros_like(signals)
    
    # Identify strong signals (absolute value > 0.5)
    strong_mask = np.abs(signals) > 0.5
    
    # Apply different timing based on signal strength
    # Strong signals: execute in same period (no lag)
    # Weak signals: execute in next period (with lag)
    timed_signals[strong_mask] = signals[strong_mask]  # No lag for strong signals
    
    # For weak signals, apply standard lag
    weak_signals = signals[~strong_mask]
    if len(weak_signals) > 0:
        timed_signals[~strong_mask][1:] = weak_signals[:-1]
    
    return timed_signals


def get_execution_mode(config: Dict[str, Any]) -> Tuple[ExecutionMode, int]:
    """Get the execution mode from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple[ExecutionMode, int]: Execution mode and custom delay
    """
    mode_str = config.get("EXECUTION_MODE", "next_period")
    custom_delay = config.get("EXECUTION_DELAY", 1)
    
    try:
        mode = ExecutionMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        mode = ExecutionMode.NEXT_PERIOD
    
    # Ensure custom_delay is an integer
    if not isinstance(custom_delay, int) or custom_delay < 0:
        custom_delay = 1
    
    return mode, custom_delay


def analyze_execution_impact(
    original_signals: np.ndarray,
    returns: np.ndarray,
    log: Optional[Callable[[str, str], None]] = None
) -> Dict[str, Any]:
    """Analyze the impact of different execution timing modes.
    
    Args:
        original_signals: Original signals
        returns: Array of returns
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Dictionary with impact analysis
    """
    if len(original_signals) != len(returns):
        if log:
            log("Signal and return arrays have different lengths", "error")
        return {}
    
    results = {}
    
    # Test different execution modes
    for mode in ExecutionMode:
        # Apply execution timing
        timed_signals = apply_execution_timing(original_signals, mode)
        
        # Calculate performance metrics
        active_returns = returns[timed_signals != 0]
        
        if len(active_returns) > 0:
            avg_return = float(np.mean(active_returns))
            win_rate = float(np.mean(active_returns > 0))
            
            # Calculate profit factor
            positive_returns = active_returns[active_returns > 0]
            negative_returns = active_returns[active_returns < 0]
            
            profit_factor = 1.0
            if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
                profit_factor = float(np.sum(positive_returns) / np.sum(np.abs(negative_returns)))
            
            results[mode.value] = {
                "avg_return": avg_return,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "signal_count": len(active_returns)
            }
    
    # Calculate impact relative to default (next_period)
    if "next_period" in results:
        baseline = results["next_period"]
        
        for mode, metrics in results.items():
            if mode != "next_period":
                impact = {
                    "avg_return_impact": metrics["avg_return"] - baseline["avg_return"],
                    "win_rate_impact": metrics["win_rate"] - baseline["win_rate"],
                    "profit_factor_impact": metrics["profit_factor"] - baseline["profit_factor"]
                }
                results[mode]["impact"] = impact
    
    if log:
        log(f"Analyzed execution timing impact across {len(results)} modes", "info")
    
    return results