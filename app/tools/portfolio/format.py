"""
Portfolio Format Conversion Module

This module provides functions for converting between different portfolio formats
and standardizing column names and data types.
"""

import polars as pl
from typing import Dict, List, Any, Callable, Optional

def standardize_portfolio_columns(
    df: pl.DataFrame,
    log: Callable[[str, str], None]
) -> pl.DataFrame:
    """
    Standardize portfolio column names to a consistent format.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function

    Returns:
        DataFrame with standardized column names
    """
    # Define column name mappings (original -> standardized)
    column_mappings = {
        # Ticker columns
        'Ticker': 'TICKER',
        'ticker': 'TICKER',
        'Symbol': 'TICKER',
        'symbol': 'TICKER',
        
        # Window columns
        'Short Window': 'SHORT_WINDOW',
        'short_window': 'SHORT_WINDOW',
        'Long Window': 'LONG_WINDOW',
        'long_window': 'LONG_WINDOW',
        
        # Strategy type columns
        'Use SMA': 'USE_SMA',
        'use_sma': 'USE_SMA',
        'Strategy Type': 'STRATEGY_TYPE',
        'strategy_type': 'STRATEGY_TYPE',
        'type': 'STRATEGY_TYPE',
        
        # Stop loss columns
        'Stop Loss': 'STOP_LOSS',
        'stop_loss': 'STOP_LOSS',
        
        # Direction columns
        'Direction': 'DIRECTION',
        'direction': 'DIRECTION',
        
        # Timeframe columns
        'Timeframe': 'TIMEFRAME',
        'timeframe': 'TIMEFRAME',
        
        # RSI columns
        'RSI Window': 'RSI_WINDOW',
        'rsi_window': 'RSI_WINDOW',
        'RSI Threshold': 'RSI_THRESHOLD',
        'rsi_threshold': 'RSI_THRESHOLD',
        
        # MACD columns
        'Signal Window': 'SIGNAL_WINDOW',
        'signal_window': 'SIGNAL_WINDOW',
        
        # Position size columns
        'Position Size': 'POSITION_SIZE',
        'position_size': 'POSITION_SIZE',
    }
    
    # Create a mapping of existing columns
    rename_map = {}
    for orig, std in column_mappings.items():
        if orig in df.columns and std not in df.columns:
            rename_map[orig] = std
            
    # Apply renaming if needed
    if rename_map:
        log(f"Standardizing column names: {rename_map}", "info")
        df = df.rename(rename_map)
    
    return df

