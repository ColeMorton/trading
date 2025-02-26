"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from JSON and CSV files. It handles parsing of required and optional strategy parameters
with appropriate type conversion.

CSV files must contain the following columns:
- Ticker: Asset symbol
- Use SMA: Boolean indicating whether to use SMA (True) or EMA (False)
- Short Window: Period for short moving average
- Long Window: Period for long moving average

Default values for CSV files:
- direction: Long
- USE_RSI: False
- USE_HOURLY: Controlled by CSV_USE_HOURLY configuration option (default: False for Daily)
"""

from pathlib import Path
from typing import List, Callable, Dict
import polars as pl
from app.concurrency.tools.types import StrategyConfig

def load_portfolio_from_csv(csv_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Load portfolio configuration from CSV file.

    Args:
        csv_path (Path): Path to the CSV file containing strategy configurations
        log (Callable[[str, str], None]): Logging function for status updates
        config (Dict): Configuration dictionary containing BASE_DIR, REFRESH, and CSV_USE_HOURLY settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV file is empty or missing required columns
    """
    log(f"Loading portfolio configuration from {csv_path}", "info")
    
    if not csv_path.exists():
        log(f"Portfolio file not found: {csv_path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {csv_path}")
        
    # Read CSV file using Polars
    df = pl.read_csv(csv_path)
    log(f"Successfully read CSV file with {len(df)} strategies", "info")
    
    # Validate required columns
    required_columns = ["Ticker", "Use SMA", "Short Window", "Long Window"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns in CSV: {', '.join(missing_columns)}"
        log(error_msg, "error")
        raise ValueError(error_msg)
    
    # Get timeframe setting from config
    use_hourly = config.get("CSV_USE_HOURLY", False)
    timeframe = "Hourly" if use_hourly else "Daily"
    log(f"Using {timeframe} timeframe for all strategies in CSV file as set by CSV_USE_HOURLY: {use_hourly}", "info")
    
    # Convert DataFrame rows to StrategyConfig objects
    portfolio = []
    for row in df.iter_rows(named=True):
        ticker = row["Ticker"]
        log(f"Processing strategy configuration for {ticker}", "info")
        
        # Determine strategy type based on Use SMA column
        strategy_type = "SMA" if row["Use SMA"] else "EMA"
        
        # Set default values
        direction = "Long"
        
        config_entry: StrategyConfig = {
            "TICKER": ticker,
            "SHORT_WINDOW": int(row["Short Window"]),
            "LONG_WINDOW": int(row["Long Window"]),
            "BASE_DIR": config["BASE_DIR"],
            "REFRESH": config["REFRESH"],
            "USE_RSI": False,
            "USE_HOURLY": use_hourly,  # Use CSV_USE_HOURLY setting
            "USE_SMA": strategy_type == "SMA",
            "STRATEGY_TYPE": strategy_type,
            "DIRECTION": direction
        }
        
        # Log complete strategy configuration
        strategy_details = [
            f"TICKER: {config_entry['TICKER']}",
            f"Strategy Type: {strategy_type}",
            f"Direction: {direction}",
            f"Timeframe: {timeframe}",
            f"SHORT_WINDOW: {config_entry['SHORT_WINDOW']}",
            f"LONG_WINDOW: {config_entry['LONG_WINDOW']}",
            f"USE_RSI: {config_entry['USE_RSI']}",
            f"USE_HOURLY: {config_entry['USE_HOURLY']} (from CSV_USE_HOURLY config)",
            f"USE_SMA: {config_entry['USE_SMA']}",
            f"BASE_DIR: {config_entry['BASE_DIR']}",
            f"REFRESH: {config_entry['REFRESH']}"
        ]
        
        log(f"Strategy Configuration:\n" + "\n".join(strategy_details), "info")
        portfolio.append(config_entry)
    
    log(f"Successfully loaded {len(portfolio)} strategy configurations", "info")
    return portfolio

def load_portfolio_from_json(json_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Load portfolio configuration from JSON file.

    Args:
        json_path (Path): Path to the JSON file containing strategy configurations
        log (Callable[[str, str], None]): Logging function for status updates
        config (Dict): Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If JSON file does not exist
        ValueError: If JSON file is empty or malformed
    """
    log(f"Loading portfolio configuration from {json_path}", "info")
    
    if not json_path.exists():
        log(f"Portfolio file not found: {json_path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {json_path}")
        
    # Read JSON file using Polars
    df = pl.read_json(json_path)
    log(f"Successfully read JSON file with {len(df)} strategies", "info")
    
    # Convert DataFrame rows to StrategyConfig objects
    portfolio = []
    for row in df.iter_rows(named=True):
        ticker = row["ticker"]
        log(f"Processing strategy configuration for {ticker}", "info")
        
        # Determine strategy type and timeframe settings
        strategy_type = row.get("type", "EMA").upper()
        timeframe = row.get("timeframe", "Daily")
        
        # Check if RSI fields exist and have non-None values
        rsi_period = row.get("rsi_period")
        rsi_threshold = row.get("rsi_threshold")
        has_rsi = rsi_period is not None and rsi_threshold is not None
        
        # Get direction with default to "Long"
        direction = row.get("direction", "Long")
        
        config_entry: StrategyConfig = {
            "TICKER": ticker,
            "SHORT_WINDOW": int(row["short_window"]),
            "LONG_WINDOW": int(row["long_window"]),
            "BASE_DIR": config["BASE_DIR"],
            "REFRESH": config["REFRESH"],
            "USE_RSI": has_rsi,
            "USE_HOURLY": timeframe.lower() == "hourly",
            "USE_SMA": strategy_type == "SMA",  # Set based on strategy type
            "STRATEGY_TYPE": strategy_type,  # Store the actual strategy type
            "DIRECTION": direction  # Store direction with default "Long"
        }
        
        # Handle stop loss validation and conversion
        stop_loss = row.get("stop_loss")
        if stop_loss is not None:
            try:
                stop_loss_float = float(stop_loss)
                # Convert percentage (0-100) to decimal (0-1)
                stop_loss_decimal = stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
                if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
                    log(f"Warning: Stop loss for {ticker} ({stop_loss_float}%) is outside valid range (0-100%)", "warning")
                config_entry["STOP_LOSS"] = stop_loss_decimal
                log(f"Stop loss set to {stop_loss_decimal:.4f} ({stop_loss_decimal*100:.2f}%) for {ticker}", "info")
            except ValueError:
                log(f"Error: Invalid stop loss value for {ticker}: {stop_loss}", "error")
                raise ValueError(f"Invalid stop loss value for {ticker}: {stop_loss}")
        else:
            log(f"Warning: No stop loss defined for {ticker}", "warning")
        
        # Add RSI fields only if both exist and have non-None values
        if has_rsi:
            config_entry["RSI_PERIOD"] = int(rsi_period)
            config_entry["RSI_THRESHOLD"] = int(rsi_threshold)  # Changed from float to int
        
        # Add MACD signal period if it's a MACD strategy
        if strategy_type == "MACD":
            # Check both signal_window and signal_window for backward compatibility
            signal = row.get("signal_window") or row.get("signal_window")
            if signal is not None:
                config_entry["SIGNAL_WINDOW"] = int(signal)
            else:
                log(f"Warning: MACD strategy for {ticker} missing signal period/window", "warning")
        
        # Log complete strategy configuration
        strategy_details = [
            f"TICKER: {config_entry['TICKER']}",
            f"Strategy Type: {strategy_type}",
            f"Direction: {direction}",
            f"Timeframe: {timeframe}",
            f"SHORT_WINDOW: {config_entry['SHORT_WINDOW']}",
            f"LONG_WINDOW: {config_entry['LONG_WINDOW']}",
            f"USE_RSI: {config_entry['USE_RSI']}"
        ]
        
        # Only add STOP_LOSS to log if it exists
        if "STOP_LOSS" in config_entry:
            strategy_details.append(f"STOP_LOSS: {config_entry['STOP_LOSS']}")
        
        # Only add RSI details if RSI is enabled
        if has_rsi:
            strategy_details.extend([
                f"RSI_PERIOD: {config_entry['RSI_PERIOD']}",
                f"RSI_THRESHOLD: {config_entry['RSI_THRESHOLD']}"
            ])
        
        strategy_details.extend([
            f"USE_HOURLY: {config_entry['USE_HOURLY']}",
            f"USE_SMA: {config_entry['USE_SMA']}",
            f"BASE_DIR: {config_entry['BASE_DIR']}",
            f"REFRESH: {config_entry['REFRESH']}"
        ])
        
        if "SIGNAL_WINDOW" in config_entry:
            strategy_details.append(f"SIGNAL_WINDOW: {config_entry['SIGNAL_WINDOW']}")
        
        log(f"Strategy Configuration:\n" + "\n".join(strategy_details), "info")
        portfolio.append(config_entry)
    
    log(f"Successfully loaded {len(portfolio)} strategy configurations", "info")
    return portfolio

def load_portfolio(file_path: str, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Load portfolio configuration from either JSON or CSV file.

    Args:
        file_path (str): Path to the portfolio file
        log (Callable[[str, str], None]): Logging function for status updates
        config (Dict): Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file is empty, malformed, or has an unsupported extension
    """
    path = Path(file_path)
    if not path.exists():
        log(f"Portfolio file not found: {path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {path}")

    extension = path.suffix.lower()
    if extension == '.json':
        return load_portfolio_from_json(path, log, config)
    elif extension == '.csv':
        return load_portfolio_from_csv(path, log, config)
    else:
        error_msg = f"Unsupported file type: {extension}. Must be .json or .csv"
        log(error_msg, "error")
        raise ValueError(error_msg)
