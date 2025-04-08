"""
Portfolio Validation Module

This module provides functions for validating portfolio data against schemas
and reporting errors.
"""

import polars as pl
from typing import Dict, List, Any, Callable, Optional, Tuple
from app.tools.portfolio.strategy_types import STRATEGY_TYPE_FIELDS
from app.tools.portfolio.strategy_utils import get_strategy_type_for_export

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
    
    # Check for TICKER which is required for all strategies
    if 'TICKER' not in strategy:
        errors.append("Missing required field: TICKER")
        
    # Get strategy type using the centralized utility function
    strategy_type = get_strategy_type_for_export(strategy)
    
    # Define required fields based on strategy type
    ticker = strategy.get('TICKER', 'Unknown')
    
    if strategy_type == 'ATR':
        # ATR strategy requires length and multiplier (check both lowercase and uppercase)
        required_fields = [('length', 'LENGTH'), ('multiplier', 'MULTIPLIER')]
        for field_pair in required_fields:
            if field_pair[0] not in strategy and field_pair[1] not in strategy:
                errors.append(f"Missing required field: {field_pair[0]} or {field_pair[1]}")
    elif strategy_type == 'MACD':
        # MACD strategies require SHORT_WINDOW, LONG_WINDOW, and SIGNAL_WINDOW
        required_fields = ['SHORT_WINDOW', 'LONG_WINDOW', 'SIGNAL_WINDOW']
        for field in required_fields:
            if field not in strategy:
                errors.append(f"Missing required field for MACD strategy {ticker}: {field}")
            elif strategy[field] is None:
                errors.append(f"Field {field} cannot be null for MACD strategy {ticker}")
        
        # Validate window relationships for MACD
        if all(field in strategy and strategy[field] is not None for field in ['SHORT_WINDOW', 'LONG_WINDOW', 'SIGNAL_WINDOW']):
            if strategy['SHORT_WINDOW'] >= strategy['LONG_WINDOW']:
                errors.append(f"SHORT_WINDOW ({strategy['SHORT_WINDOW']}) must be less than LONG_WINDOW ({strategy['LONG_WINDOW']}) for MACD strategy {ticker}")
            if strategy['SIGNAL_WINDOW'] <= 0:
                errors.append(f"SIGNAL_WINDOW ({strategy['SIGNAL_WINDOW']}) must be greater than 0 for MACD strategy {ticker}")
    else:
        # MA strategies require SHORT_WINDOW and LONG_WINDOW
        required_fields = ['SHORT_WINDOW', 'LONG_WINDOW']
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
        'SIGNAL_WINDOW': int,
        'length': int,
        'LENGTH': int,
        'multiplier': float,
        'MULTIPLIER': float
    }
    
    for field, field_type in numeric_fields.items():
        if field in strategy:
            # Skip None values
            if strategy[field] is None:
                continue
                
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
        stop_loss_float = float(strategy['STOP_LOSS'])
        # Convert percentage (0-100) to decimal (0-1)
        stop_loss_decimal = stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
        if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
            errors.append(f"Stop loss for {strategy.get('TICKER', 'Unknown')} ({stop_loss_float}%) is outside valid range (0-100%)")
        strategy['STOP_LOSS'] = stop_loss_decimal
    
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