def convert_csv_to_strategy_config(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert a CSV DataFrame to a list of strategy configurations.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function
        config: Configuration dictionary with default values

    Returns:
        List of strategy configuration dictionaries
    """
    # Standardize column names
    df = standardize_portfolio_columns(df, log)
    
    # Validate required columns
    required_columns = ['TICKER']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        raise ValueError(error_msg)
    
    # Get timeframe setting from config
    use_hourly = config.get("CSV_USE_HOURLY", config.get("USE_HOURLY", False))
    timeframe = "Hourly" if use_hourly else "Daily"
    
    # Convert DataFrame rows to strategy configurations
    strategies = []
    for row in df.iter_rows(named=True):
        ticker = row["TICKER"]
        log(f"Processing strategy configuration for {ticker}", "info")
        
        # Determine strategy type
        strategy_type = None
        
        # Check if STRATEGY_TYPE is directly provided
        if "STRATEGY_TYPE" in row:
            strategy_type = row["STRATEGY_TYPE"]
        
        # Check if type is directly provided (from JSON portfolios)
        elif "type" in row:
            strategy_type = row["type"]
        
        # Otherwise determine from USE_SMA
        else:
            use_sma = row.get("USE_SMA", True)
            if isinstance(use_sma, str):
                use_sma = use_sma.lower() in ['true', 'yes', '1']
            strategy_type = "SMA" if use_sma else "EMA"
        
        # Set default values
        direction = row.get("DIRECTION", "Long")
        
        # Determine if this is a MACD strategy
        is_macd = strategy_type == "MACD" or "SIGNAL_WINDOW" in row
        
        # Create strategy configuration
        strategy_config = {
            "TICKER": ticker,
            "USE_SMA": strategy_type == "SMA",
            "STRATEGY_TYPE": strategy_type,
            "type": strategy_type,  # Add explicit type field for compatibility
            "DIRECTION": direction,
            "USE_HOURLY": use_hourly,
            "USE_RSI": False,
            "BASE_DIR": config.get("BASE_DIR", "."),
            "REFRESH": config.get("REFRESH", True),
        }
        
        # Add window parameters if available
        if "SHORT_WINDOW" in row:
            strategy_config["SHORT_WINDOW"] = int(row["SHORT_WINDOW"])
        elif "SMA_FAST" in row and use_sma:
            strategy_config["SHORT_WINDOW"] = int(row["SMA_FAST"])
        elif "EMA_FAST" in row and not use_sma:
            strategy_config["SHORT_WINDOW"] = int(row["EMA_FAST"])
        
        if "LONG_WINDOW" in row:
            strategy_config["LONG_WINDOW"] = int(row["LONG_WINDOW"])
        elif "SMA_SLOW" in row and use_sma:
            strategy_config["LONG_WINDOW"] = int(row["SMA_SLOW"])
        elif "EMA_SLOW" in row and not use_sma:
            strategy_config["LONG_WINDOW"] = int(row["EMA_SLOW"])
        
        # Add stop loss if available
        if "STOP_LOSS" in row and row["STOP_LOSS"] is not None:
            try:
                stop_loss = float(row["STOP_LOSS"])
                strategy_config["STOP_LOSS"] = stop_loss
            except (ValueError, TypeError):
                log(f"Invalid stop loss value for {ticker}: {row['STOP_LOSS']}", "warning")
        
        # Add position size if available
        if "POSITION_SIZE" in row and row["POSITION_SIZE"] is not None:
            try:
                position_size = float(row["POSITION_SIZE"])
                strategy_config["POSITION_SIZE"] = position_size
            except (ValueError, TypeError):
                log(f"Invalid position size value for {ticker}: {row['POSITION_SIZE']}", "warning")
        
        # Add RSI parameters if available
        has_rsi_period = "RSI_WINDOW" in row and row["RSI_WINDOW"] is not None
        has_rsi_threshold = "RSI_THRESHOLD" in row and row["RSI_THRESHOLD"] is not None
        
        # Enable RSI if either parameter is provided
        if has_rsi_period or has_rsi_threshold:
            strategy_config["USE_RSI"] = True
            
            # Add RSI window if available
            if has_rsi_period:
                strategy_config["RSI_WINDOW"] = int(row["RSI_WINDOW"])
                log(f"Using RSI window: {strategy_config['RSI_WINDOW']} for {ticker}", "info")
            else:
                # Use default RSI window if not provided
                strategy_config["RSI_WINDOW"] = 14
                log(f"Using default RSI window: 14 for {ticker}", "info")
                
            # Add RSI threshold if available
            if has_rsi_threshold:
                strategy_config["RSI_THRESHOLD"] = int(row["RSI_THRESHOLD"])
                log(f"Using RSI threshold: {strategy_config['RSI_THRESHOLD']} for {ticker}", "info")
            else:
                # Use default RSI threshold if not provided
                strategy_config["RSI_THRESHOLD"] = 70 if direction == "Long" else 30
                log(f"Using default RSI threshold: {strategy_config['RSI_THRESHOLD']} for {ticker}", "info")
        
        # Add MACD signal window if available
        if "SIGNAL_WINDOW" in row and row["SIGNAL_WINDOW"] is not None:
            strategy_config["SIGNAL_WINDOW"] = int(row["SIGNAL_WINDOW"])
        
        strategies.append(strategy_config)
    
    return strategies