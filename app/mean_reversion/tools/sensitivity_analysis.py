"""
Sensitivity Analysis Module for Mean Reversion Strategy

This module performs sensitivity analysis on mean reversion strategy parameters,
calculating performance metrics for different price change percentages.
"""

import polars as pl
from typing import List, Dict, Any, Optional, Callable
from app.mean_reversion.tools.signal_generation import is_signal_current, calculate_signals
from app.tools.stats_converter import convert_stats
from app.tools.backtest_strategy import backtest_strategy

def analyze_parameter_combination(
    data: pl.DataFrame,
    change_pct: float,
    config: Dict[str, Any],
    log: Callable
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single parameter combination.
    
    Args:
        data: Price data DataFrame
        change_pct: Price change percentage for entry
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        Optional[Dict]: Portfolio statistics if successful, None if failed
    """
    try:
        if len(data) == 0:
            log(f"Insufficient data for parameter {change_pct}", "warning")
            return None
            
        # Create strategy config for this parameter combination
        strategy_config = {
            "change_pct": change_pct,
            "USE_CURRENT": config.get("USE_CURRENT", False)
        }
        
        # Calculate signals for this parameter combination
        temp_data = calculate_signals(data.clone(), strategy_config)
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for parameter {change_pct}", "warning")
            return None
            
        current = is_signal_current(temp_data)
        portfolio = backtest_strategy(temp_data, config, log)

        stats = portfolio.stats()
        stats['Change PCT'] = change_pct
        converted_stats = convert_stats(stats, log, config)
        converted_stats['Signal Entry'] = current
        
        return converted_stats
        
    except Exception as e:
        log(f"Failed to process parameter {change_pct}: {str(e)}", "warning")
        return None

def analyze_parameter_combinations(
    data: pl.DataFrame,
    change_pcts: List[float],
    config: Dict[str, Any],
    log: Callable
) -> List[Dict[str, Any]]:
    """
    Analyze all valid parameter combinations.
    
    Args:
        data: Price data DataFrame
        change_pcts: List of price change percentages
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        List[Dict]: List of portfolio statistics for each valid combination
    """
    portfolios = []
    
    for change_pct in change_pcts:
        result = analyze_parameter_combination(data, change_pct, config, log)
        if result is not None:
            portfolios.append(result)
                    
    return portfolios
