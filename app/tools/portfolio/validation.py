"""
Portfolio Validation Module

This module provides functions for validating portfolio data against schemas
and reporting errors.
"""

import polars as pl
from typing import Dict, List, Any, Callable, Optional, Tuple

def validate_portfolio_schema(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    required_columns: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that a portfolio DataFrame has the required columns.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function
        required_columns: List of required column names (default: ['TICKER'])

    Returns:
        Tuple of (is_valid, error_messages)
    """
    if required_columns is None:
        required_columns = ['TICKER']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        return False, [error_msg]
    
    return True, []

def validate_strategy_config(
    strategy: Dict[str, Any],
    log: Callable[[str, str], None]
) -> Tuple[bool, List[str]]:
    """
    Validate a strategy configuration dictionary.

    Args:
        strategy: Strategy configuration dictionary
        log: Logging function

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ['TICKER', 'SHORT_WINDOW', 'LONG_WINDOW']
    for field in required_fields:
        if field not in strategy:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        for error in errors:
            log(error, "error")
        return False, errors
    
    # Validate numeric fields
    numeric_fields = {
        'SHORT_WINDOW': int,
        'LONG_WINDOW': int,
        'STOP_LOSS': float,
        'POSITION_SIZE': float,
        'RSI_WINDOW': int,
        'RSI_THRESHOLD': int,
        'SIGNAL_WINDOW': int
    }
    
    for field, field_type in numeric_fields.items():
        if field in strategy:
            try:
                # Attempt to convert to the expected type
                strategy[field] = field_type(strategy[field])
            except (ValueError, TypeError):
                errors.append(f"Invalid {field} value: {strategy[field]}")
    
    # Validate window relationships
    if 'SHORT_WINDOW' in strategy and 'LONG_WINDOW' in strategy:
        if strategy['SHORT_WINDOW'] >= strategy['LONG_WINDOW']:
            errors.append(f"SHORT_WINDOW ({strategy['SHORT_WINDOW']}) must be less than LONG_WINDOW ({strategy['LONG_WINDOW']})")
    
    # Validate stop loss range
    if 'STOP_LOSS' in strategy and strategy['STOP_LOSS'] is not None:
        stop_loss = strategy['STOP_LOSS']
        if stop_loss <= 0 or stop_loss > 100:
            errors.append(f"STOP_LOSS ({stop_loss}) must be between 0 and 100")
    
    if errors:
        for error in errors:
            log(error, "error")
        return False, errors
    
    return True, []

def validate_portfolio_configs(
    strategies: List[Dict[str, Any]],
    log: Callable[[str, str], None]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate a list of strategy configurations.

    Args:
        strategies: List of strategy configuration dictionaries
        log: Logging function

    Returns:
        Tuple of (is_valid, valid_strategies)
    """
    valid_strategies = []
    all_valid = True
    
    for strategy in strategies:
        is_valid, _ = validate_strategy_config(strategy, log)
        if is_valid:
            valid_strategies.append(strategy)
        else:
            all_valid = False
    
    return all_valid, valid_strategies