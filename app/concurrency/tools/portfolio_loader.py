"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from JSON files. It handles parsing of required and optional strategy parameters with
appropriate type conversion.
"""

from pathlib import Path
from typing import List, Callable, Dict
import polars as pl
from app.concurrency.tools.types import StrategyConfig

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
        
        config_entry: StrategyConfig = {
            "TICKER": ticker,
            "SHORT_WINDOW": int(row["short_window"]),
            "LONG_WINDOW": int(row["long_window"]),
            "BASE_DIR": config["BASE_DIR"],
            "REFRESH": config["REFRESH"],
            "STOP_LOSS": float(row.get("stop_loss", 0.0)),
            "USE_RSI": has_rsi,
            "USE_HOURLY": timeframe.lower() == "hourly",
            "USE_SMA": False  # Default to EMA
        }
        
        # Add RSI fields only if both exist and have non-None values
        if has_rsi:
            config_entry["RSI_PERIOD"] = int(rsi_period)
            config_entry["RSI_THRESHOLD"] = float(rsi_threshold)
        
        # Add MACD signal period if it's a MACD strategy
        if strategy_type == "MACD" and "signal_period" in row:
            config_entry["SIGNAL_PERIOD"] = int(row["signal_period"])
        
        # Log complete strategy configuration
        strategy_details = [
            f"TICKER: {config_entry['TICKER']}",
            f"Strategy Type: {strategy_type}",
            f"Timeframe: {timeframe}",
            f"SHORT_WINDOW: {config_entry['SHORT_WINDOW']}",
            f"LONG_WINDOW: {config_entry['LONG_WINDOW']}",
            f"STOP_LOSS: {config_entry['STOP_LOSS']}",
            f"USE_RSI: {config_entry['USE_RSI']}"
        ]
        
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
        
        if "SIGNAL_PERIOD" in config_entry:
            strategy_details.append(f"SIGNAL_PERIOD: {config_entry['SIGNAL_PERIOD']}")
        
        log(f"Strategy Configuration:\n" + "\n".join(strategy_details), "info")
        portfolio.append(config_entry)
    
    log(f"Successfully loaded {len(portfolio)} strategy configurations", "info")
    return portfolio
